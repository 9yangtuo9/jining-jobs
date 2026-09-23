/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#1a365d',
          50: '#eaf0f7',
          100: '#cdddee',
          200: '#9bbcd9',
          300: '#5f8abf',
          400: '#3a6aa0',
          500: '#1a365d',
          600: '#162d4f',
          700: '#102440',
          800: '#0b1a2e',
          900: '#07111f',
        },
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', '"PingFang SC"', '"Microsoft YaHei"', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
