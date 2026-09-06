import { Platform, NativeModules } from 'react-native';

/**
 * Anti-spoofing check.
 *
 * On Android, GeoPosition objects include an `isFromMockProvider` flag
 * when using react-native-geolocation-service with the right config,
 * but the most reliable cross-device check is via Settings.Secure /
 * Location.isMock at the native layer.
 *
 * For now this wraps react-native-device-info's isMockLocationEnabled,
 * which is enough for MVP. If we need per-fix mock detection later,
 * we can inspect `position.mocked` (Android) on each GPS fix in
 * LocationService and reject/flag pings from mocked providers.
 */

// eslint-disable-next-line @typescript-eslint/no-var-requires
const DeviceInfo = require('react-native-device-info').default;

export async function isMockLocationSuspected(): Promise<boolean> {
  if (Platform.OS !== 'android') {
    // iOS doesn't expose a general "developer mock location" toggle
    // the way Android does; treat as not-suspected for now.
    return false;
  }

  try {
    const isMockEnabled: boolean = await DeviceInfo.isMockLocationEnabled();
    return isMockEnabled;
  } catch (err) {
    // Fail safe: if we can't determine it, don't block the driver,
    // but log for later investigation.
    console.warn('mockLocationCheck: could not determine mock status', err);
    return false;
  }
}

/**
 * Per-fix check — call this on every GPS update once wired into
 * LocationService, to catch mock providers that get toggled on
 * mid-trip rather than only at app start.
 *
 * `mocked` comes from the native position object on Android
 * (position.mocked). Not present on iOS.
 */
export function isFixMocked(rawPosition: any): boolean {
  return Boolean(rawPosition?.mocked);
}
