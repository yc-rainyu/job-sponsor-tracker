import { flushSync } from 'react-dom'

// same length as ::view-transition-group(root) in globals.css
const REVEAL_MS = 800

type ThemeName = 'light' | 'dark'

function applyTheme(theme: ThemeName, setTheme: (theme: string) => void) {
  // next-themes sets the class in an effect, too late for the new snapshot
  document.documentElement.classList.toggle('dark', theme === 'dark')
  setTheme(theme)
}

export async function revealThemeChange(
  theme: ThemeName,
  setTheme: (theme: string) => void
) {
  const reduceMotion = window.matchMedia(
    '(prefers-reduced-motion: reduce)'
  ).matches
  if (!('startViewTransition' in document) || reduceMotion) {
    applyTheme(theme, setTheme)
    return
  }

  const transition = document.startViewTransition(() => {
    flushSync(() => applyTheme(theme, setTheme))
  })
  try {
    await transition.ready
  } catch {
    // a second toggle before this one finished skips it, nothing to animate
    return
  }

  // grow the new theme as a circle from the top left, where the toggle sits
  const radius = Math.hypot(window.innerWidth, window.innerHeight)
  document.documentElement.animate(
    { clipPath: ['circle(0px at 0px 0px)', `circle(${radius}px at 0px 0px)`] },
    {
      duration: REVEAL_MS,
      easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
      pseudoElement: '::view-transition-new(root)',
    }
  )
}
