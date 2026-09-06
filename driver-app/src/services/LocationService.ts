import Geolocation, {
  GeoPosition,
  GeoError,
} from 'react-native-geolocation-service';
import { PermissionsAndroid, Platform } from 'react-native';
import {
  GPS_DESIRED_ACCURACY_METERS,
  GPS_DISTANCE_FILTER_METERS,
} from '../utils/constants';

export type GpsFix = {
  latitude: number;
  longitude: number;
  speed: number | null; // m/s, may be null if device can't determine it
  heading: number | null;
  accuracy: number;
  timestamp: number; // epoch ms
};

export type LocationErrorHandler = (error: GeoError) => void;
export type LocationUpdateHandler = (fix: GpsFix) => void;

let watchId: number | null = null;

/**
 * Requests the Android runtime permissions needed for background location.
 * On Android 10+ (API 29+) background location is a SEPARATE permission
 * from foreground location and must be requested after foreground is granted.
 */
export async function requestLocationPermissions(): Promise<boolean> {
  if (Platform.OS !== 'android') {
    return true;
  }

  const fineLocation = await PermissionsAndroid.request(
    PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
    {
      title: 'Location Permission',
      message:
        'GatiSync needs your location to share live bus position with commuters.',
      buttonPositive: 'Allow',
    },
  );

  if (fineLocation !== PermissionsAndroid.RESULTS.GRANTED) {
    return false;
  }

  // Android 10+ requires a second, separate request for background access
  if (Platform.Version >= 29) {
    const backgroundLocation = await PermissionsAndroid.request(
      PermissionsAndroid.PERMISSIONS.ACCESS_BACKGROUND_LOCATION,
      {
        title: 'Background Location Permission',
        message:
          'GatiSync needs to track location even when the app is in the background, so passengers can see live bus updates.',
        buttonPositive: 'Allow',
      },
    );
    return backgroundLocation === PermissionsAndroid.RESULTS.GRANTED;
  }

  return true;
}

/**
 * Gets a single one-off GPS fix. Useful for testing / initial map centering
 * before continuous tracking starts.
 */
export function getCurrentPosition(
  onSuccess: LocationUpdateHandler,
  onError: LocationErrorHandler,
): void {
  Geolocation.getCurrentPosition(
    (position: GeoPosition) => onSuccess(toGpsFix(position)),
    onError,
    {
      enableHighAccuracy: true,
      timeout: 15000,
      maximumAge: 0,
    },
  );
}

/**
 * Starts continuous GPS tracking. Call this once the driver hits "Start Trip".
 * Returns the watch id so the caller can stop it later if needed directly,
 * but prefer using stopWatchingPosition() for consistency.
 */
export function startWatchingPosition(
  onUpdate: LocationUpdateHandler,
  onError: LocationErrorHandler,
): void {
  if (watchId !== null) {
    // already watching — avoid double subscriptions
    return;
  }

  watchId = Geolocation.watchPosition(
    (position: GeoPosition) => onUpdate(toGpsFix(position)),
    onError,
    {
      enableHighAccuracy: true,
      distanceFilter: GPS_DISTANCE_FILTER_METERS,
      interval: 5000,
      fastestInterval: 2000,
      forceRequestLocation: true,
      showLocationDialog: true,
    },
  );
}

export function stopWatchingPosition(): void {
  if (watchId !== null) {
    Geolocation.clearWatch(watchId);
    watchId = null;
  }
}

/**
 * Normalizes the raw library position object into the shape the rest of
 * our app (and eventually the Protobuf encoder) will consume.
 */
function toGpsFix(position: GeoPosition): GpsFix {
  const { latitude, longitude, speed, heading, accuracy } = position.coords;
  return {
    latitude,
    longitude,
    speed,
    heading,
    accuracy: accuracy ?? GPS_DESIRED_ACCURACY_METERS,
    timestamp: position.timestamp,
  };
}
