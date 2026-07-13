'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { AlgaeAnimation } from './algae-animation'
import { 
  Compass, 
  Settings, 
  HelpCircle, 
  AlertTriangle, 
  RefreshCw, 
  Undo2, 
  ChevronRight, 
  Sliders, 
  BookOpen, 
  Info,
  Calendar,
  Thermometer,
  Droplet
} from 'lucide-react'

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
      reachable_yes?: string[]
      reachable_no?: string[]
    }
    final_diagnosis?: {
      species: string
      description?: string
    }
    candidates?: Candidate[]
    pre_filters?: {
      temp: number | null
      salinity: number | null
      station: number | null
      month: string | null
    }
    contradiction?: {
      conflict: string[]
      message: string
    } | null
    user_choices?: {
      character_name: string
      question: string
      answer: string
    }[]
  }
}

interface DiagnosisState {
  session_id: string
  status?: string
  question?: string
  character_name?: string
  is_final_node?: boolean
  result?: {
    species: string
    description?: string
  }
  candidates?: Candidate[]
  pre_filters?: {
    temp: number | null
    salinity: number | null
    station: number | null
    month: string | null
  }
  contradiction?: {
    conflict: string[]
    message: string
  } | null
  user_choices?: {
    character_name: string
    question: string
    answer: string
  }[]
  reachable_yes?: string[]
  reachable_no?: string[]
}

