import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],

  define: {
    'process.env.NODE_ENV': JSON.stringify('production'),
  },

  build: {
    outDir:    resolve(__dirname, '.'),
    emptyOutDir: false,
    lib: {
      entry:   resolve(__dirname, 'main.js'),
      name:    'LavanyaService',
      formats: ['iife'],
      fileName: () => 'lavanya_bundle.js',
    },
    rollupOptions: {
      output: {
        assetFileNames: (info) =>
          info.name?.endsWith('.css') ? 'lavanya.css' : info.name,
      },
    },
    cssCodeSplit: false,
    sourcemap:    false,
    minify:       'esbuild',
  },

  resolve: {
    alias: { '@': resolve(__dirname, '.') },
  },
})
