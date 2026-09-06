import { Platform, Linking, NativeModules } from 'react-native';

/**
 * Android aggressively kills background services to save battery
 * (Doze mode, App Standby, and OEM-specific killers on Xiaomi/Oppo/
 * Vivo devices are especially bad). Since our whole app depends on
 * staying alive in the background for the driver's entire shift,
 * we need to:
 *
 * 1. Ask the user to disable battery optimization for this app.
 * 2. Run as a foreground service with a persistent notification
 *    (handled in services/BackgroundTask.ts) so Android is far less
 *    likely to kill us even without step 1.
 */

/**
 * Opens the Android system dialog asking the user to exempt this app
 * from battery optimization ("Doze"). Requires the
 * REQUEST_IGNORE_BATTERY_OPTIMIZATIONS permission in the manifest.
 *
 * This should be called once, ideally right after login / before the
 * driver starts their first trip — not buried in a settings menu they
 * might never visit.
 */
export function requestIgnoreBatteryOptimizations(): void {
  if (Platform.OS !== 'android') {
    return;
  }

  // NativeModules.BatteryOptimizationModule would be a small native
  // module wrapping:
  //   Intent intent = new Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS);
  //   intent.setData(Uri.parse("package:" + getPackageName()));
  //   startActivity(intent);
  //
  // Until that native module is added, fall back to opening the app's
  // battery settings page so the user can manually allow it.
  Linking.openSettings();
}

/**
 * Best-effort check for whether we're already exempted.
 * Returns false (unknown/not-exempt) until the native module above
 * is implemented — treat this as a TODO, not a blocker for building
 * the rest of the app.
 */
export async function isIgnoringBatteryOptimizations(): Promise<boolean> {
  if (Platform.OS !== 'android') {
    return true;
  }
  // TODO: wire up native module (PowerManager.isIgnoringBatteryOptimizations)
  return false;
}

/**
 * Human-readable manufacturer-specific guidance. Xiaomi/Oppo/Vivo/
 * Huawei devices have extra "autostart" or "background app" toggles
 * beyond stock Android's battery optimization setting. We can surface
 * this text in the UI based on DeviceInfo.getBrand().
 */
export const MANUFACTURER_GUIDANCE: Record<string, string> = {
  xiaomi:
    'Go to Settings > Apps > Manage Apps > GatiSync > Autostart, and enable it.',
  oppo: 'Go to Settings > Battery > App Battery Management > GatiSync, and set to "Allow background activity".',
  vivo: 'Go to Settings > Battery > Background Power Consumption Management, and enable GatiSync.',
  huawei:
    'Go to Settings > Apps > GatiSync > Battery > App Launch, and set to "Manage manually" with all toggles on.',
};
