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
        brand: {
          dark: '#0a0a0f',
          card: '#12121a',
          cardHover: '#181824',
          accent: '#8b5cf6',
          accentHover: '#7c3aed',
          cyan: '#06b6d4',
          gold: '#eab308'
        }
      }
    },
  },
  plugins: [],
}
