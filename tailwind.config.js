/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"DM Sans"', 'sans-serif'],
        body: ['"DM Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        navy: {
          950: '#060D18',
          900: '#0D1B2E',
          800: '#112238',
          700: '#163048',
          600: '#1E4068',
          500: '#2756A0',
        },
        brand: {
          DEFAULT: '#1A6FE8',
          dark: '#1558C0',
          light: '#4D92F5',
          50: '#EBF3FE',
          100: '#C4DCFC',
        },
        emerald: {
          900: '#052E16',
          800: '#14532D',
          700: '#166534',
          600: '#16A34A',
          500: '#22C55E',
          100: '#DCFCE7',
          50: '#F0FDF4',
        },
        rose: {
          900: '#4C0519',
          700: '#BE123C',
          500: '#F43F5E',
          100: '#FFE4E6',
          50: '#FFF1F2',
        },
        amber: {
          900: '#451A03',
          700: '#B45309',
          500: '#F59E0B',
          100: '#FEF3C7',
          50: '#FFFBEB',
        },
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.10)',
        sidebar: '2px 0 12px rgba(0,0,0,0.25)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.35s ease-out',
        'spin-slow': 'spin 2s linear infinite',
      },
      keyframes: {
        fadeIn: { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp: { from: { opacity: 0, transform: 'translateY(12px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
      },
    },
  },
  plugins: [],
}
