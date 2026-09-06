import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet } from 'react-native';
import { useDriverStore } from '../store/driverStore';

/**
 * There is no login or routes-listing API in the backend yet (confirmed:
 * no /auth endpoint, no /routes endpoint in api-gateway). MQTT itself
 * needs no credentials either (EMQX_ALLOW_ANONYMOUS=true for this MVP).
 *
 * So for now, the driver just types in which bus and route they're on.
 * These two values map directly to the GPSPing proto's bus_id/route_id
 * fields and become part of every MQTT topic (gps/<bus_id>/ping).
 *
 * Swap this for a real picker (or add auth) once Member 2/6 exposes a
 * routes/vehicles endpoint — the rest of the app doesn't need to change,
 * since it only depends on driverStore.busId/routeId being set.
 */
export default function SetupScreen({ navigation }: any) {
  const [busIdInput, setBusIdInput] = useState('');
  const [routeIdInput, setRouteIdInput] = useState('');
  const setSession = useDriverStore(s => s.setSession);

  const canContinue = busIdInput.trim().length > 0 && routeIdInput.trim().length > 0;

  const handleContinue = () => {
    setSession(busIdInput.trim(), routeIdInput.trim());
    navigation.replace('Tracking');
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>GatiSync Driver</Text>
      <Text style={styles.subtitle}>
        Enter your bus and route to start sharing live location.
      </Text>

      <TextInput
        style={styles.input}
        placeholder="Bus ID (e.g. BUS-402)"
        value={busIdInput}
        onChangeText={setBusIdInput}
        autoCapitalize="characters"
      />
      <TextInput
        style={styles.input}
        placeholder="Route ID (e.g. R-7)"
        value={routeIdInput}
        onChangeText={setRouteIdInput}
        autoCapitalize="characters"
      />

      <Button title="Continue" onPress={handleContinue} disabled={!canContinue} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 24 },
  title: { fontSize: 24, fontWeight: '700', marginBottom: 8, textAlign: 'center' },
  subtitle: { fontSize: 14, color: '#666', marginBottom: 32, textAlign: 'center' },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
});
