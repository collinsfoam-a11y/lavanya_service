/**
 * Tailwind config — Lavanya Service Console.
 * Design tokens ported verbatim from the Stitch "Lavanya Service Console"
 * project (Material Design 3, blue #004ac6 primary). Keep in sync with the
 * Stitch design system; do not hand-edit token values.
 */
const path = require("path")

module.exports = {
  presets: [],
  content: [
    path.join(__dirname, "index.html"),
    path.join(__dirname, "src/**/*.{vue,js,ts,jsx,tsx}"),
    path.join(__dirname, "node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}"),
  ],
  // Stitch color tokens are applied via extend.colors; force the bg/text/border
  // utilities to emit regardless of content-scan color detection.
  safelist: [
    {
      pattern:
        /^(bg|text|border)-(background|on-background|surface|surface-bright|surface-dim|surface-variant|surface-container|surface-container-lowest|surface-container-low|surface-container-high|surface-container-highest|on-surface|on-surface-variant|outline|outline-variant|primary|primary-container|on-primary|on-primary-container|surface-tint|inverse-primary|inverse-surface|inverse-on-surface|secondary|secondary-container|on-secondary|on-secondary-container|tertiary|tertiary-container|on-tertiary|on-tertiary-container|error|error-container|on-error|on-error-container)$/,
    },
  ],
  theme: {
    extend: {
      colors: {
        "background": "#f8f9ff",
        "on-background": "#121c28",
        "surface": "#f8f9ff",
        "surface-bright": "#f8f9ff",
        "surface-dim": "#d1dbec",
        "surface-variant": "#d9e3f4",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#eef4ff",
        "surface-container": "#e5eeff",
        "surface-container-high": "#dfe9fa",
        "surface-container-highest": "#d9e3f4",
        "on-surface": "#121c28",
        "on-surface-variant": "#434655",
        "outline": "#737686",
        "outline-variant": "#c3c6d7",
        "primary": "#004ac6",
        "primary-container": "#2563eb",
        "on-primary": "#ffffff",
        "on-primary-container": "#eeefff",
        "surface-tint": "#0053db",
        "inverse-primary": "#b4c5ff",
        "inverse-surface": "#27313e",
        "inverse-on-surface": "#eaf1ff",
        "secondary": "#712ae2",
        "secondary-container": "#8a4cfc",
        "on-secondary": "#ffffff",
        "on-secondary-container": "#fffbff",
        "tertiary": "#943700",
        "tertiary-container": "#bc4800",
        "on-tertiary": "#ffffff",
        "on-tertiary-container": "#ffede6",
        "error": "#ba1a1a",
        "error-container": "#ffdad6",
        "on-error": "#ffffff",
        "on-error-container": "#93000a",
      },
      fontFamily: {
        "display": ["Inter", "sans-serif"],
        "headline-lg": ["Inter", "sans-serif"],
        "headline-md": ["Inter", "sans-serif"],
        "body-lg": ["Inter", "sans-serif"],
        "body-md": ["Inter", "sans-serif"],
        "label-md": ["Inter", "sans-serif"],
      },
      fontSize: {
        "display": ["36px", { lineHeight: "44px", letterSpacing: "-0.02em", fontWeight: "700" }],
        "headline-lg": ["28px", { lineHeight: "36px", letterSpacing: "-0.01em", fontWeight: "600" }],
        "headline-md": ["20px", { lineHeight: "28px", fontWeight: "600" }],
        "body-lg": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "body-md": ["14px", { lineHeight: "20px", fontWeight: "400" }],
        "label-md": ["12px", { lineHeight: "16px", fontWeight: "600" }],
      },
      spacing: {
        "unit": "8px",
        "gutter": "16px",
        "container-padding": "24px",
        "sidebar-width": "260px",
        "max-content-width": "1440px",
      },
      borderRadius: {
        DEFAULT: "0.25rem",
        lg: "0.5rem",
        xl: "0.75rem",
        full: "9999px",
      },
    },
  },
  plugins: [],
}
