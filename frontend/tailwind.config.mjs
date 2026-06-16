/**
 * Tailwind config — Lavanya Service Console.
 *
 * Base theme comes from frappe-ui's official preset (the same one Helpdesk,
 * CRM, Insights and Gameplan use): it restores Tailwind's default screens +
 * utilities (so `md:` and color utilities actually emit), and adds
 * @tailwindcss/forms, typography, the frappe-ui design tokens (full gray
 * palette, semantic colors) and the lucide icon plugin.
 *
 * The Stitch "Lavanya Service Console" brand tokens (Material Design 3, blue
 * #004ac6 primary) are layered on top via theme.extend, so the app keeps its
 * Stitch identity while inheriting frappe-ui's solid base.
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
        background: '#f8f9ff',
        'on-background': '#121c28',
        surface: '#f8f9ff',
        'surface-bright': '#f8f9ff',
        'surface-dim': '#d1dbec',
        'surface-variant': '#d9e3f4',
        'surface-container-lowest': '#ffffff',
        'surface-container-low': '#eef4ff',
        'surface-container': '#e5eeff',
        'surface-container-high': '#dfe9fa',
        'surface-container-highest': '#d9e3f4',
        'on-surface': '#121c28',
        'on-surface-variant': '#434655',
        'outline-variant': '#c3c6d7',
        primary: '#004ac6',
        'primary-container': '#2563eb',
        'on-primary': '#ffffff',
        'on-primary-container': '#eeefff',
        'surface-tint': '#0053db',
        'inverse-primary': '#b4c5ff',
        secondary: '#712ae2',
        'secondary-container': '#8a4cfc',
        'on-secondary': '#ffffff',
        tertiary: '#943700',
        'tertiary-container': '#bc4800',
        'on-tertiary': '#ffffff',
        error: '#ba1a1a',
        'error-container': '#ffdad6',
        'on-error': '#ffffff',
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
        gutter: '16px',
        'container-padding': '24px',
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
