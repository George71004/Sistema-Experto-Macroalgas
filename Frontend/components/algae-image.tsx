'use client'

import { useEffect, useState } from 'react'

interface AlgaeImageProps {
  speciesName: string
}

const getApiBaseUrl = () => {
  if (typeof window !== 'undefined') {
    const fromEnv = process.env.NEXT_PUBLIC_API_BASE_URL
    if (fromEnv) return fromEnv

    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'http://localhost:8000'
    }
  }
  return 'https://sistema-experto-macroalgas.onrender.com'
}

export function AlgaeImage({ speciesName }: AlgaeImageProps) {
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const [isGenusFallback, setIsGenusFallback] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!speciesName) return

    let active = true
    setLoading(true)

    async function fetchImage() {
      try {
        const apiBaseUrl = getApiBaseUrl()
        const response = await fetch(`${apiBaseUrl}/api/species-image?name=${encodeURIComponent(speciesName)}`)
        
        if (response.ok && active) {
          const data = await response.json()
          setImageUrl(data.image_url)
          setIsGenusFallback(data.is_genus_fallback)
        }
      } catch (e) {
        if (active) {
          setImageUrl(null)
          setIsGenusFallback(false)
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    fetchImage()

    return () => {
      active = false
    }
  }, [speciesName])

  if (loading) {
    return (
      <div className="w-full h-48 md:h-64 rounded-xl bg-secondary/50 animate-pulse flex items-center justify-center border border-border/50">
        <span className="text-xs text-muted-foreground font-light font-sans">Buscando imagen de la especie...</span>
      </div>
    )
  }

  const cleanSpeciesName = speciesName.split(' ').slice(0, 2).join(' ')
  const genusName = speciesName.split(' ')[0]

  if (!imageUrl) {
    return (
      <div className="w-full h-48 md:h-64 rounded-xl bg-secondary/20 border border-dashed border-border flex flex-col items-center justify-center p-6 text-center">
        <svg className="w-8 h-8 text-muted-foreground/40 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <p className="text-xs text-muted-foreground font-sans font-light">
          No hay imagen ilustrativa disponible para el género o especie de <em>{cleanSpeciesName}</em>
        </p>
      </div>
    )
  }

  return (
    <div className="relative w-full h-56 md:h-72 rounded-xl overflow-hidden border border-border bg-secondary/30 group shadow-sm">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={imageUrl}
        alt={speciesName}
        className="w-full h-full object-cover transition-all duration-700 group-hover:scale-105"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-background/95 via-background/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-4">
        <p className="text-[10px] text-muted-foreground font-sans">
          {isGenusFallback ? (
            <>
              Fotografía del género <em>{genusName}</em> (imagen de referencia vía Wikipedia)
            </>
          ) : (
            <>
              Fotografía de <em>{cleanSpeciesName}</em> obtenida vía Wikipedia
            </>
          )}
        </p>
      </div>
    </div>
  )
}
