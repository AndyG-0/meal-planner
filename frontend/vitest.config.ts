import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.js',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json-summary', 'lcov'],
      all: true,
      include: ['src/**/*'],
      exclude: ['src/main.jsx', 'src/setupTests.js', '**/*.test.js', '**/*.test.jsx'],
      reportsDirectory: 'coverage',
    },
  },
})