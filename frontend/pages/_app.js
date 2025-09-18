import { useEffect, useState } from 'react'
import '../styles/globals.css'

export default function App({ Component, pageProps }) {
  const [theme, setTheme] = useState('dark')

  useEffect(() => {
    const stored = localStorage.getItem('theme')
    if (stored) setTheme(stored)
  }, [])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem('theme', theme)
  }, [theme])

  return (
    <div>
      <button 
        onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        className="fixed top-4 right-4 p-2 bg-secondary rounded-lg"
      >
        {theme === 'dark' ? '🌙' : '🌞'}
      </button>
      <Component {...pageProps} />
    </div>
  )
}
