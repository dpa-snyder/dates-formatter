import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import Converter from './screens/Converter'
import Manual from './screens/Manual'
import { THEMES, ThemePalette, getAppVars } from './themes'
import { WindowSetSize } from '../wailsjs/runtime/runtime'
import { CheckForUpdate, GetSettings, RestartToApplyUpdate, SaveSettings } from '../wailsjs/go/main/App'
import { main } from '../wailsjs/go/models'

export type Screen = 'converter' | 'manual'
export type ThemeMode = 'light' | 'dark' | 'system'
export type { ThemePalette }

const THEME_KEY = 'df-theme'
const PALETTE_KEY = 'df-palette'
const CONVERTER_SIZE = { width: 1020, height: 770 }
const MANUAL_SIZE = { width: 1420, height: 770 }

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
  root.setAttribute('data-palette', palette)
}

function loadPalette(): ThemePalette {
  const saved = localStorage.getItem(PALETTE_KEY) as ThemePalette | null
  return saved ?? 'default'
}

export default function App() {
  const [screen, setScreen] = useState<Screen>('converter')
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [updateReady, setUpdateReady] = useState<main.UpdateCheckResult | null>(null)
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
    if (!(window as any).runtime?.WindowSetSize) return
    const size = screen === 'manual' ? MANUAL_SIZE : CONVERTER_SIZE
    WindowSetSize(size.width, size.height)
  }, [screen])

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

  function setCurrentTheme(next: ThemeMode) {
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

  useEffect(() => {
    function dispatchConverterShortcut(name: 'browse' | 'run') {
      const fire = () => window.dispatchEvent(new CustomEvent(`df:shortcut:${name}`))
      if (screen !== 'converter') {
        setScreen('converter')
        window.setTimeout(fire, 80)
      } else {
        fire()
      }
    }

    function onKeyDown(e: KeyboardEvent) {
      if (settingsOpen) return
      const mod = e.metaKey || e.ctrlKey
      if (!mod || e.altKey) return

      const key = e.key.toLowerCase()
      if (key === 'o') {
        e.preventDefault()
        dispatchConverterShortcut('browse')
      } else if (key === 'r') {
        e.preventDefault()
        dispatchConverterShortcut('run')
      } else if (key === '/') {
        e.preventDefault()
        setScreen('manual')
      } else if (key === ',') {
        e.preventDefault()
        setSettingsOpen(true)
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [screen, settingsOpen])

  useEffect(() => {
    if (!settingsOpen) return
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') setSettingsOpen(false)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [settingsOpen])

  useEffect(() => {
    if (!(window as any).go?.main?.App?.CheckForUpdate) return
    Promise.resolve()
      .then(CheckForUpdate)
      .then(result => {
        if (result?.updateAvailable) setUpdateReady(result)
      })
      .catch(() => {})
  }, [])

  async function restartForUpdate() {
    await RestartToApplyUpdate()
  }

  return (
    <div className="app-shell">
      <Sidebar
        active={screen}
        onNav={setScreen}
        theme={theme}
        onSetTheme={setCurrentTheme}
        palette={palette}
        onSetPalette={setCurrentPalette}
        onOpenSettings={() => setSettingsOpen(true)}
      />
      <main className="main-content">
        {screen === 'converter' && <Converter />}
        {screen === 'manual'    && <Manual palette={palette} dark={resolvedDark} />}
      </main>
      {settingsOpen && (
        <SettingsDialog
          theme={theme}
          palette={palette}
          onSetTheme={setCurrentTheme}
          onSetPalette={setCurrentPalette}
          onClose={() => setSettingsOpen(false)}
        />
      )}
      {updateReady && (
        <UpdateRestartDialog
          update={updateReady}
          onRestart={restartForUpdate}
          onDismiss={() => setUpdateReady(null)}
        />
      )}
    </div>
  )
}

interface SettingsDialogProps {
  theme: ThemeMode
  palette: ThemePalette
  onSetTheme: (t: ThemeMode) => void
  onSetPalette: (p: ThemePalette) => void
  onClose: () => void
}

function SettingsDialog({ theme, palette, onSetTheme, onSetPalette, onClose }: SettingsDialogProps) {
  const [settings, setSettings] = useState<main.Settings | null>(null)
  const [updateFolder, setUpdateFolder] = useState('')
  const [updateStatus, setUpdateStatus] = useState('')
  const [updateReady, setUpdateReady] = useState<main.UpdateCheckResult | null>(null)

  useEffect(() => {
    Promise.resolve()
      .then(GetSettings)
      .then(s => {
        const next = new main.Settings(s)
        setSettings(next)
        setUpdateFolder(next.updateFolder ?? '')
      })
      .catch(() => {})
  }, [])

  async function saveUpdateFolder() {
    const base = settings ?? new main.Settings(await GetSettings())
    const next = new main.Settings({
      ...base,
      updateFolder: updateFolder.trim(),
    })
    await SaveSettings(next)
    setSettings(next)
    return next
  }

  async function saveAndClose() {
    await saveUpdateFolder()
    onClose()
  }

  async function checkNow() {
    setUpdateStatus('Checking...')
    setUpdateReady(null)
    try {
      await saveUpdateFolder()
      const result = await CheckForUpdate()
      if (result.updateAvailable) {
        setUpdateReady(result)
        setUpdateStatus(`Version ${result.availableVersion} is ready. Restart to apply.`)
      } else {
        setUpdateStatus(result.message || 'No newer update found.')
      }
    } catch (err) {
      setUpdateStatus(String(err))
    }
  }

  return (
    <div className="settings-backdrop" role="presentation" onClick={onClose}>
      <section
        className="settings-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-title"
        onClick={e => e.stopPropagation()}
      >
        <div className="settings-head">
          <h2 id="settings-title">Settings</h2>
          <button className="settings-close" type="button" onClick={onClose} aria-label="Close settings">×</button>
        </div>
        <div className="settings-section">
          <div className="settings-label">Appearance</div>
          <div className="theme-toggle settings-theme-toggle">
            {(['light', 'dark', 'system'] as ThemeMode[]).map(t => (
              <button
                key={t}
                type="button"
                className={`theme-btn${theme === t ? ' active' : ''}`}
                onClick={() => onSetTheme(t)}
              >
                {t === 'light' ? '☀' : t === 'dark' ? '☾' : 'Auto'}
              </button>
            ))}
          </div>
        </div>
        <div className="settings-section">
          <label className="settings-label" htmlFor="settings-palette">Theme</label>
          <select
            id="settings-palette"
            className="theme-select settings-select"
            value={palette}
            onChange={e => onSetPalette(e.target.value as ThemePalette)}
          >
            {(Object.keys(THEMES) as ThemePalette[]).map(p => (
              <option key={p} value={p}>{THEMES[p].label}</option>
            ))}
          </select>
        </div>
        <div className="settings-section">
          <label className="settings-label" htmlFor="settings-update-folder">Update Folder</label>
          <input
            id="settings-update-folder"
            className="settings-input"
            value={updateFolder}
            onChange={e => setUpdateFolder(e.target.value)}
            placeholder="\\\\server\\share\\Date Formatter"
          />
          <div className="settings-help">Folder containing date-formatter.exe.</div>
          <div className="settings-inline-actions">
            <button type="button" className="btn-ghost-sm" onClick={checkNow}>Check</button>
            {updateReady && (
              <button type="button" className="btn-primary-sm" onClick={() => RestartToApplyUpdate()}>
                Restart
              </button>
            )}
          </div>
          {updateStatus && <div className="settings-status">{updateStatus}</div>}
        </div>
        <div className="settings-actions">
          <button type="button" className="btn-primary-sm" onClick={saveAndClose}>Done</button>
        </div>
      </section>
    </div>
  )
}

interface UpdateRestartDialogProps {
  update: main.UpdateCheckResult
  onRestart: () => void
  onDismiss: () => void
}

function UpdateRestartDialog({ update, onRestart, onDismiss }: UpdateRestartDialogProps) {
  return (
    <div className="settings-backdrop" role="presentation" onClick={onDismiss}>
      <section
        className="settings-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="update-title"
        onClick={e => e.stopPropagation()}
      >
        <div className="settings-head">
          <h2 id="update-title">Update Ready</h2>
          <button className="settings-close" type="button" onClick={onDismiss} aria-label="Dismiss update">×</button>
        </div>
        <div className="settings-section">
          <div className="settings-status">
            Version {update.availableVersion} is ready. Restart Date Formatter to finish updating.
          </div>
        </div>
        <div className="settings-actions">
          <button type="button" className="btn-ghost-sm" onClick={onDismiss}>Later</button>
          <button type="button" className="btn-primary-sm" onClick={onRestart}>Restart</button>
        </div>
      </section>
    </div>
  )
}