const getApiBaseUrl = () => {
  if (typeof window !== 'undefined') {
    const fromWindow = (window as Window & { __API_BASE_URL__?: string }).__API_BASE_URL__
    if (fromWindow) return fromWindow

    const fromEnv = process.env.NEXT_PUBLIC_API_BASE_URL
    if (fromEnv) return fromEnv

    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'https://sistema-experto-macroalgas.onrender.com'
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

  // Local state for environmental filters
  const [tempInput, setTempInput] = useState<string>('')
  const [salinityInput, setSalinityInput] = useState<string>('')
  const [stationInput, setStationInput] = useState<string>('')
  const [monthInput, setMonthInput] = useState<string>('')
  const [showFiltersMobile, setShowFiltersMobile] = useState(false)

  // XAI Panels Toggles
  const [showWhyPanel, setShowWhyPanel] = useState(true)

  useEffect(() => {
    initializeDiagnosis()
  }, [])

  // Sync environmental local inputs when state's pre_filters are returned
  useEffect(() => {
    if (state?.pre_filters) {
      setTempInput(state.pre_filters.temp !== null ? state.pre_filters.temp.toString() : '')
      setSalinityInput(state.pre_filters.salinity !== null ? state.pre_filters.salinity.toString() : '')
      setStationInput(state.pre_filters.station !== null ? state.pre_filters.station.toString() : '')
      
      // month usually arrives as "M1", "M2"... extract the number or keep it
      const m = state.pre_filters.month
      if (m && m.startsWith('M')) {
        setMonthInput(m.substring(1))
      } else {
        setMonthInput(m || '')
      }
    }
  }, [state?.pre_filters])

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
      const mappedState = mapApiResponseToState(data)
      setStateData(mappedState)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error de conexión'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const mapApiResponseToState = (data: DiagnosisResponse): DiagnosisState => {
    const { state } = data

    const isContradiction = state.status === 'contradiction' || (state.contradiction !== null && state.contradiction !== undefined)
    const isFinal = state.final_diagnosis || (!state.current_question && state.candidates && state.candidates.length > 0 && !isContradiction)

    if (isContradiction) {
      return {
        session_id: data.session_id,
        status: 'contradiction',
        is_final_node: false,
        contradiction: state.contradiction || { conflict: [], message: 'Combinación incompatible de caracteres.' },
        candidates: state.candidates || [],
        user_choices: state.user_choices || [],
        pre_filters: state.pre_filters,
      }
    }

    if (isFinal && state.candidates && state.candidates.length > 0) {
      const primaryCandidate = state.candidates[0]
      return {
        session_id: data.session_id,
        status: state.status,
        is_final_node: true,
        result: {
          species: primaryCandidate.species_name,
          description: primaryCandidate.description,
        },
        candidates: state.candidates,
        user_choices: state.user_choices || [],
        pre_filters: state.pre_filters,
      }
    }

    if (state.current_question) {
      return {
        session_id: data.session_id,
        status: state.status,
        question: state.current_question.question,
        character_name: state.current_question.character_name,
        is_final_node: false,
        candidates: state.candidates || [],
        user_choices: state.user_choices || [],
        pre_filters: state.pre_filters,
        reachable_yes: state.current_question.reachable_yes || [],
        reachable_no: state.current_question.reachable_no || [],
      }
    }

    return {
      session_id: data.session_id,
      status: state.status,
      candidates: state.candidates || [],
      user_choices: state.user_choices || [],
      pre_filters: state.pre_filters,
    }
  }

  const handleAnswer = async (answer: 'S' | 'N' | 'NS') => {
    if (!state?.character_name) return

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
      const mappedState = mapApiResponseToState(answerData)
      setStateData(mappedState)
      setQuestionCount(prev => prev + 1)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al procesar la respuesta'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleUndo = async () => {
    if (!state?.user_choices || state.user_choices.length === 0) return

    const lastChoice = state.user_choices[state.user_choices.length - 1]
    try {
      setLoading(true)
      setError(null)

      const apiBaseUrl = getApiBaseUrl()
      const response = await fetch(`${apiBaseUrl}/api/diagnosis/retract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          character_name: lastChoice.character_name,
        }),
        signal: AbortSignal.timeout(10000),
      })

      if (!response.ok) {
        throw new Error(`Error al deshacer: ${response.status}`)
      }

      const retractData: DiagnosisResponse = await response.json()
      const mappedState = mapApiResponseToState(retractData)
      setStateData(mappedState)
      setQuestionCount(prev => Math.max(0, prev - 1))
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al deshacer la acción'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleApplyFilters = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setLoading(true)
      setError(null)

      const apiBaseUrl = getApiBaseUrl()
      const response = await fetch(`${apiBaseUrl}/api/diagnosis/filters`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          temp: tempInput !== '' ? parseFloat(tempInput) : null,
          salinity: salinityInput !== '' ? parseFloat(salinityInput) : null,
          station: stationInput !== '' ? parseInt(stationInput) : null,
          month: monthInput !== '' ? parseInt(monthInput) : null,
        }),
        signal: AbortSignal.timeout(10000),
      })

      if (!response.ok) {
        throw new Error(`Error al aplicar filtros: ${response.status}`)
      }

      const filterData: DiagnosisResponse = await response.json()
      const mappedState = mapApiResponseToState(filterData)
      setStateData(mappedState)
      setShowFiltersMobile(false)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al aplicar filtros ambientales'
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
    // Clean local filters inputs
    setTempInput('')
    setSalinityInput('')
    setStationInput('')
    setMonthInput('')
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
          <p className="text-sm text-muted-foreground">Inicializando diagnóstico ficológico...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-background">
        <AlgaeAnimation />
        <div className="relative z-10 max-w-md p-8 text-center bg-card/60 backdrop-blur border border-border rounded-xl">
          <AlertTriangle className="w-12 h-12 text-destructive mx-auto mb-4" />
          <h2 className="text-xl font-light mb-2 text-foreground">Error de conexión</h2>
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

  // Render Environmental Form Elements
  const renderEnvironmentalFilters = () => (
    <form onSubmit={handleApplyFilters} className="space-y-4">
      <div>
        <label className="text-xs text-muted-foreground uppercase tracking-wider block mb-1 flex items-center gap-1 font-semibold">
          <Thermometer className="w-3.5 h-3.5 text-primary" />
          Temperatura (°C)
        </label>
        <div className="flex items-center gap-2">
          <input
            type="range"
            min="20"
            max="40"
            step="0.5"
            value={tempInput || '28'}
            onChange={(e) => setTempInput(e.target.value)}
            className="w-full h-1.5 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
            disabled={loading}
          />
          <input
            type="number"
            min="20"
            max="40"
            step="0.1"
            placeholder="N/A"
            value={tempInput}
            onChange={(e) => setTempInput(e.target.value)}
            className="w-16 bg-background text-sm text-center border border-border rounded p-1"
            disabled={loading}
          />
        </div>
        <p className="text-[10px] text-muted-foreground mt-0.5">Rango normal en Margarita: 25.0°C - 32.0°C</p>
      </div>

      <div>
        <label className="text-xs text-muted-foreground uppercase tracking-wider block mb-1 flex items-center gap-1 font-semibold">
          <Droplet className="w-3.5 h-3.5 text-primary" />
          Salinidad (ups)
        </label>
        <div className="flex items-center gap-2">
          <input
            type="range"
            min="20"
            max="50"
            step="0.5"
            value={salinityInput || '36'}
            onChange={(e) => setSalinityInput(e.target.value)}
            className="w-full h-1.5 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
            disabled={loading}
          />
          <input
            type="number"
            min="20"
            max="50"
            step="0.1"
            placeholder="N/A"
            value={salinityInput}
            onChange={(e) => setSalinityInput(e.target.value)}
            className="w-16 bg-background text-sm text-center border border-border rounded p-1"
            disabled={loading}
          />
        </div>
        <p className="text-[10px] text-muted-foreground mt-0.5">Rango normal en Margarita: 30.0 - 42.0 ups</p>
      </div>

      <div>
        <label className="text-xs text-muted-foreground uppercase tracking-wider block mb-1 flex items-center gap-1 font-semibold">
          <Compass className="w-3.5 h-3.5 text-primary" />
          Estación de Muestreo
        </label>
        <select
          value={stationInput}
          onChange={(e) => setStationInput(e.target.value)}
          className="w-full text-sm bg-background border border-border rounded p-2 focus:outline-none focus:ring-1 focus:ring-primary"
          disabled={loading}
        >
          <option value="">No Filtrar</option>
          <option value="1">Estación 1: La Caracola (Rocosa de alta energía)</option>
          <option value="2">Estación 2: La Caracola (Arenosa)</option>
          <option value="3">Estación 3: Playa Valdez (Pedregosa protegida)</option>
          <option value="4">Estación 4: Playa Valdez (Bahía somera fangosa)</option>
        </select>
      </div>

      <div>
        <label className="text-xs text-muted-foreground uppercase tracking-wider block mb-1 flex items-center gap-1 font-semibold">
          <Calendar className="w-3.5 h-3.5 text-primary" />
          Mes de Muestreo
        </label>
        <select
          value={monthInput}
          onChange={(e) => setMonthInput(e.target.value)}
          className="w-full text-sm bg-background border border-border rounded p-2 focus:outline-none focus:ring-1 focus:ring-primary"
          disabled={loading}
        >
          <option value="">No Filtrar</option>
          <option value="1">M1: Enero</option>
          <option value="2">M2: Febrero</option>
          <option value="3">M3: Marzo</option>
          <option value="4">M4: Abril</option>
          <option value="5">M5: Mayo</option>
          <option value="6">M6: Junio</option>
        </select>
        <p className="text-[10px] text-muted-foreground mt-0.5">Meses de colecta correspondientes al año ficológico.</p>
      </div>

      <div className="pt-2">
        <Button
          type="submit"
          disabled={loading}
          className="w-full bg-primary text-primary-foreground text-xs hover:bg-primary/95 transition-all"
        >
          {loading ? 'Procesando...' : 'Aplicar Filtros Ambientales'}
        </Button>
      </div>
    </form>
  )

  return (
    <div className="relative min-h-screen text-foreground py-6 px-4 md:px-8 max-w-7xl mx-auto flex flex-col justify-between">
      <AlgaeAnimation />

      {/* Top Header */}
      <header className="relative z-10 flex flex-col md:flex-row justify-between items-center gap-4 mb-8 pb-4 border-b border-border/50">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-primary/10 rounded-lg text-primary">
            <img src="/algaico.png" alt="Alga Icon" className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-foreground">
              Sistema Experto Ficológico
            </h1>
            <p className="text-xs text-muted-foreground font-light">
              Macroalgas Intermareales de la Isla de Margarita
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Mobile Filters Toggle */}
          <Button
            onClick={() => setShowFiltersMobile(!showFiltersMobile)}
            className="md:hidden bg-secondary text-secondary-foreground text-xs border border-border"
          >
            <Sliders className="w-3.5 h-3.5 mr-1.5" />
            Filtros Ambientales
          </Button>

          <Button
            onClick={handleRestart}
            variant="outline"
            className="text-xs border-border hover:bg-secondary hover:text-secondary-foreground"
          >
            <RefreshCw className="w-3 h-3 mr-1.5" />
            Reiniciar
          </Button>
        </div>
      </header>

      {/* Main Grid Layout */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-3 gap-8 items-start mb-8 flex-1">
        
        {/* LEFT / CENTER PANEL: Diagnosis Interactive Screens */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Contradiction / Conflict screen */}
          {state.status === 'contradiction' && state.contradiction && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-xl p-8 shadow-sm space-y-6 animate-fade-in-up">
              <div className="flex items-center gap-3 text-destructive">
                <AlertTriangle className="w-8 h-8" />
                <h2 className="text-2xl font-light">Incompatibilidad de Caracteres</h2>
              </div>
              
              <div className="bg-card rounded-lg p-5 border border-destructive/20 space-y-3">
                <p className="text-sm font-medium text-foreground leading-relaxed">
                  El Sistema de Mantenimiento de Verdad (JTMS) detectó un conflicto lógico:
                </p>
                <blockquote className="border-l-4 border-destructive bg-destructive/5 px-4 py-2 text-sm text-destructive-foreground italic font-mono rounded-r">
                  "{state.contradiction.message}"
                </blockquote>
                {state.contradiction.conflict && state.contradiction.conflict.length > 0 && (
                  <div className="pt-2">
                    <p className="text-xs text-muted-foreground uppercase font-bold tracking-wider mb-2">Caracteres en conflicto:</p>
                    <div className="flex flex-wrap gap-2">
                      {state.contradiction.conflict.map((char, index) => (
                        <span key={index} className="text-[11px] bg-destructive/15 text-destructive font-mono px-2 py-1 rounded border border-destructive/10">
                          {char}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <p className="text-sm text-muted-foreground">
                Las características anatómicas ingresadas violan las restricciones biológicas ficológicas de la taxonomía del catálogo de Margarita. Puedes deshacer la última respuesta para corregir el conflicto o iniciar un nuevo diagnóstico.
              </p>

              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <Button
                  onClick={handleUndo}
                  disabled={loading}
                  className="flex-1 bg-primary hover:bg-primary/95 text-primary-foreground text-sm font-light transition-all"
                >
                  <Undo2 className="w-4 h-4 mr-2" />
                  Deshacer Última Respuesta
                </Button>
                <Button
                  onClick={handleRestart}
                  variant="outline"
                  className="flex-1 border-border text-sm font-light hover:bg-secondary"
                >
                  Nuevo Diagnóstico
                </Button>
              </div>
            </div>
          )}

          {/* Final Result / Especie Identificada Screen */}
          {state.is_final_node && state.result && (
            <div className="space-y-6 animate-fade-in-up">
              <div className="bg-secondary/40 backdrop-blur rounded-xl border border-border p-6 md:p-8 space-y-6">
                
                {/* Header */}
                <div className="text-center pb-4 border-b border-border/50">
                  <span className="text-[11px] bg-primary/10 text-primary uppercase font-bold tracking-widest px-3 py-1 rounded-full">
                    Especie Clasificada Exitosamente
                  </span>
                  <h2 className="text-3xl md:text-4xl font-light text-foreground mt-3 italic">
                    {state.result.species}
                  </h2>
                </div>

                {state.candidates && state.candidates.length > 0 && (
                  <>
                    {/* Primary candidate specs */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-background/50 rounded-lg p-4 border border-border/50">
                      <div>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-0.5">Filo</p>
                        <p className="text-xs md:text-sm text-foreground font-semibold font-sans">{state.candidates[0].phylum}</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-0.5">Orden</p>
                        <p className="text-xs md:text-sm text-foreground font-semibold italic">{state.candidates[0].order}</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-0.5">Familia</p>
                        <p className="text-xs md:text-sm text-foreground font-semibold italic">{state.candidates[0].family}</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-0.5">Confianza Global</p>
                        <p className="text-xs md:text-sm text-primary font-bold">{Math.round(state.candidates[0].confidence)}%</p>
                      </div>
                    </div>

                    {/* Detailed info */}
                    <div className="space-y-4">
                      <div>
                        <h4 className="text-xs text-muted-foreground uppercase font-bold tracking-wider mb-1">Descripción Morfológica</h4>
                        <p className="text-sm text-foreground leading-relaxed font-sans font-light">
                          {state.candidates[0].description}
                        </p>
                      </div>
                      <div>
                        <h4 className="text-xs text-muted-foreground uppercase font-bold tracking-wider mb-1">Hábitat y Distribución (Margarita)</h4>
                        <p className="text-sm text-foreground leading-relaxed font-sans font-light">
                          {state.candidates[0].habitat_note}
                        </p>
                      </div>
                    </div>

                    {/* Details confidence metrics */}
                    <div className="grid grid-cols-3 gap-4 pt-4 border-t border-border/50 text-center">
                      <div>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-0.5">Confianza de Inferencia</p>
                        <p className="text-base md:text-lg font-semibold text-primary">{Math.round(state.candidates[0].path_confidence)}%</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-0.5">Ajuste Ecológico</p>
                        <p className="text-base md:text-lg font-semibold text-primary">{Math.round(state.candidates[0].env_fit)}%</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-0.5">Penalización Incertidumbre</p>
                        <p className="text-base md:text-lg font-semibold text-primary">
                          {state.candidates[0].confidence === state.candidates[0].env_fit ? 'Ninguna' : `-${~~(state.candidates[0].env_fit - state.candidates[0].confidence)}%`}
                        </p>
                      </div>
                    </div>

                    {/* Assumed characteristics paths */}
                    {state.candidates[0].assumed_chars && state.candidates[0].assumed_chars.length > 0 && (
                      <div className="pt-4 border-t border-border/50">
                        <h4 className="text-xs text-muted-foreground uppercase font-bold tracking-wider mb-3">
                          Justificación de Diagnóstico (JTMS / Caracteres Asumidos)
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-60 overflow-y-auto pr-2">
                          {state.candidates[0].assumed_chars.map((char, index) => (
                            <div key={index} className="bg-background/50 border border-border/50 rounded p-2.5 text-xs flex justify-between items-center">
                              <span className="text-muted-foreground font-sans pr-2 leading-tight">{char.question}</span>
                              <span className={`font-semibold shrink-0 text-[10px] px-2 py-0.5 rounded ${
                                char.value === 'Verdadero' 
                                  ? 'bg-primary/10 text-primary border border-primary/20' 
                                  : 'bg-muted text-muted-foreground border border-border'
                              }`}>
                                {char.value}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Close Candidates Accordion */}
              {state.candidates && state.candidates.length > 1 && (
                <div className="bg-card border border-border rounded-xl p-5 space-y-3">
                  <h4 className="text-xs text-muted-foreground uppercase font-bold tracking-wider">
                    Especies Candidatas Alternativas (Rutas Lógicas Paralelas)
                  </h4>
                  <div className="space-y-2">
                    {state.candidates.slice(1).map((candidate, idx) => (
                      <div key={idx} className="bg-secondary/20 rounded-lg p-3 border border-border/50 text-xs flex flex-col md:flex-row md:items-center justify-between gap-2">
                        <div>
                          <p className="font-semibold italic text-foreground text-sm">{candidate.species_name}</p>
                          <p className="text-muted-foreground text-[10px]">
                            {candidate.phylum} &bull; {candidate.family}
                          </p>
                        </div>
                        <div className="flex gap-4 shrink-0 text-right">
                          <div>
                            <p className="text-muted-foreground text-[9px] uppercase tracking-wider">Ajuste Ecológico</p>
                            <p className="font-medium text-foreground">{Math.round(candidate.env_fit)}%</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground text-[9px] uppercase tracking-wider">Confianza</p>
                            <p className="font-bold text-primary">{Math.round(candidate.confidence)}%</p>
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
                  className="bg-primary hover:bg-primary/95 text-primary-foreground text-sm font-light px-8 py-2"
                >
                  Iniciar Nuevo Diagnóstico
                </Button>
              </div>
            </div>
          )}

          {/* Active Question interrogation screen */}
          {!state.is_final_node && state.status !== 'contradiction' && (
            <div className="space-y-6">
              
              {/* Main Question Card */}
              <div className="bg-card rounded-xl border border-border p-6 md:p-8 shadow-sm relative overflow-hidden animate-fade-in-up">
                
                {/* Question Info Bar */}
                <div className="flex justify-between items-center mb-6">
                  <span className="text-[10px] bg-secondary text-secondary-foreground font-semibold px-2.5 py-1 rounded border border-border">
                    Pregunta {questionCount + 1}
                  </span>
                  
                  {state.user_choices && state.user_choices.length > 0 && (
                    <Button
                      onClick={handleUndo}
                      disabled={loading}
                      variant="ghost"
                      className="text-xs text-muted-foreground hover:text-foreground h-7 px-2.5"
                    >
                      <Undo2 className="w-3.5 h-3.5 mr-1" />
                      Deshacer anterior
                    </Button>
                  )}
                </div>

                {/* The Question */}
                <div className="mb-8">
                  <h2 className="text-2xl md:text-3xl font-light text-foreground leading-relaxed italic">
                    {state.question || 'Analizando base de datos...'}
                  </h2>
                </div>

                {/* Answer Options buttons */}
                <div className="flex flex-col sm:flex-row gap-3">
                  <Button
                    onClick={() => handleAnswer('S')}
                    disabled={loading}
                    className="flex-1 bg-primary hover:bg-primary/95 text-primary-foreground text-sm font-light border border-primary/30 transition-all hover:shadow-md py-6 rounded-lg"
                  >
                    {loading ? 'Procesando...' : 'Sí'}
                  </Button>

                  <Button
                    onClick={() => handleAnswer('N')}
                    disabled={loading}
                    className="flex-1 bg-secondary hover:bg-secondary/90 text-secondary-foreground text-sm font-light border border-border transition-all hover:shadow-md py-6 rounded-lg"
                  >
                    {loading ? 'Procesando...' : 'No'}
                  </Button>

                  <Button
                    onClick={() => handleAnswer('NS')}
                    disabled={loading}
                    className="flex-1 bg-muted/65 hover:bg-muted text-muted-foreground text-sm font-light border border-border transition-all hover:shadow-md py-6 rounded-lg"
                  >
                    {loading ? 'Procesando...' : 'No sé'}
                  </Button>
                </div>

                {/* Loading state indicator */}
                {loading && (
                  <div className="mt-4 flex justify-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse-soft" style={{ animationDelay: '0s' }} />
                    <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse-soft" style={{ animationDelay: '0.2s' }} />
                    <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse-soft" style={{ animationDelay: '0.4s' }} />
                  </div>
                )}
              </div>

              {/* Explainable AI (XAI) Panel - WHY THIS QUESTION */}
              {state.question && (
                <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
                  <button
                    onClick={() => setShowWhyPanel(!showWhyPanel)}
                    className="w-full px-5 py-4 flex items-center justify-between hover:bg-secondary/20 transition-all border-b border-border/40"
                  >
                    <span className="text-xs text-muted-foreground uppercase font-bold tracking-wider flex items-center gap-1.5">
                      <HelpCircle className="w-4 h-4 text-primary" />
                      ¿Por qué se realiza esta pregunta? (Explicación XAI)
                    </span>
                    <ChevronRight className={`w-4 h-4 transition-transform duration-300 ${showWhyPanel ? 'rotate-90' : ''}`} />
                  </button>

                  {showWhyPanel && (
                    <div className="p-5 space-y-4 text-xs leading-relaxed animate-fade-in-up font-sans">
                      <p className="text-muted-foreground">
                        Esta pregunta evalúa el carácter anatómico ficológico <code className="font-mono bg-secondary px-1 py-0.5 rounded text-foreground text-[11px] font-semibold">{state.character_name}</code> para descartar ramas lógicas incompatibles y reducir la incertidumbre diagnóstica.
                      </p>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                        {/* Reachable on Yes */}
                        <div className="bg-secondary/35 border border-border/50 rounded-lg p-3.5 space-y-2">
                          <p className="font-semibold text-primary flex items-center gap-1 text-[11px]">
                            <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                            Si respondes SÍ, te acercas a:
                          </p>
                          {state.reachable_yes && state.reachable_yes.length > 0 ? (
                            <ul className="space-y-1.5 text-foreground list-disc list-inside italic font-light font-serif">
                              {state.reachable_yes.slice(0, 5).map((sp, index) => (
                                <li key={index} className="truncate">{sp}</li>
                              ))}
                              {state.reachable_yes.length > 5 && (
                                <li className="list-none text-muted-foreground text-[10px] pl-3">
                                  ...y {state.reachable_yes.length - 5} especies más.
                                </li>
                              )}
                            </ul>
                          ) : (
                            <p className="text-muted-foreground text-[11px] italic">Ninguna especie catalogada (podría causar contradicción).</p>
                          )}
                        </div>

                        {/* Reachable on No */}
                        <div className="bg-secondary/35 border border-border/50 rounded-lg p-3.5 space-y-2">
                          <p className="font-semibold text-primary flex items-center gap-1 text-[11px]">
                            <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                            Si respondes NO, te desvías hacia:
                          </p>
                          {state.reachable_no && state.reachable_no.length > 0 ? (
                            <ul className="space-y-1.5 text-foreground list-disc list-inside italic font-light font-serif">
                              {state.reachable_no.slice(0, 5).map((sp, index) => (
                                <li key={index} className="truncate">{sp}</li>
                              ))}
                              {state.reachable_no.length > 5 && (
                                <li className="list-none text-muted-foreground text-[10px] pl-3">
                                  ...y {state.reachable_no.length - 5} especies más.
                                </li>
                              )}
                            </ul>
                          ) : (
                            <p className="text-muted-foreground text-[11px] italic">Ninguna especie catalogada (podría causar contradicción).</p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* RIGHT PANEL (Desktop): Environmental Calibration & Traceability */}
        <div className="space-y-6 lg:col-span-1">
          
          {/* Desktop Environmental Calibration Card */}
          <div className="hidden md:block bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
            <h3 className="text-xs text-muted-foreground uppercase font-bold tracking-wider border-b border-border/50 pb-2 flex items-center gap-1.5">
              <Sliders className="w-4 h-4 text-primary" />
              Parámetros Ecológicos
            </h3>
            {renderEnvironmentalFilters()}
          </div>

          {/* Active Environmental Filters Status badge */}
          {(state.pre_filters?.temp || state.pre_filters?.salinity || state.pre_filters?.station || state.pre_filters?.month) && (
            <div className="bg-primary/5 border border-primary/20 rounded-xl p-4 text-xs space-y-2.5">
              <p className="font-semibold text-primary uppercase tracking-wider text-[10px]">Filtros Activos en Diagnóstico:</p>
              <div className="flex flex-wrap gap-1.5">
                {state.pre_filters.temp && (
                  <span className="bg-background border border-border px-2 py-0.5 rounded-full font-mono">
                    Temp: {state.pre_filters.temp}°C
                  </span>
                )}
                {state.pre_filters.salinity && (
                  <span className="bg-background border border-border px-2 py-0.5 rounded-full font-mono">
                    Sal: {state.pre_filters.salinity} ups
                  </span>
                )}
                {state.pre_filters.station && (
                  <span className="bg-background border border-border px-2 py-0.5 rounded-full">
                    Estación: {state.pre_filters.station}
                  </span>
                )}
                {state.pre_filters.month && (
                  <span className="bg-background border border-border px-2 py-0.5 rounded-full">
                    Mes: {state.pre_filters.month}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Traceability / User Choices History Card */}
          <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
            <h3 className="text-xs text-muted-foreground uppercase font-bold tracking-wider border-b border-border/50 pb-2 flex items-center gap-1.5">
              <BookOpen className="w-4 h-4 text-primary" />
              Trazabilidad del Razonamiento
            </h3>
            
            {state.user_choices && state.user_choices.length > 0 ? (
              <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
                {state.user_choices.map((choice, index) => (
                  <div key={index} className="bg-secondary/25 border border-border/40 rounded p-2.5 text-xs flex flex-col gap-1.5">
                    <div className="flex justify-between items-start gap-2">
                      <span className="font-semibold text-primary text-[10px]">C{index + 1}: {choice.character_name}</span>
                      <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${
                        choice.answer === 'Sí' 
                          ? 'text-primary bg-primary/10' 
                          : choice.answer === 'No'
                            ? 'text-destructive bg-destructive/10'
                            : 'text-muted-foreground bg-muted'
                      }`}>
                        {choice.answer}
                      </span>
                    </div>
                    <p className="text-muted-foreground leading-tight text-[11px]">{choice.question}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6 text-xs text-muted-foreground italic">
                No hay decisiones tomadas todavía. Comienza a responder para ver la trazabilidad de la inferencia.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Environmental Filters Overlay (Drawer) */}
      {showFiltersMobile && (
        <div className="fixed inset-0 z-50 flex items-end bg-background/80 backdrop-blur-sm md:hidden animate-fade-in-up">
          <div className="w-full bg-card rounded-t-2xl border-t border-border p-6 space-y-4 shadow-lg max-h-[85vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-border pb-2">
              <h3 className="text-sm text-foreground font-semibold flex items-center gap-1.5">
                <Sliders className="w-4 h-4 text-primary" />
                Filtros Ambientales (Calibración)
              </h3>
              <Button
                onClick={() => setShowFiltersMobile(false)}
                variant="ghost"
                className="h-8 w-8 p-0"
              >
                &times;
              </Button>
            </div>
            {renderEnvironmentalFilters()}
          </div>
        </div>
      )}

      {/* Footer / Copyright / Metadata */}
      <footer className="relative z-10 flex flex-col md:flex-row justify-between items-center text-[10px] text-muted-foreground pt-4 border-t border-border/30 gap-2 w-full">
        <p className="font-sans font-light text-center md:text-left">
          Realizado por: Jorge Garcia. Jesús Jiménez.
        </p>
        <p className="font-sans font-light text-center hidden lg:block opacity-60">
          Metodología de Buchanan &bull; Tesis Ficológica Isla de Margarita &bull; UDO Nueva Esparta
        </p>
        <p className="font-sans font-light text-center md:text-right">
          Prof. José Murillo.
        </p>
      </footer>
    </div>
  )
}
