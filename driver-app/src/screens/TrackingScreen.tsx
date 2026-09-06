import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, Button, StyleSheet, Alert } from 'react-native';
import { useDriverStore } from '../store/driverStore';
import { requestLocationPermissions } from '../services/LocationService';
import {
  startBackgroundTracking,
  stopBackgroundTracking,
} from '../services/BackgroundTask';
import {
  connectMqtt,
  disconnectMqtt,
  onMqttStatusChange,
  MqttConnectionStatus,
} from '../services/MqttService';
import { isMockLocationSuspected } from '../utils/mockLocationCheck';
import { requestIgnoreBatteryOptimizations } from '../utils/batteryOptimization';

export default function TrackingScreen() {
  const {
    busId,
    routeId,
    tripStatus,
    lastFix,
    pingsSentCount,
    pingsFailedCount,
    setTripStatus,
    recordFix,
    recordPublishFailure,
    setError,
  } = useDriverStore();

  const [mqttStatus, setMqttStatus] = useState<MqttConnectionStatus>('disconnected');

  useEffect(() => {
    requestIgnoreBatteryOptimizations();
    onMqttStatusChange((status, err) => {
      setMqttStatus(status);
      if (err) {
        console.warn('MQTT status error:', err);
      }
    });
  }, []);

  const handleStart = useCallback(async () => {
    if (!busId || !routeId) {
      Alert.alert('Missing setup', 'Bus ID / Route ID not set.');
      return;
    }

    const mockSuspected = await isMockLocationSuspected();
    if (mockSuspected) {
      Alert.alert(
        'Mock Location Detected',
        'Please disable mock/fake GPS apps before starting a trip.',
      );
      return;
    }

    const granted = await requestLocationPermissions();
    if (!granted) {
      Alert.alert(
        'Permission Required',
        'Location permission is required to track your trip.',
      );
      return;
    }

    try {
      await connectMqtt();
      await startBackgroundTracking(
        busId,
        routeId,
        fix => recordFix(fix),
        message => {
          recordPublishFailure();
          console.warn(message);
        },
      );
      setTripStatus('tracking');
    } catch (err) {
      setError('Failed to start tracking service.');
    }
  }, [busId, routeId, recordFix, recordPublishFailure, setError, setTripStatus]);

  const handleStop = useCallback(async () => {
    await stopBackgroundTracking();
    disconnectMqtt();
    setTripStatus('idle');
  }, [setTripStatus]);

  return (
    <View style={styles.container}>
      <Text style={styles.sessionLine}>
        Bus {busId} · Route {routeId}
      </Text>
      <Text style={styles.status}>Status: {tripStatus}</Text>
      <Text style={styles.mqttStatus}>MQTT: {mqttStatus}</Text>

      {lastFix && (
        <View style={styles.fixBox}>
          <Text>Lat: {lastFix.latitude.toFixed(6)}</Text>
          <Text>Lng: {lastFix.longitude.toFixed(6)}</Text>
          <Text>
            Speed: {lastFix.speed !== null ? `${lastFix.speed.toFixed(1)} m/s` : 'n/a'}
          </Text>
          <Text>Accuracy: {lastFix.accuracy.toFixed(1)} m</Text>
        </View>
      )}

      <Text style={styles.pingCount}>
        Pings sent: {pingsSentCount}  ·  Failed/skipped: {pingsFailedCount}
      </Text>

      <View style={styles.buttonRow}>
        {tripStatus !== 'tracking' ? (
          <Button title="Start Trip" onPress={handleStart} />
        ) : (
          <Button title="Stop Trip" color="#d32f2f" onPress={handleStop} />
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, justifyContent: 'center' },
  sessionLine: { fontSize: 14, color: '#555', marginBottom: 4, textAlign: 'center' },
  status: { fontSize: 18, fontWeight: '600', marginBottom: 4, textAlign: 'center' },
  mqttStatus: { fontSize: 14, color: '#777', marginBottom: 16, textAlign: 'center' },
  fixBox: {
    backgroundColor: '#f0f0f0',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  pingCount: { marginBottom: 24, color: '#555', textAlign: 'center' },
  buttonRow: { marginTop: 8 },
});
