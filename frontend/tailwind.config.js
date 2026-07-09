/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f5f7fa',
          100: '#e4e8f0',
          200: '#c8d1e1',
          300: '#9db0cc',
          400: '#6c88b3',
          500: '#4a6794',
          600: '#384f76',
          700: '#2e3f60',
          800: '#27344f',
          900: '#212a3e',
        }
      }
    },
  },
  plugins: [],
}
