/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,js}"],
  theme: {
    extend: {
      colors: {
        // Fire Safety Color Palette
        'fire': {
          50: '#FFF4ED',
          100: '#FFE6D5',
          200: '#FFCDAA',
          300: '#FFAA74',
          400: '#FF7A3C',
          500: '#FF6B35', // Primary fire orange
          600: '#E8441A',
          700: '#C4320F',
          800: '#A02212',
          900: '#821B12',
        },
        'safety': {
          50: '#F0F9FF',
          100: '#E0F2FE',
          200: '#BAE6FD',
          300: '#7DD3FC',
          400: '#38BDF8',
          500: '#0EA5E9',
          600: '#0284C7',
          700: '#0369A1',
          800: '#075985',
          900: '#1A365D', // Deep safety blue
        },
        'emergency': {
          50: '#FEF2F2',
          100: '#FEE2E2',
          200: '#FECACA',
          300: '#FCA5A5',
          400: '#F87171',
          500: '#EF4444',
          600: '#DC2626',
          700: '#B91C1C',
          800: '#991B1B',
          900: '#7F1D1D',
        },
        'warning': {
          50: '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          300: '#FCD34D',
          400: '#FBBF24',
          500: '#F59E0B',
          600: '#D97706',
          700: '#B45309',
          800: '#92400E',
          900: '#78350F',
        },
        'command': {
          900: '#0C0E19', // Deep command center
          800: '#1A1F2E',
          700: '#242A3A',
          600: '#2E3548',
          500: '#384056',
          400: '#4A5568',
        }
      },
      animation: {
        'pulse-fire': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'alert-flash': 'alert-flash 1s ease-in-out infinite',
        'status-ping': 'ping 1s cubic-bezier(0, 0, 0.2, 1) infinite',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px #FF6B35, 0 0 10px #FF6B35, 0 0 15px #FF6B35' },
          '100%': { boxShadow: '0 0 10px #FF6B35, 0 0 20px #FF6B35, 0 0 30px #FF6B35' }
        },
        'alert-flash': {
          '0%, 100%': { backgroundColor: '#EF4444', opacity: 1 },
          '50%': { backgroundColor: '#DC2626', opacity: 0.8 }
        }
      },
      fontFamily: {
        'command': ['JetBrains Mono', 'SF Mono', 'Monaco', 'Consolas', 'monospace'],
        'display': ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}