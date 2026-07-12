'use client'

import { AlgaeAnimation } from './algae-animation'

export function LoadingScreen() {
  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center bg-background z-50">
      <AlgaeAnimation />
      
      <div className="relative z-10 flex flex-col items-center gap-6">
        {/* Animated loading dots */}
        <div className="flex gap-2">
          <div className="w-3 h-3 rounded-full bg-primary animate-pulse-soft" style={{ animationDelay: '0s' }} />
          <div className="w-3 h-3 rounded-full bg-primary animate-pulse-soft" style={{ animationDelay: '0.2s' }} />
          <div className="w-3 h-3 rounded-full bg-primary animate-pulse-soft" style={{ animationDelay: '0.4s' }} />
        </div>
        
        <div className="text-center">
          <h2 className="text-lg font-light text-foreground mb-2">Conectando con el sistema...</h2>
          <p className="text-sm text-muted-foreground">Por favor espera mientras se carga el diagnóstico</p>
        </div>
      </div>
    </div>
  )
}
