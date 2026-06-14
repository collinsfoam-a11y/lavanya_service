import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import { fileURLToPath } from 'url'
import { createRequire } from 'module'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(import.meta.url)
const { webserver_port } = require('../../../sites/common_site_config.json')

// https://vitejs.dev/config/
export default defineConfig({
  base: '/assets/lavanya_service/frontend/',
  plugins: [vue()],
  server: {
    port: 8080,
    proxy: {
      '^/(app|api|assets|files|private)': {
        target: `http://127.0.0.1:${webserver_port}`,
        ws: true,
        router: function (req) {
          const site_name = req.headers.host.split(':')[0]
          return `http://${site_name}:${webserver_port}`
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  build: {
    outDir: `../${path.basename(path.resolve('..'))}/public/frontend`,
    emptyOutDir: true,
    target: 'es2015',
  },
})
