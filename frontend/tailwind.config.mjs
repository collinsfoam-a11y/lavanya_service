/**
 * Tailwind config — Lavanya Service Console.
 *
 * Base theme comes from frappe-ui's official preset (the same one Helpdesk,
 * CRM, Insights and Gameplan use): it restores Tailwind's default screens +
 * utilities (so `md:` and color utilities actually emit), and adds
 * @tailwindcss/forms, typography, the frappe-ui design tokens (full gray
 * palette, semantic colors) and the lucide icon plugin.
 *
 * The Lavanya brand tokens are now driven by CSS custom properties so the
 * runtime theme engine (`utils/theme-engine.js`) can switch themes without a
 * page rebuild. Default values match the Lavanya Light theme.
 */
import frappeUIPreset from 'frappe-ui/tailwind'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default {
  presets: [frappeUIPreset],
  content: [
    path.join(__dirname, 'index.html'),
    path.join(__dirname, 'src/**/*.{vue,js,ts,jsx,tsx}'),
    path.join(__dirname, 'node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}'),
  ],
  theme: {
    extend: {
      colors: {
        background: 'var(--lav-background)',
        'on-background': 'var(--lav-text-primary)',
        surface: 'var(--lav-surface)',
        'surface-bright': 'var(--lav-surface)',
        'surface-dim': 'var(--lav-surface-container-low)',
        'surface-variant': 'var(--lav-surface-elevated)',
        'surface-container-lowest': 'var(--lav-surface)',
        'surface-container-low': 'var(--lav-surface-container-low)',
        'surface-container': 'var(--lav-surface-elevated)',
        'surface-container-high': 'var(--lav-surface-container-high)',
        'surface-container-highest': 'var(--lav-surface-container-highest)',
        'on-surface': 'var(--lav-text-primary)',
        'on-surface-variant': 'var(--lav-text-secondary)',
        'outline-variant': 'var(--lav-border)',
        primary: 'var(--lav-primary)',
        'primary-container': 'var(--lav-primary-container)',
        'on-primary': 'var(--lav-on-primary)',
        'on-primary-container': 'var(--lav-on-primary-container)',
        secondary: 'var(--lav-secondary)',
        'secondary-container': 'var(--lav-secondary-container)',
        'on-secondary': 'var(--lav-on-secondary)',
        tertiary: 'var(--lav-tertiary)',
        'tertiary-container': 'var(--lav-tertiary-container)',
        'on-tertiary': 'var(--lav-on-tertiary)',
        error: 'var(--lav-danger)',
        'error-container': 'var(--lav-danger-container)',
        'on-error': 'var(--lav-on-danger)',
        success: 'var(--lav-success)',
        warning: 'var(--lav-warning)',
        info: 'var(--lav-info)',
      },
      fontFamily: {
        display: ['Inter', 'sans-serif'],
        'headline-lg': ['Inter', 'sans-serif'],
        'headline-md': ['Inter', 'sans-serif'],
        'body-lg': ['Inter', 'sans-serif'],
        'body-md': ['Inter', 'sans-serif'],
        'label-md': ['Inter', 'sans-serif'],
      },
      fontSize: {
        display: ['36px', { lineHeight: '44px', letterSpacing: '-0.02em', fontWeight: '700' }],
        'headline-lg': ['28px', { lineHeight: '36px', letterSpacing: '-0.01em', fontWeight: '600' }],
        'headline-md': ['20px', { lineHeight: '28px', fontWeight: '600' }],
        'body-lg': ['16px', { lineHeight: '24px', fontWeight: '400' }],
        'body-md': ['14px', { lineHeight: '20px', fontWeight: '400' }],
        'label-md': ['12px', { lineHeight: '16px', fontWeight: '600' }],
      },
      spacing: {
        unit: '8px',
        gutter: 'var(--lav-gutter)',
        'container-padding': 'var(--lav-container-padding)',
        'sidebar-width': '260px',
        'max-content-width': '1440px',
      },
      borderRadius: {
        lg: '0.5rem',
        xl: '0.75rem',
      },
    },
  },
  plugins: [],
}
