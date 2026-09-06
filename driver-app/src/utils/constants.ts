/**
 * App-wide constants.
 *
 * CONFIRMED against the backend repo (SVH-2026-Backend-Development):
 * infra/docker-compose.yml, ingestion-worker/proto/gps_ping.proto,
 * ingestion-worker/cmd/worker/main.go.
 */

// --- GPS / tracking config ---
export const GPS_PING_INTERVAL_MS = 5000; // send a ping every 5s per spec
export const GPS_DESIRED_ACCURACY_METERS = 15;
export const GPS_DISTANCE_FILTER_METERS = 5; // ignore updates smaller than this

// --- Background service config ---
export const FOREGROUND_NOTIFICATION_CHANNEL_ID = 'gatisync-tracking';
export const FOREGROUND_NOTIFICATION_TITLE = 'GatiSync is tracking your trip';
export const FOREGROUND_NOTIFICATION_TEXT = 'Location sharing is active';

// --- Backend connection (confirmed from infra/docker-compose.yml) ---
//
// IMPORTANT for physical-device testing: "localhost" here means the
// PHONE's localhost, not your laptop's. If you're running docker-compose
// on your laptop and testing on a real Android device (not an emulator),
// replace these with your laptop's LAN IP (e.g. 192.168.1.42) — find it
// with `ipconfig` (Windows) while phone and laptop are on the same Wi-Fi.
// Android emulators specifically can reach the host laptop via 10.0.2.2.
export const MQTT_BROKER_HOST = 'localhost'; // emqx service, port 1883 exposed in docker-compose
export const MQTT_BROKER_PORT = 1883;
export const API_BASE_URL = 'http://localhost:8000'; // api-gateway service, port 8000 exposed

// Topic pattern confirmed from docker-compose: MQTT_TOPIC: gps/+/ping
// Actual publish topic per bus: gps/<bus_id>/ping — built dynamically
// in MqttService.publishGPSPing(), not as a fixed constant.
export const MQTT_TOPIC_WILDCARD = 'gps/+/ping';

// --- Auth ---
// NOTE: no login/auth API exists in the backend yet (no /auth endpoint,
// and EMQX_ALLOW_ANONYMOUS=true means MQTT itself needs no credentials
// for this MVP). The app currently just asks the driver to enter a
// Bus ID + Route ID directly (see screens/SetupScreen.tsx) rather than
// pretending a JWT login flow exists. Revisit this if/when backend adds
// real device auth.
export const DRIVER_SESSION_STORAGE_KEY = '@gatisync/driver_session';
