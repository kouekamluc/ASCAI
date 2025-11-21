/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.{html,js}",
    "./apps/**/*.{html,js,py}",
    "./static/js/**/*.{js,ts}",
  ],
  theme: {
    extend: {
      colors: {
        "cameroon-green": "#2D5016",
        "cameroon-red": "#CE1126",
        "cameroon-yellow": "#FCD116",
      },
    },
  },
  plugins: [],
};

