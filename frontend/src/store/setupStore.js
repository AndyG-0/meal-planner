import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useSetupStore = create(
  persist(
    (set) => ({
      setupComplete: false,
      
      markSetupComplete: () =>
        set({ setupComplete: true }),
      
      resetSetup: () =>
        set({ setupComplete: false }),
    }),
    {
      name: 'setup-storage',
    }
  )
)
