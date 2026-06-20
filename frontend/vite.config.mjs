import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import fs from 'fs'
import { fileURLToPath } from 'url'
import { createRequire } from 'module'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(import.meta.url)
const { webserver_port } = require('../../../sites/common_site_config.json')

// The Frappe module dir (apps/lavanya_service/lavanya_service) — same basis as
// build.outDir below. Build output and www both live under it.
const moduleDir = path.resolve('..', path.basename(path.resolve('..')))
const builtIndex = path.join(moduleDir, 'public', 'frontend', 'index.html')
const servePage = path.join(moduleDir, 'www', 'frontend.html')

// Keep the Frappe serve page (www/frontend.html) in sync with the hashed build
// output on every build, so /frontend never references stale asset hashes.
// Pair with www/frontend.py (no_cache) so Frappe re-reads it without clear-cache.
// Uses readFileSync + writeFileSync to avoid EPERM on Docker overlay/copyFileSync.
function syncServePage() {
  return {
    name: 'lavanya-sync-serve-page',
    closeBundle() {
      if (fs.existsSync(builtIndex)) {
        fs.writeFileSync(servePage, fs.readFileSync(builtIndex))
        // eslint-disable-next-line no-console
        console.log('[lavanya] synced www/frontend.html ->', path.basename(builtIndex))
      }
    },
  }
}

// https://vitejs.dev/config/
export default defineConfig({
  base: '/assets/lavanya_service/frontend/',
  plugins: [vue(), syncServePage()],
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
