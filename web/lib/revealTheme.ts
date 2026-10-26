import { flushSync } from 'react-dom'

const REVEAL_MS = 800

type ThemeName = 'light' | 'dark'

function canReveal() {
  return (
    'startViewTransition' in document &&
    !window.matchMedia('(prefers-reduced-motion: reduce)').matches
  )
}

function applyTheme(theme: ThemeName, setTheme: (theme: string) => void) {
  document.documentElement.classList.toggle('dark', theme === 'dark')
  setTheme(theme)
}

function afterPaint() {
  return new Promise<void>((resolve) => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => resolve())
    })
  })
}

export async function revealThemeChange(
  theme: ThemeName,
  setTheme: (theme: string) => void
) {
  if (!canReveal()) {
    applyTheme(theme, setTheme)
    return
  }

  const radius = Math.hypot(window.innerWidth, window.innerHeight)
  const transition = document.startViewTransition(() => {
    flushSync(() => applyTheme(theme, setTheme))
  })

  try {
    await transition.ready
    await afterPaint()

    const timing: KeyframeAnimationOptions = {
      duration: REVEAL_MS,
      easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
      fill: 'both',
    }

    document.documentElement.animate(
      { opacity: [1, 1] },
      { ...timing, pseudoElement: '::view-transition-group(root)' }
    )

    document.documentElement.animate(
      {
        clipPath: ['circle(0px at 0px 0px)', `circle(${radius}px at 0px 0px)`],
      },
      { ...timing, pseudoElement: '::view-transition-new(root)' }
    )
  } catch {}
}
