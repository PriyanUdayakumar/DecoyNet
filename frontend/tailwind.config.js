/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#07101f',
          900: '#0b1220',
          850: '#0f172a',
          800: '#111c33',
          700: '#1e293b',
        },
        cyber: {
          cyan: '#22d3ee',
          green: '#34d399',
          amber: '#f59e0b',
          orange: '#fb923c',
          red: '#f87171',
          purple: '#c084fc',
        },
      },
      boxShadow: {
        glow: '0 0 32px rgba(34, 211, 238, 0.16)',
      },
    },
  },
  plugins: [],
};
