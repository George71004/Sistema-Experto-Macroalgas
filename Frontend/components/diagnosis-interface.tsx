'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { AlgaeAnimation } from './algae-animation'

interface AssumedCharacter {
  character: string
  question: string
  value: string
}

interface Candidate {
  species_id: string
  species_name: string
  phylum: string
  order: string
  family: string
  description: string
  habitat_note: string
  confidence: number
  env_fit: number
  path_confidence: number
  assumed_chars: AssumedCharacter[]
}

interface DiagnosisResponse {
  session_id: string
  state: {
    status: string
    current_question?: {
      node_id: string
      question: string
      character_name: string
    }
    final_diagnosis?: {
      species: string
      description?: string
    }
    candidates?: Candidate[]
  }
}

interface DiagnosisState {
  session_id: string
  question?: string
  character_name?: string
  is_final_node?: boolean
  result?: {
    species: string
    description?: string
  }
  candidates?: Candidate[]
}

const getApiBaseUrl = () => {
  if (typeof window !== 'undefined') {
    const fromWindow = (window as Window & { __API_BASE_URL__?: string }).__API_BASE_URL__
    if (fromWindow) return fromWindow

    const fromEnv = process.env.NEXT_PUBLIC_API_BASE_URL
    if (fromEnv) return fromEnv

    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'http://127.0.0.1:8000'
    }
  }

  return 'https://sistema-experto-macroalgas.onrender.com'
}

