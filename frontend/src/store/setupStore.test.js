import { describe, it, expect, beforeEach } from 'vitest';
import { useSetupStore } from './setupStore';

describe('setupStore', () => {
  beforeEach(() => {
    const store = useSetupStore.getState();
    store.resetSetup();
  });

  it('should initialize with default state', () => {
    const state = useSetupStore.getState();
    expect(state.setupComplete).toBe(false);
  });

  it('should mark setup as complete', () => {
    useSetupStore.getState().markSetupComplete();

    const state = useSetupStore.getState();
    expect(state.setupComplete).toBe(true);
  });

  it('should reset setup', () => {
    useSetupStore.getState().markSetupComplete();
    expect(useSetupStore.getState().setupComplete).toBe(true);

    useSetupStore.getState().resetSetup();

    const state = useSetupStore.getState();
    expect(state.setupComplete).toBe(false);
  });
});
