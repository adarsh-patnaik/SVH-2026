import { create } from 'zustand';
import { GpsFix } from '../services/LocationService';

export type TripStatus = 'idle' | 'tracking' | 'paused' | 'error';

type DriverState = {
  // --- Session: no login API exists yet, so the driver just enters
  // which bus + route they're driving. Revisit if backend adds auth. ---
  busId: string | null;
  routeId: string | null;
  isSessionSet: boolean;

  // --- Live tracking state ---
  tripStatus: TripStatus;
  lastFix: GpsFix | null;
  pingsSentCount: number;
  pingsFailedCount: number; // validation/publish failures — worth showing in UI
  lastError: string | null;

  // --- Actions ---
  setSession: (busId: string, routeId: string) => void;
  clearSession: () => void;
  setTripStatus: (status: TripStatus) => void;
  recordFix: (fix: GpsFix) => void;
  recordPublishFailure: () => void;
  setError: (message: string | null) => void;
  reset: () => void;
};

export const useDriverStore = create<DriverState>(set => ({
  busId: null,
  routeId: null,
  isSessionSet: false,

  tripStatus: 'idle',
  lastFix: null,
  pingsSentCount: 0,
  pingsFailedCount: 0,
  lastError: null,

  setSession: (busId, routeId) =>
    set({ busId, routeId, isSessionSet: true }),

  clearSession: () => set({ busId: null, routeId: null, isSessionSet: false }),

  setTripStatus: status => set({ tripStatus: status }),

  recordFix: fix =>
    set(state => ({
      lastFix: fix,
      pingsSentCount: state.pingsSentCount + 1,
    })),

  recordPublishFailure: () =>
    set(state => ({ pingsFailedCount: state.pingsFailedCount + 1 })),

  setError: message => set({ lastError: message, tripStatus: 'error' }),

  reset: () =>
    set({
      tripStatus: 'idle',
      lastFix: null,
      pingsSentCount: 0,
      pingsFailedCount: 0,
      lastError: null,
    }),
}));
