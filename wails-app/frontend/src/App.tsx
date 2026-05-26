import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import Converter from './screens/Converter'
import Manual from './screens/Manual'
import { THEMES, ThemePalette, getAppVars } from './themes'

export type Screen = 'converter' | 'manual'
export type ThemeMode = 'light' | 'dark' | 'system'
export type { ThemePalette }

const THEME_KEY = 'df-theme'
const PALETTE_KEY = 'df-palette'

function getSystemDark() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

function applyTheme(mode: ThemeMode) {
  const dark = mode === 'system' ? getSystemDark() : mode === 'dark'
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
}

function loadTheme(): ThemeMode {
  const saved = localStorage.getItem(THEME_KEY) as ThemeMode | null
  return saved ?? 'system'
}

function applyPalette(palette: ThemePalette, dark: boolean) {
  const colors = THEMES[palette][dark ? 'dark' : 'light']
  const vars = getAppVars(colors)
  const root = document.documentElement
  Object.entries(vars).forEach(([key, value]) => {
    root.style.setProperty(key, value)
  })
}

function loadPalette(): ThemePalette {
  const saved = localStorage.getItem(PALETTE_KEY) as ThemePalette | null
  return saved ?? 'default'
}

export default function App() {
  const [screen, setScreen] = useState<Screen>('converter')
  const [theme, setTheme] = useState<ThemeMode>(() => {
    const t = loadTheme()
    applyTheme(t)
    return t
  })
  const [palette, setPalette] = useState<ThemePalette>(() => {
    const p = loadPalette()
    const t = loadTheme()
    const dark = t === 'system' ? getSystemDark() : t === 'dark'
    applyPalette(p, dark)
    return p
  })

  const resolvedDark = theme === 'system' ? getSystemDark() : theme === 'dark'

  useEffect(() => {
    applyPalette(palette, resolvedDark)
  }, [palette, resolvedDark])

  useEffect(() => {
    if (theme !== 'system') return
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => applyTheme('system')
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [theme])

  function cycleTheme() {
    const next: ThemeMode =
      theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light'
    setTheme(next)
    applyTheme(next)
    localStorage.setItem(THEME_KEY, next)
  }

  function setCurrentPalette(p: ThemePalette) {
    setPalette(p)
    localStorage.setItem(PALETTE_KEY, p)
    const dark = theme === 'system' ? getSystemDark() : theme === 'dark'
    applyPalette(p, dark)
  }

  return (
    <div className="app-shell">
      <Sidebar
        active={screen}
        onNav={setScreen}
        theme={theme}
        onCycleTheme={cycleTheme}
        palette={palette}
        onSetPalette={setCurrentPalette}
      />
      <main className="main-content">
        {screen === 'converter' && <Converter />}
        {screen === 'manual'    && <Manual palette={palette} dark={resolvedDark} />}
      </main>
    </div>
  )
}
