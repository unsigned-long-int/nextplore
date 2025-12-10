import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths';

export default defineConfig({
      plugins: [react(), tsconfigPaths()],
      server: {
          host: '0.0.0.0',
          port: 5173,
          watch: {
              usePolling: true,
          },
          proxy: {
                '/api': {
                    target: 'http://orchestration_service:8001',
                    changeOrigin: true,
                },
          },
      }
})
