'use client'

import { useEffect, useState } from 'react'
import { DiagnosisInterface } from '@/components/diagnosis-interface'
import { LoadingScreen } from '@/components/loading-screen'

export default function Page() {
  const [apiReady, setApiReady] = useState(false)
  const [showTimeout, setShowTimeout] = useState(false)
  const [isHydrated, setIsHydrated] = useState(false)
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    setIsHydrated(true)

    const savedTheme = window.localStorage.getItem('theme')
    if (savedTheme === 'dark' || savedTheme === 'light') {
      setTheme(savedTheme)
    }

    // Check API health with 8 second timeout
    const timeoutId = setTimeout(() => {
      if (!apiReady) {
        setShowTimeout(true)
      }
    }, 8000)

    const checkHealth = async () => {
      try {
        const candidates = [
          'http://127.0.0.1:8000/health',
          'https://sistema-experto-macroalgas.onrender.com/health',
        ]

        for (const url of candidates) {
          try {
            const response = await fetch(url, { signal: AbortSignal.timeout(4000) })
            if (response.ok) {
              clearTimeout(timeoutId)
              setApiReady(true)
              setShowTimeout(false)
              return
            }
          } catch {
            // Try next candidate
          }
        }
      } catch {
        // API error - will show loading screen
      }
    }

    checkHealth()

    return () => clearTimeout(timeoutId)
  }, [apiReady])

  useEffect(() => {
    document.documentElement.classList.remove('light', 'dark')
    document.documentElement.classList.add(theme)
    window.localStorage.setItem('theme', theme)
  }, [theme])

  if (!isHydrated) {
    return <LoadingScreen />
  }

  if (showTimeout || !apiReady) {
    return <LoadingScreen />
  }

  return (
    <main className="relative min-h-screen bg-background">
      <DiagnosisInterface theme={theme} onThemeToggle={() => setTheme(theme === 'dark' ? 'light' : 'dark')} />
    </main>
  )
}
