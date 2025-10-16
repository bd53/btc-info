/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        inter: ['Inter var', 'sans-serif'],
      },
      fontFeatureSettings: {
        'slashed-zero': '"zero"',
      },
      colors: {
        'ongy': '#ED9B60',
        'blig': '#000000',
        'gwey': '#999999'
      },
    },
  },
  plugins: [
    function ({ addUtilities }) {
      addUtilities({
        '.font-slashed-zero': {
          fontFeatureSettings: '"zero"',
        },
      });
    },
  ],
};
