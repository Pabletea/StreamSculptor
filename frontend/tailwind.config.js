/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class', // Habilitar el modo oscuro basado en clase
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
        // Usar variables CSS para que los temas funcionen
        background: 'hsl(var(--background))',
        surface: 'hsl(var(--surface))',
        primary: 'hsl(var(--primary))',
        'primary-hover': 'hsl(var(--primary-hover))',
        secondary: 'hsl(var(--secondary))',
        'text-main': 'hsl(var(--text-main))',
        'text-secondary': 'hsl(var(--text-secondary))',
      },
      boxShadow: {
        // La sombra también usará la variable de color primario
        'glow': '0 0 20px 0 hsl(var(--primary) / 0.3)',
      }
    },
  },
  plugins: [],
}