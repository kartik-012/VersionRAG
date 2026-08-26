/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#090a0f',
        surface: {
          DEFAULT: '#12151e',
          subtle: '#181c28',
          card: '#151824',
          border: '#23283a',
          hover: '#1e2333'
        },
        primary: {
          DEFAULT: '#3b82f6',
          hover: '#2563eb',
          light: '#60a5fa',
          glow: 'rgba(59, 130, 246, 0.15)'
        },
        change: {
          added: '#10b981',
          removed: '#f43f5e',
          modified: '#0ea5e9',
          deprecated: '#f59e0b',
          breaking: '#d946ef',
          silent: '#a855f7'
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'SF Mono', 'Menlo', 'monospace'],
      }
    },
  },
  plugins: [],
}
