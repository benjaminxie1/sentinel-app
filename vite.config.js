import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  
  // Tauri integration
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    watch: {
      ignored: ['**/src-tauri/**']
    }
  },
  
  // Build configuration
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: resolve(__dirname, 'index.html')
    }
  },
  
  // Environment variables for Tauri
  envPrefix: ['VITE_', 'TAURI_'],
  
  // CSS processing
  css: {
    postcss: './postcss.config.js'
  }
});