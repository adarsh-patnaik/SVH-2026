package telemetry

import (
	"testing"

	"github.com/golang/protobuf/proto"
)

func TestGPSPingRoundTrip(t *testing.T) {
	want := &GPSPing{BusID: "BUS-402", RouteID: "R-7", Latitude: 31.634, Longitude: 74.872, SpeedMPS: 8.2, HeadingDegrees: 90, CapturedAtUnixMS: 1_700_000_000_000}
	b, err := proto.Marshal(want)
	if err != nil { t.Fatal(err) }
	var got GPSPing
	if err := proto.Unmarshal(b, &got); err != nil { t.Fatal(err) }
	if got.BusID != want.BusID || got.RouteID != want.RouteID || got.Latitude != want.Latitude || got.CapturedAtUnixMS != want.CapturedAtUnixMS { t.Fatalf("round trip mismatch: %#v", got) }
}
