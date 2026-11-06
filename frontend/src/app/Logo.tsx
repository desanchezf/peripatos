/** Una stoa: la columnata por la que se paseaba en el Liceo */
export function Logo({ size = 24 }: { size?: number }) {
  return (
    <svg className="pt-logo" viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden>
      <path d="M3 6h18M3 21h18M6 6v15M12 6v15M18 6v15M5 3h14" />
    </svg>
  )
}
