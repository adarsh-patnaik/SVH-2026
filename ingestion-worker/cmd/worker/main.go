package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"math"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/eclipse/paho.mqtt.golang"
	"github.com/redis/go-redis/v9"
	"github.com/golang/protobuf/proto"

	"gatisync/ingestion-worker/internal/telemetry"
)

const stateTTL = 90 * time.Second

type liveBus struct {
	BusID          string  `json:"bus_id"`
	RouteID        string  `json:"route_id"`
	Latitude       float64 `json:"latitude"`
	Longitude      float64 `json:"longitude"`
	SpeedMPS       float32 `json:"speed_mps"`
	HeadingDegrees float32 `json:"heading_degrees"`
	CapturedAtMS   int64   `json:"captured_at_unix_ms"`
	ReceivedAtMS   int64   `json:"received_at_unix_ms"`
}

func env(key, fallback string) string { if value := os.Getenv(key); value != "" { return value }; return fallback }

func valid(p *telemetry.GPSPing) error {
	if len(p.BusID) == 0 || len(p.BusID) > 64 || strings.ContainsAny(p.BusID, "{}\n\r") { return fmt.Errorf("invalid bus_id") }
	if len(p.RouteID) == 0 || len(p.RouteID) > 64 { return fmt.Errorf("invalid route_id") }
	if math.IsNaN(p.Latitude) || math.IsNaN(p.Longitude) || p.Latitude < -90 || p.Latitude > 90 || p.Longitude < -180 || p.Longitude > 180 { return fmt.Errorf("invalid coordinates") }
	if p.SpeedMPS < 0 || p.SpeedMPS > 70 || p.HeadingDegrees < 0 || p.HeadingDegrees >= 360 { return fmt.Errorf("invalid motion") }
	return nil
}

func persist(ctx context.Context, rdb *redis.Client, ping *telemetry.GPSPing) error {
	now := time.Now().UnixMilli()
	item := liveBus{ping.BusID, ping.RouteID, ping.Latitude, ping.Longitude, ping.SpeedMPS, ping.HeadingDegrees, ping.CapturedAtUnixMS, now}
	payload, err := json.Marshal(item)
	if err != nil { return err }
	key := "bus:" + ping.BusID + ":live"
	pipe := rdb.TxPipeline()
	pipe.Set(ctx, key, payload, stateTTL)
	pipe.SAdd(ctx, "route:"+ping.RouteID+":buses", ping.BusID)
	pipe.Expire(ctx, "route:"+ping.RouteID+":buses", stateTTL*2)
	pipe.Publish(ctx, "bus-updates", payload)
	_, err = pipe.Exec(ctx)
	return err
}

func main() {
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()
	rdb := redis.NewClient(&redis.Options{Addr: env("REDIS_ADDR", "redis:6379"), Password: os.Getenv("REDIS_PASSWORD")})
	if err := rdb.Ping(ctx).Err(); err != nil { log.Fatalf("redis unavailable: %v", err) }
	defer rdb.Close()

	opts := mqtt.NewClientOptions().AddBroker(env("MQTT_BROKER", "tcp://emqx:1883")).SetClientID(env("MQTT_CLIENT_ID", "gatisync-ingestion-worker")).SetCleanSession(false)
	opts.SetConnectionLostHandler(func(_ mqtt.Client, err error) { log.Printf("mqtt connection lost: %v", err) })
	client := mqtt.NewClient(opts)
	if token := client.Connect(); token.Wait() && token.Error() != nil { log.Fatalf("mqtt unavailable: %v", token.Error()) }
	defer client.Disconnect(250)

	if token := client.Subscribe(env("MQTT_TOPIC", "gps/+/ping"), 1, func(_ mqtt.Client, msg mqtt.Message) {
		var ping telemetry.GPSPing
		if err := proto.Unmarshal(msg.Payload(), &ping); err != nil { log.Printf("discarded malformed protobuf on %s: %v", msg.Topic(), err); return }
		if err := valid(&ping); err != nil { log.Printf("discarded invalid ping for %q: %v", ping.BusID, err); return }
		if err := persist(ctx, rdb, &ping); err != nil { log.Printf("failed to persist ping for %s: %v", ping.BusID, err); return }
		log.Printf("stored bus=%s route=%s", ping.BusID, ping.RouteID)
	}); token.Wait() && token.Error() != nil { log.Fatalf("mqtt subscription failed: %v", token.Error()) }
	log.Printf("ingestion worker ready; topic=%s", env("MQTT_TOPIC", "gps/+/ping"))
	<-ctx.Done()
}
