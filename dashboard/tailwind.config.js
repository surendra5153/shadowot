/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0e1416',
        surface: '#0e1416',
        'surface-bright': '#343a3c',
        'on-surface': '#dee3e6',
        'on-surface-variant': '#bcc9cd',
        primary: '#4cd7f6',
        'on-primary': '#003640',
        error: '#ffb4ab',
        'on-error': '#690005',
        outline: '#869397',
        'outline-variant': '#3d494c',
        'card': '#1A1E2E',
        'card-border': '#334155'
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      fontSize: {
        'label-caps': ['11px', { lineHeight: '16px', letterSpacing: '0.05em', fontWeight: '500' }],
      }
    },
  },
  plugins: [],
}
