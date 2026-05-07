/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Outfit', 'system-ui', 'sans-serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        brand: {
          50: '#f0f4ff',
          100: '#dbe4ff',
          200: '#bac8ff',
          300: '#91a7ff',
          400: '#748ffc',
          500: '#5c7cfa',
          600: '#4c6ef5',
          700: '#4263eb',
          800: '#3b5bdb',
          900: '#364fc7',
          950: '#1c3d8f',
        },
        surface: {
          0: '#0a0e1a',
          1: '#0f1424',
          2: '#151b30',
          3: '#1a213d',
          4: '#1f2849',
          5: '#252f55',
        },
        neon: {
          blue: '#5c7cfa',
          cyan: '#22b8cf',
          green: '#51cf66',
          orange: '#ff922b',
          pink: '#f06595',
        },
      },
      backgroundImage: {
        'glow-blue': 'radial-gradient(circle at 50% 0%, rgba(92,124,250,0.15) 0%, transparent 60%)',
        'glow-cyan': 'radial-gradient(circle at 50% 0%, rgba(34,184,207,0.12) 0%, transparent 60%)',
      },
    },
  },
  plugins: [],
}
