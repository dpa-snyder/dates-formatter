import { useEffect, useState } from 'react'
import { Screen, ThemeMode } from '../App'
import { THEMES, ThemePalette } from '../themes'
import { GetAppVersion } from '../../wailsjs/go/main/App'

interface Props {
  active: Screen
  onNav: (s: Screen) => void
  theme: ThemeMode
  onCycleTheme: () => void
  palette: ThemePalette
  onSetPalette: (p: ThemePalette) => void
}

const NAV: { id: Screen; label: string; icon: string }[] = [
  { id: 'converter', label: 'Converter',    icon: '⇄' },
  { id: 'manual',    label: 'User Manual',  icon: '📖' },
]

export default function Sidebar({ active, onNav, theme, onCycleTheme, palette, onSetPalette }: Props) {
  const [version, setVersion] = useState('…')
  useEffect(() => { GetAppVersion().then(setVersion) }, [])

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-eyebrow">Date Formatter</div>
        <div className="sidebar-brand-title">Archival Dates</div>
      </div>

      <nav className="sidebar-nav">
        {NAV.map(item => (
          <button
            key={item.id}
            className={`sidebar-nav-item${active === item.id ? ' active' : ''}`}
            onClick={() => onNav(item.id)}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-footer-label">Appearance</div>
        <div className="theme-toggle">
          {(['light', 'dark', 'system'] as ThemeMode[]).map(t => (
            <button
              key={t}
              className={`theme-btn${theme === t ? ' active' : ''}`}
              onClick={() => {
                if (theme !== t) onCycleTheme()
              }}
            >
              {t === 'light' ? '☀' : t === 'dark' ? '☾' : 'Auto'}
            </button>
          ))}
        </div>
        <div className="sidebar-footer-label" style={{marginTop: '10px'}}>Theme</div>
        <select
          className="theme-select"
          value={palette}
          onChange={e => onSetPalette(e.target.value as ThemePalette)}
        >
          {(Object.keys(THEMES) as ThemePalette[]).map(p => (
            <option key={p} value={p}>{THEMES[p].label}</option>
          ))}
        </select>
        <div className="sidebar-version">{version}</div>
      </div>
    </aside>
  )
}
