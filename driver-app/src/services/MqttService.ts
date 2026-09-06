import MQTT, { IMqttClient } from 'sp-react-native-mqtt';
import { MQTT_BROKER_HOST, MQTT_BROKER_PORT } from '../utils/constants';

/**
 * Wraps sp-react-native-mqtt, a native TCP MQTT client.
 *
 * WHY NOT a pure-JS mqtt.js client? The 'mqtt' npm package speaks MQTT
 * over WebSockets by default in browser-like environments, but our
 * docker-compose only exposes EMQX's raw TCP port (1883), not a
 * websocket listener (8083/8084). React Native doesn't have raw TCP
 * sockets in JS without a native module, so we use a library that
 * wraps the native Paho MQTT client on Android/iOS instead.
 *
 * EMQX_ALLOW_ANONYMOUS=true in the docker-compose for this MVP, so no
 * username/password is required to connect or publish. Do not ship
 * this to production without adding per-device credentials.
 */

let client: IMqttClient | null = null;
let isConnecting = false;

/**
 * Plain-JS base64 encoder — no dependency on Node's Buffer, which
 * doesn't exist in React Native without an extra polyfill package.
 * Standard base64 alphabet, works on any Uint8Array.
 */
const BASE64_CHARS =
  'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

function uint8ArrayToBase64(bytes: Uint8Array): string {
  let result = '';
  let i = 0;
  for (; i + 2 < bytes.length; i += 3) {
    const chunk = (bytes[i] << 16) | (bytes[i + 1] << 8) | bytes[i + 2];
    result += BASE64_CHARS[(chunk >> 18) & 63];
    result += BASE64_CHARS[(chunk >> 12) & 63];
    result += BASE64_CHARS[(chunk >> 6) & 63];
    result += BASE64_CHARS[chunk & 63];
  }
  const remaining = bytes.length - i;
  if (remaining === 1) {
    const chunk = bytes[i] << 16;
    result += BASE64_CHARS[(chunk >> 18) & 63];
    result += BASE64_CHARS[(chunk >> 12) & 63];
    result += '==';
  } else if (remaining === 2) {
    const chunk = (bytes[i] << 16) | (bytes[i + 1] << 8);
    result += BASE64_CHARS[(chunk >> 18) & 63];
    result += BASE64_CHARS[(chunk >> 12) & 63];
    result += BASE64_CHARS[(chunk >> 6) & 63];
    result += '=';
  }
  return result;
}

export type MqttConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

type StatusListener = (status: MqttConnectionStatus, error?: string) => void;
let statusListener: StatusListener | null = null;

export function onMqttStatusChange(listener: StatusListener): void {
  statusListener = listener;
}

function emitStatus(status: MqttConnectionStatus, error?: string) {
  statusListener?.(status, error);
}

export async function connectMqtt(): Promise<void> {
  if (client || isConnecting) {
    return;
  }
  isConnecting = true;
  emitStatus('connecting');

  try {
    client = await MQTT.createClient({
      uri: `tcp://${MQTT_BROKER_HOST}:${MQTT_BROKER_PORT}`,
      clientId: `gatisync-driver-${Math.random().toString(16).slice(2)}`,
      clean: true,
      auth: false, // EMQX_ALLOW_ANONYMOUS=true — see note above
    });

    client.on('closed', () => emitStatus('disconnected'));
    client.on('error', (err: unknown) => {
      emitStatus('error', String(err));
    });
    client.on('connect', () => emitStatus('connected'));

    client.connect();
  } catch (err) {
    emitStatus('error', String(err));
    client = null;
  } finally {
    isConnecting = false;
  }
}

export function disconnectMqtt(): void {
  client?.disconnect();
  client = null;
  emitStatus('disconnected');
}

/**
 * Publishes a pre-encoded Protobuf payload to gps/<busId>/ping at QoS 1,
 * matching exactly what the Go worker subscribes to
 * (MQTT_TOPIC=gps/+/ping in infra/docker-compose.yml).
 *
 * QoS 1 = "at least once" delivery — matches the backend's expectation
 * per the research doc (99% packet delivery over patchy networks) and
 * is what the worker's client.Subscribe(..., 1, ...) call uses.
 */
export function publishGPSPing(busId: string, payload: Uint8Array): void {
  if (!client) {
    console.warn('publishGPSPing: MQTT client not connected, dropping ping');
    return;
  }
  const topic = `gps/${busId}/ping`;

  // VERIFY BEFORE TRUSTING: the RN bridge doesn't reliably pass raw byte
  // arrays as JS strings. This base64-encodes the Protobuf bytes, which
  // is the common workaround for this library — but whether the native
  // side decodes it back to raw bytes before publishing (vs. publishing
  // the base64 text itself) varies by library version.
  //
  // TEST THIS FIRST: run the local docker-compose worker, publish one
  // ping, and check the worker log. If you see "discarded malformed
  // protobuf", the worker received base64 TEXT instead of decoded bytes
  // — in that case, check this library's README for its actual binary
  // payload API, or switch to a library that accepts a Buffer directly.
  client.publish(topic, uint8ArrayToBase64(payload), 1, false);
}
