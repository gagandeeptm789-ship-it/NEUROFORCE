/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        midnight: {
          950: '#060A12',
          900: '#0B1120',
          850: '#0E172B',
          800: '#13203D',
          700: '#1E2F56',
          600: '#2B4277',
        },
        cyber: {
          cyan: '#00E5FF',
          blue: '#0284C7',
          glow: 'rgba(0, 229, 255, 0.15)',
        },
        status: {
          verified: '#10B981',
          tampered: '#EF4444',
          transformed: '#F59E0B',
          unverifiable: '#64748B',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Courier New', 'monospace'],
      },
      boxShadow: {
        'cyber-sm': '0 0 15px -3px rgba(0, 229, 255, 0.12)',
        'cyber-md': '0 0 25px -5px rgba(0, 229, 255, 0.2)',
        'cyber-danger': '0 0 20px -3px rgba(239, 68, 68, 0.25)',
        'cyber-success': '0 0 20px -3px rgba(16, 185, 129, 0.25)',
        'cyber-amber': '0 0 20px -3px rgba(245, 158, 11, 0.25)',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseSlow: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.4' },
        },
        scanBeam: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(210px)' },
        }
      },
      animation: {
        fadeIn: 'fadeIn 0.3s ease-out forwards',
        pulseSlow: 'pulseSlow 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        scanBeam: 'scanBeam 2.2s ease-in-out infinite',
      }
    },
  },
  plugins: [],
}
