/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./components/**/*.{vue,js,ts,jsx,tsx}",
    "./layouts/**/*.{vue,js,ts,jsx,tsx}",
    "./pages/**/*.{vue,js,ts,jsx,tsx}",
    "./plugins/**/*.{js,ts}",
    "./app.vue",
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
        'caveat-regular': ['Caveat-Regular', 'cursive'],
        'caveat-medium': ['Caveat-Medium', 'cursive'],
        'caveat-semibold': ['Caveat-SemiBold', 'cursive'],
        'caveat-bold': ['Caveat-Bold', 'cursive'],
      },
      colors: {
        'window-black': '#191919',
        'esmerald-light': '#E6EFEF',
        'esmerald': '#002921',
        'esmerald-dark': '#001713',
        'green-light' : '#809490',
        'lemon': '#F0FF3D',
        'bone': '#FAF3E0',
        'brown': '#623721',
        'black': '#121212',
        'dark' : '#000000'
      },
      animation: {
        first: "moveVertical 30s ease infinite",
        second: "moveInCircle 20s reverse infinite",
        third: "moveInCircle 40s linear infinite",
        fourth: "moveHorizontal 40s ease infinite",
        fifth: "moveInCircle 20s ease infinite",
      },
      keyframes: {
        moveHorizontal: {
          "0%": {
            transform: "translateX(-50%) translateY(-10%)",
          },
          "50%": {
            transform: "translateX(50%) translateY(10%)",
          },
          "100%": {
            transform: "translateX(-50%) translateY(-10%)",
          },
        },
        moveInCircle: {
          "0%": {
            transform: "rotate(0deg)",
          },
          "50%": {
            transform: "rotate(180deg)",
          },
          "100%": {
            transform: "rotate(360deg)",
          },
        },
        moveVertical: {
          "0%": {
            transform: "translateY(-50%)",
          },
          "50%": {
            transform: "translateY(50%)",
          },
          "100%": {
            transform: "translateY(-50%)",
          },
        },
      },
    },
  },
  plugins: [],
}