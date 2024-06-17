/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'bold': ['Ubuntu-Bold', 'sans-serif'],
        'medium': ['Ubuntu-Medium', 'sans-serif'],
        'regular': ['Ubuntu-Regular', 'sans-serif'],
        'light': ['Ubuntu-Light', 'sans-serif'],
        'bolditalic': ['Ubuntu-BoldItalic', 'sans-serif'],
        'mediumitalic': ['Ubuntu-MediumItalic', 'sans-serif'],
        'italic': ['Ubuntu-Italic', 'sans-serif'],
        'lightitalic': ['Ubuntu-LightItalic', 'sans-serif'],
      },
      colors: {
        'window-black': '#191919',
        'esmerald-light': '#E6EFEF',
        'esmerald': '#002921',
        'esmerald-dark': '#001713',
        'green-light' : '#809490',
        'lemon': '#F0FF3D',
        'pink': '#C55FFF',
        'brown': '#623721',
        'black': '#121212'
      }
    },
  },
  plugins: [],
}