export function DiagnosisInterface() {
  const [state, setStateData] = useState<DiagnosisState | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sessionId] = useState(() => `session_${Date.now()}`)
  const [questionCount, setQuestionCount] = useState(0)

  useEffect(() => {
    initializeDiagnosis()
  }, [])

  const initializeDiagnosis = async () => {
    try {
      setLoading(true)
      setError(null)
      setQuestionCount(0)

      const apiBaseUrl = getApiBaseUrl()
      const response = await fetch(`${apiBaseUrl}/api/diagnosis/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
        signal: AbortSignal.timeout(10000),
      })

      if (!response.ok) {
        throw new Error(`Error al iniciar diagnóstico: ${response.status}`)
      }

      const data: DiagnosisResponse = await response.json()

      // Map API response to internal state
      const mappedState = mapApiResponseToState(data)
      setStateData(mappedState)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const mapApiResponseToState = (data: DiagnosisResponse): DiagnosisState => {
    const { state } = data

    // Check if it's a final diagnosis (either final_diagnosis is set OR no current_question and candidates exist)
    const isFinal = state.final_diagnosis || (!state.current_question && state.candidates && state.candidates.length > 0)

    if (isFinal && state.candidates && state.candidates.length > 0) {
      // Use the first candidate as the result
      const primaryCandidate = state.candidates[0]
      return {
        session_id: data.session_id,
        is_final_node: true,
        result: {
          species: primaryCandidate.species_name,
          description: primaryCandidate.description,
        },
        candidates: state.candidates,
      }
    }

    // If it's a question
    if (state.current_question) {
      return {
        session_id: data.session_id,
        question: state.current_question.question,
        character_name: state.current_question.character_name,
        is_final_node: false,
      }
    }

    return {
      session_id: data.session_id,
    }
  }

  const handleAnswer = async (answer: 'S' | 'N' | 'NS') => {
    if (!state?.character_name) {
      return
    }

    try {
      setLoading(true)
      setError(null)

      const apiBaseUrl = getApiBaseUrl()
      const response = await fetch(`${apiBaseUrl}/api/diagnosis/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          character_name: state.character_name,
          answer: answer,
        }),
        signal: AbortSignal.timeout(10000),
      })

      if (!response.ok) {
        throw new Error(`Error al procesar respuesta: ${response.status}`)
      }

      const answerData: DiagnosisResponse = await response.json()

      // Map the response and update state directly
      const mappedState = mapApiResponseToState(answerData)
      setStateData(mappedState)
      setQuestionCount(prev => prev + 1)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleRestart = async () => {
    try {
      const apiBaseUrl = getApiBaseUrl()
      await fetch(`${apiBaseUrl}/api/diagnosis/session?session_id=${sessionId}`, {
        method: 'DELETE',
        signal: AbortSignal.timeout(10000),
      })
    } catch (err) {
      // Silently fail on cleanup
    }
    setStateData(null)
    initializeDiagnosis()
  }

  if (loading && !state) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-background">
        <AlgaeAnimation />
        <div className="relative z-10 text-center">
          <div className="flex gap-2 mb-6 justify-center">
            <div className="w-3 h-3 rounded-full bg-primary animate-pulse-soft" style={{ animationDelay: '0s' }} />
            <div className="w-3 h-3 rounded-full bg-primary animate-pulse-soft" style={{ animationDelay: '0.2s' }} />
            <div className="w-3 h-3 rounded-full bg-primary animate-pulse-soft" style={{ animationDelay: '0.4s' }} />
          </div>
          <p className="text-sm text-muted-foreground">Iniciando diagnóstico...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-background">
        <AlgaeAnimation />
        <div className="relative z-10 max-w-md p-8 text-center">
          <h2 className="text-xl font-light mb-4 text-foreground">Error de conexión</h2>
          <p className="text-sm text-muted-foreground mb-6">{error}</p>
          <Button
            onClick={initializeDiagnosis}
            className="bg-primary hover:bg-primary/90 text-primary-foreground"
          >
            Reintentar
          </Button>
        </div>
      </div>
    )
  }

  if (!state) return null

  // Final result screen
  if (state.is_final_node && state.result) {
    const primaryCandidate = state.candidates?.[0]

    return (
      <div className="fixed inset-0 flex items-center justify-center bg-background min-h-screen overflow-y-auto py-8">
        <AlgaeAnimation />
        <div className="relative z-10 max-w-3xl mx-auto px-4 animate-fade-in-up">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-light mb-2 text-foreground">¡Especie Identificada!</h1>
            <p className="text-primary text-lg font-medium">{state.result.species}</p>
          </div>

          {/* Primary candidate details */}
          {primaryCandidate && (
            <div className="bg-secondary/50 rounded-lg p-8 mb-8 border border-border space-y-6">
              {/* Taxonomic information */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Filo</p>
                  <p className="text-sm text-foreground font-medium">{primaryCandidate.phylum}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Orden</p>
                  <p className="text-sm text-foreground font-medium">{primaryCandidate.order}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Familia</p>
                  <p className="text-sm text-foreground font-medium">{primaryCandidate.family}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Confianza</p>
                  <p className="text-sm text-primary font-medium">{Math.round(primaryCandidate.confidence)}%</p>
                </div>
              </div>

              {/* Description */}
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide mb-2">Descripción</p>
                <p className="text-sm text-foreground leading-relaxed">{primaryCandidate.description}</p>
              </div>

              {/* Habitat */}
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide mb-2">Hábitat</p>
                <p className="text-sm text-foreground leading-relaxed">{primaryCandidate.habitat_note}</p>
              </div>

              {/* Assumed characteristics */}
              {primaryCandidate.assumed_chars && primaryCandidate.assumed_chars.length > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-3">Características asumidas</p>
                  <div className="space-y-3">
                    {primaryCandidate.assumed_chars.map((char, idx) => (
                      <div key={idx} className="bg-background/50 rounded p-3 border border-border/50">
                        <p className="text-xs text-primary font-medium mb-1">{char.question}</p>
                        <p className="text-sm text-foreground">
                          <span className="font-medium">Respuesta:</span> {char.value}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Confidence metrics */}
              <div className="grid grid-cols-3 gap-4 pt-4 border-t border-border">
                <div className="text-center">
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Confianza ruta</p>
                  <p className="text-lg font-medium text-primary">{Math.round(primaryCandidate.path_confidence)}%</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Ajuste ambiental</p>
                  <p className="text-lg font-medium text-primary">{Math.round(primaryCandidate.env_fit)}%</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Confianza general</p>
                  <p className="text-lg font-medium text-primary">{Math.round(primaryCandidate.confidence)}%</p>
                </div>
              </div>
            </div>
          )}

          {/* Other candidates */}
          {state.candidates && state.candidates.length > 1 && (
            <div className="bg-muted/30 rounded-lg p-6 mb-8 border border-border">
              <p className="text-xs text-muted-foreground uppercase tracking-wide mb-4">Candidatos cercanos</p>
              <div className="space-y-3">
                {state.candidates.slice(1).map((candidate, idx) => (
                  <div key={idx} className="bg-background/50 rounded p-4 border border-border/50">
                    <div className="flex justify-between items-start gap-4">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-foreground mb-1">{candidate.species_name}</p>
                        <p className="text-xs text-muted-foreground">{candidate.family}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-primary">{Math.round(candidate.confidence)}%</p>
                        <p className="text-xs text-muted-foreground">confianza</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-center">
            <Button
              onClick={handleRestart}
              className="bg-primary hover:bg-primary/90 text-primary-foreground"
            >
              Nuevo Diagnóstico
            </Button>
          </div>
        </div>
      </div>
    )
  }

  // Question screen
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-background min-h-screen px-4">
      <AlgaeAnimation />

      <div className="relative z-10 max-w-2xl w-full animate-fade-in-up">
        <div className="bg-card rounded-lg border border-border p-8 shadow-sm">
          {/* Question */}
          <div className="mb-8">
            <h2 className="text-2xl font-light text-foreground mb-4 leading-relaxed">
              {state.question || 'Cargando pregunta...'}
            </h2>
            <p className="text-xs text-muted-foreground uppercase tracking-wide">Pregunta {questionCount + 1}</p>
          </div>

          {/* Answer buttons */}
          <div className="flex flex-col gap-3 sm:flex-row sm:gap-4">
            <Button
              onClick={() => handleAnswer('S')}
              disabled={loading}
              className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground font-light border border-primary transition-all duration-300 hover:shadow-md"
            >
              {loading ? 'Procesando...' : 'Sí'}
            </Button>

            <Button
              onClick={() => handleAnswer('N')}
              disabled={loading}
              className="flex-1 bg-secondary hover:bg-secondary/80 text-secondary-foreground font-light border border-border transition-all duration-300 hover:shadow-md"
            >
              {loading ? 'Procesando...' : 'No'}
            </Button>

            <Button
              onClick={() => handleAnswer('NS')}
              disabled={loading}
              className="flex-1 bg-muted hover:bg-muted/80 text-muted-foreground font-light border border-border transition-all duration-300 hover:shadow-md"
            >
              {loading ? 'Procesando...' : 'No sé'}
            </Button>
          </div>

          {/* Loading state */}
          {loading && (
            <div className="mt-6 flex justify-center gap-2">
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse-soft" style={{ animationDelay: '0s' }} />
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse-soft" style={{ animationDelay: '0.2s' }} />
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse-soft" style={{ animationDelay: '0.4s' }} />
            </div>
          )}
        </div>

        {/* Info text */}
        <p className="text-center text-xs text-muted-foreground mt-6 font-light">
          Responde basándote en las características de la especie de alga observada
        </p>
      </div>
    </div>
  )
}
