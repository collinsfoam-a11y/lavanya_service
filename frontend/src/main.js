import './index.css'

import { createApp } from 'vue'
import router from './router'
import App from './App.vue'

const app = createApp(App)
app.config.errorHandler = (err) => {
  console.error('[Lavanya] Unhandled error:', err)
}
app.use(router).mount('#app')
