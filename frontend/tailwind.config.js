/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      colors: {
        'background': '#0A090C', // Un negro casi puro para el fondo
        'surface': '#131217',   // Un gris muy oscuro para las tarjetas
        'primary': '#7E42FF',    // Nuestro morado principal para acciones
        'primary-hover': '#905EFF',
        'secondary': '#2A292F', // Un color sutil para bordes y elementos secundarios
        'accent': '#00F5D4',     // Un toque de color vibrante (opcional)
        'text-main': '#F0F0F0',
        'text-secondary': '#A0A0A0',
      },
      boxShadow: {
        'glow': '0 0 20px 0 rgba(126, 66, 255, 0.3)',
      }
    },
  },
  plugins: [],
}