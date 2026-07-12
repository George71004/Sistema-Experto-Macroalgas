export function AlgaeAnimation() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden">
      {/* Alga 1 */}
      <div className="absolute top-20 left-10 animate-float opacity-60">
        <svg width="40" height="80" viewBox="0 0 40 80" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M20 0 Q 15 15 18 30 Q 20 40 15 55 Q 12 65 20 80" stroke="currentColor" strokeWidth="2" className="text-primary" />
          <circle cx="12" cy="25" r="2" fill="currentColor" className="text-primary" />
          <circle cx="18" cy="45" r="2" fill="currentColor" className="text-primary" />
          <circle cx="10" cy="65" r="2" fill="currentColor" className="text-primary" />
        </svg>
      </div>

      {/* Alga 2 */}
      <div className="absolute top-40 right-20 animate-float-slow opacity-50">
        <svg width="35" height="75" viewBox="0 0 35 75" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M17 0 Q 12 12 15 25 Q 18 38 12 52 Q 10 62 17 75" stroke="currentColor" strokeWidth="2" className="text-primary opacity-80" />
          <circle cx="10" cy="20" r="1.5" fill="currentColor" className="text-primary" />
          <circle cx="16" cy="40" r="1.5" fill="currentColor" className="text-primary" />
          <circle cx="8" cy="60" r="1.5" fill="currentColor" className="text-primary" />
        </svg>
      </div>

      {/* Alga 3 */}
      <div className="absolute bottom-32 left-1/4 animate-float-delayed opacity-40">
        <svg width="38" height="85" viewBox="0 0 38 85" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M19 0 Q 25 18 20 35 Q 15 50 22 65 Q 25 75 19 85" stroke="currentColor" strokeWidth="2" className="text-primary" />
          <circle cx="28" cy="28" r="2" fill="currentColor" className="text-primary opacity-70" />
          <circle cx="20" cy="50" r="2" fill="currentColor" className="text-primary opacity-70" />
          <circle cx="26" cy="70" r="2" fill="currentColor" className="text-primary opacity-70" />
        </svg>
      </div>

      {/* Alga 4 */}
      <div className="absolute bottom-20 right-1/3 animate-float opacity-55">
        <svg width="32" height="70" viewBox="0 0 32 70" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M16 0 Q 10 12 14 28 Q 18 42 11 58 Q 8 65 16 70" stroke="currentColor" strokeWidth="2" className="text-primary" />
          <circle cx="8" cy="18" r="1.5" fill="currentColor" className="text-primary" />
          <circle cx="14" cy="38" r="1.5" fill="currentColor" className="text-primary" />
          <circle cx="5" cy="55" r="1.5" fill="currentColor" className="text-primary" />
        </svg>
      </div>

      {/* Alga 5 - Pequeña */}
      <div className="absolute top-1/3 right-1/4 animate-float-slow opacity-45">
        <svg width="25" height="60" viewBox="0 0 25 60" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 0 Q 8 10 10 20 Q 12 32 8 45 Q 6 52 12 60" stroke="currentColor" strokeWidth="1.5" className="text-primary" />
          <circle cx="5" cy="15" r="1" fill="currentColor" className="text-primary opacity-60" />
          <circle cx="10" cy="35" r="1" fill="currentColor" className="text-primary opacity-60" />
        </svg>
      </div>
    </div>
  )
}
