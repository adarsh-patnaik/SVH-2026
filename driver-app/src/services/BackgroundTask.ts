import BackgroundService from 'react-native-background-actions';
import {
  startWatchingPosition,
  stopWatchingPosition,
  GpsFix,
} from './LocationService';
import {
  toGPSPingPayload,
  validateGPSPingPayload,
  encodeGPSPing,
} from './ProtobufEncoder';
import { publishGPSPing } from './MqttService';
import {
  FOREGROUND_NOTIFICATION_TITLE,
  FOREGROUND_NOTIFICATION_TEXT,
} from '../utils/constants';


export type FixConsumer = (fix: GpsFix) => void;

/**
 * The options object for react-native-background-actions.
 * This is what puts up the persistent "GatiSync is tracking your trip"
 * notification and keeps the process alive as a foreground service.
 */
function buildTaskOptions() {
  return {
    taskName: 'GatiSyncTracking',
    taskTitle: FOREGROUND_NOTIFICATION_TITLE,
    taskDesc: FOREGROUND_NOTIFICATION_TEXT,
    taskIcon: {
      name: 'ic_launcher',
      type: 'mipmap',
    },
    color: '#1E88E5',
    linkingURI: 'gatisync://tracking',
    parameters: {
      delay: 60000,
    },
  };
}
/**
 * The actual background "task" — an infinite loop that keeps the
 * foreground service alive. The real work happens via the
 * startWatchingPosition callback below, not in this loop; the loop's
 * only job is to keep the service from being torn down.
 */
const backgroundTask = async (taskDataArguments?: { delay?: number }) => {
  const delay = taskDataArguments?.delay ?? 60000;
  // eslint-disable-next-line no-constant-condition
  await new Promise<void>(async resolve => {
    for (;;) {
      if (!BackgroundService.isRunning()) {
        resolve();
        break;
      }
      await sleep(delay);
    }
  });
};

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Starts the foreground service AND GPS watching together, and now
 * publishes every valid fix to the real backend: encodes it as the
 * GPSPing Protobuf message and publishes to gps/<busId>/ping over MQTT.
 *
 * `onFix` still fires for every fix (for UI updates in TrackingScreen),
 * independent of whether the MQTT publish succeeds.
 */
export async function startBackgroundTracking(
  busId: string,
  routeId: string,
  onFix: FixConsumer,
  onPublishError: (message: string) => void,
): Promise<void> {
  await BackgroundService.start(backgroundTask, buildTaskOptions());

  startWatchingPosition(
    fix => {
      onFix(fix);

      const payload = toGPSPingPayload(fix, busId, routeId);
      const validationError = validateGPSPingPayload(payload);
      if (validationError) {
        // Matches the Go worker's own validation — if it fails here,
        // the worker would have silently discarded it anyway.
        onPublishError(`Skipped invalid ping: ${validationError}`);
        return;
      }

      try {
        const encoded = encodeGPSPing(payload);
        publishGPSPing(busId, encoded);
      } catch (err) {
        onPublishError(`Failed to encode/publish ping: ${String(err)}`);
      }
    },
    error => {
      console.warn('BackgroundTask: location error', error);
    },
  );
}

export async function stopBackgroundTracking(): Promise<void> {
  stopWatchingPosition();
  await BackgroundService.stop();
}
