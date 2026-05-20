import { useCallback, useEffect, useRef, useState } from 'react'
import { main } from '../../wailsjs/go/models'
import {
  CancelProcess,
  GetColumns,
  GetSettings,
  OpenPath,
  PickFile,
  StartProcess,
} from '../../wailsjs/go/main/App'
import { EventsOn } from '../../wailsjs/runtime/runtime'
import { MODES, MODE_AE, ProcessProgress, ProcessResult } from '../types'

// ── Stage type ────────────────────────────────────────────────────────────────

type Stage = 'idle' | 'file_loaded' | 'running' | 'done' | 'error'

// ── Converter ─────────────────────────────────────────────────────────────────

export default function Converter() {
  // Core state
  const [mode, setMode] = useState<number>(MODE_AE)
  const [filePath, setFilePath] = useState<string>('')
  const [columnsInfo, setColumnsInfo] = useState<main.ColumnsResult | null>(null)
  const [selectedCols, setSelectedCols] = useState<string[]>([])
  const [outputMode, setOutputMode] = useState<'overwrite' | 'copy'>('overwrite')
  const [colFilter, setColFilter] = useState<string>('')

  // Processing state
  const [stage, setStage] = useState<Stage>('idle')
  const [progress, setProgress] = useState<ProcessProgress | null>(null)
  const [log, setLog] = useState<string[]>([])
  const [result, setResult] = useState<ProcessResult | null>(null)
  const [errorMsg, setErrorMsg] = useState<string>('')
  const [recentFiles, setRecentFiles] = useState<string[]>([])
  const logRef = useRef<HTMLDivElement>(null)

  // Load settings on mount
  useEffect(() => {
    GetSettings().then(s => {
      if (s) {
        if (s.lastMode !== undefined) setMode(s.lastMode)
        if (s.lastOutputMode) setOutputMode(s.lastOutputMode as 'overwrite' | 'copy')
        if (s.recentFiles?.length) setRecentFiles(s.recentFiles)
      }
    }).catch(() => {})
  }, [])

  // Wire up process events
  useEffect(() => {
    const offProg = EventsOn('process:progress', (data: ProcessProgress) => {
      setProgress(data)
    })
    const offDone = EventsOn('process:done', (data: ProcessResult) => {
      setResult(data)
      setStage('done')
      setProgress(null)
    })
    const offErr = EventsOn('process:error', (msg: string) => {
      setErrorMsg(msg)
      setStage('error')
    })
    const offLog = EventsOn('process:log', (msg: string) => {
      setLog(prev => [...prev, msg])
    })
    return () => { offProg(); offDone(); offErr(); offLog() }
  }, [])

  // Auto-scroll log
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [log])

  // ── File loading ─────────────────────────────────────────────────────────────

  const loadFile = useCallback(async (path: string) => {
    if (!path) return
    try {
      const info = await GetColumns(path)
      setFilePath(path)
      setColumnsInfo(info)
      // Pre-select auto-detected date columns
      setSelectedCols(info.dateyColumns?.length ? [...info.dateyColumns] : [])
      setStage('file_loaded')
      setResult(null)
      setLog([])
      setProgress(null)
      setErrorMsg('')
    } catch (e: any) {
      setErrorMsg(String(e))
      setStage('error')
    }
  }, [])

  const handleBrowse = async () => {
    const path = await PickFile()
    if (path) loadFile(path)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) {
      // In Wails WebView, file.path is the native OS path
      const path = (file as any).path || ''
      if (path) loadFile(path)
    }
  }

  // ── Column selection ─────────────────────────────────────────────────────────

  const toggleCol = (col: string) => {
    setSelectedCols(prev =>
      prev.includes(col) ? prev.filter(c => c !== col) : [...prev, col]
    )
  }

  const selectAll = () => {
    const visible = filteredCols()
    const allSelected = visible.every(c => selectedCols.includes(c))
    if (allSelected) {
      setSelectedCols(prev => prev.filter(c => !visible.includes(c)))
    } else {
      setSelectedCols(prev => [...new Set([...prev, ...visible])])
    }
  }

  const filteredCols = () => {
    if (!columnsInfo) return []
    const q = colFilter.toLowerCase()
    return columnsInfo.columns.filter(c => !q || c.toLowerCase().includes(q))
  }

  // ── Run ──────────────────────────────────────────────────────────────────────

  const handleRun = async () => {
    if (!filePath || selectedCols.length === 0) return
    setStage('running')
    setLog([])
    setProgress(null)
    setResult(null)
    setErrorMsg('')
    const opts = new main.ProcessOptions({
      filePath,
      columns: selectedCols,
      mode,
      outputMode,
    })
    StartProcess(opts)
  }

  const handleCancel = () => {
    CancelProcess()
    setStage('file_loaded')
    setProgress(null)
    setLog(prev => [...prev, 'Cancelled by user.'])
  }

  const handleReset = () => {
    setStage('idle')
    setFilePath('')
    setColumnsInfo(null)
    setSelectedCols([])
    setResult(null)
    setLog([])
    setProgress(null)
    setErrorMsg('')
  }

  // ── Progress pct ─────────────────────────────────────────────────────────────

  const progressPct = () => {
    if (!progress || progress.total === 0) return 0
    return Math.round((progress.row / progress.total) * 100)
  }

  const pct = progressPct()

  // ── Filename helper ───────────────────────────────────────────────────────────

  const basename = (p: string) => p.split(/[/\\]/).pop() || p
  const previewOut = () => {
    if (!filePath) return ''
    if (outputMode === 'overwrite') return basename(filePath)
    const ext = filePath.includes('.') ? '.' + filePath.split('.').pop() : ''
    const stem = basename(filePath).replace(ext, '')
    return stem + '-formatted' + ext
  }

  // ── Render ────────────────────────────────────────────────────────────────────

  return (
    <div className="screen converter-screen">

      {/* ── Header ── */}
      <div className="screen-title">Date Formatter</div>
      <div className="screen-subtitle">
        Standardize date columns in archival Excel and CSV spreadsheets.
      </div>

      {/* ── Mode selector ── */}
      <section className="cv-section">
        <div className="cv-section-label">1 · Conversion Mode</div>
        <div className="mode-cards">
          {MODES.map(m => (
            <button
              key={m.id}
              className={`mode-card${mode === m.id ? ' active' : ''}`}
              onClick={() => setMode(m.id)}
            >
              <div className="mc-label">{m.label}</div>
              <div className="mc-subtitle">{m.subtitle}</div>
              <div className="mc-example">{m.example}</div>
              <div className="mc-desc">{m.description}</div>
            </button>
          ))}
        </div>
      </section>

      {/* ── File picker ── */}
      <section className="cv-section">
        <div className="cv-section-label">2 · File</div>
        <div
          className={`file-zone${stage === 'idle' ? ' empty' : ''}`}
          onDrop={handleDrop}
          onDragOver={e => e.preventDefault()}
        >
          {filePath ? (
            <div className="file-zone-loaded">
              <div className="fz-name">{basename(filePath)}</div>
              <div className="fz-meta">
                {columnsInfo?.rowCount?.toLocaleString()} rows ·{' '}
                {columnsInfo?.columns?.length} columns
              </div>
              <button className="btn-ghost-sm" onClick={handleBrowse}>Change file</button>
            </div>
          ) : (
            <div className="file-zone-empty">
              <div className="fz-hint">Drop .xlsx or .csv here</div>
              <button className="btn-primary-sm" onClick={handleBrowse}>Browse…</button>
            </div>
          )}
        </div>

        {/* Recent files */}
        {!filePath && recentFiles.length > 0 && (
          <div className="recent-files">
            <div className="recent-label">Recent</div>
            {recentFiles.map(f => (
              <button key={f} className="recent-item" onClick={() => loadFile(f)}>
                {basename(f)}
              </button>
            ))}
          </div>
        )}
      </section>

      {/* ── Column picker ── */}
      {columnsInfo && (
        <section className="cv-section">
          <div className="cv-section-label">3 · Date Columns</div>
          <div className="col-picker">
            <div className="col-picker-toolbar">
              <input
                className="col-filter"
                placeholder="Filter columns…"
                value={colFilter}
                onChange={e => setColFilter(e.target.value)}
              />
              <button className="btn-ghost-sm" onClick={selectAll}>
                {filteredCols().every(c => selectedCols.includes(c))
                  ? 'Deselect all'
                  : 'Select all'}
              </button>
              <span className="col-count">
                {selectedCols.length} selected
              </span>
            </div>
            <div className="col-list">
              {filteredCols().map(col => {
                const datey = columnsInfo.dateyColumns?.includes(col)
                return (
                  <label key={col} className="col-item">
                    <input
                      type="checkbox"
                      checked={selectedCols.includes(col)}
                      onChange={() => toggleCol(col)}
                    />
                    <span className="col-name">{col}</span>
                    {datey && <span className="datey-badge">dates</span>}
                  </label>
                )
              })}
            </div>
          </div>
        </section>
      )}

      {/* ── Output mode + run ── */}
      {columnsInfo && (
        <section className="cv-section run-section">
          <div className="run-row">
            {/* Output mode */}
            <div className="output-toggle">
              <div className="cv-section-label" style={{marginBottom: 8}}>Output</div>
              <div className="seg-ctrl">
                <button
                  className={`seg-btn${outputMode === 'overwrite' ? ' active' : ''}`}
                  onClick={() => setOutputMode('overwrite')}
                >Overwrite</button>
                <button
                  className={`seg-btn${outputMode === 'copy' ? ' active' : ''}`}
                  onClick={() => setOutputMode('copy')}
                >Save copy</button>
              </div>
              <div className="output-preview">→ {previewOut()}</div>
            </div>

            {/* Run / cancel */}
            <div className="run-controls">
              {stage === 'running' ? (
                <button className="btn-cancel" onClick={handleCancel}>Cancel</button>
              ) : (
                <button
                  className="btn-run"
                  disabled={!filePath || selectedCols.length === 0}
                  onClick={handleRun}
                >
                  Run
                </button>
              )}
            </div>
          </div>

          {/* Progress */}
          {stage === 'running' && (
            <div className="progress-panel">
              <div className="prog-bar-track">
                <div className="prog-bar-fill" style={{width: `${pct}%`}} />
              </div>
              <div className="prog-stats">
                <span>{progress?.column}</span>
                <span>{progress?.row?.toLocaleString()} / {progress?.total?.toLocaleString()} rows</span>
                <span>{progress?.flagged} flagged</span>
                <span>{pct}%</span>
              </div>
              <div className="proc-log" ref={logRef}>
                {log.map((line, i) => <div key={i}>{line}</div>)}
              </div>
            </div>
          )}
        </section>
      )}

      {/* ── Result panel ── */}
      {stage === 'done' && result && (
        <section className="cv-section result-panel">
          <div className="result-header">
            <span className="result-check">✓</span>
            <span className="result-title">Done</span>
          </div>
          <div className="result-stats">
            <div className="result-stat">
              <span className="rs-val">{result.rowsProcessed.toLocaleString()}</span>
              <span className="rs-label">Rows processed</span>
            </div>
            <div className="result-stat">
              <span className={`rs-val${result.flaggedRows > 0 ? ' flagged' : ''}`}>
                {result.flaggedRows.toLocaleString()}
              </span>
              <span className="rs-label">Flagged for review</span>
            </div>
            <div className="result-stat">
              <span className="rs-val">{result.columns.length}</span>
              <span className="rs-label">Column(s) converted</span>
            </div>
          </div>
          <div className="result-path">{result.outputPath}</div>
          <div className="result-actions">
            <button className="btn-primary-sm" onClick={() => OpenPath(result.outputPath)}>
              Open file
            </button>
            <button className="btn-ghost-sm"
              onClick={() => OpenPath(result.outputPath.split(/[/\\]/).slice(0, -1).join('/'))}>
              Open folder
            </button>
            <button className="btn-ghost-sm" onClick={handleReset}>New job</button>
          </div>
          <div className="proc-log" style={{marginTop: 12}} ref={logRef}>
            {log.map((line, i) => <div key={i}>{line}</div>)}
          </div>
        </section>
      )}

      {/* ── Error panel ── */}
      {stage === 'error' && (
        <section className="cv-section error-panel">
          <div className="err-title">Error</div>
          <div className="err-msg">{errorMsg}</div>
          <button className="btn-ghost-sm" onClick={() => setStage(filePath ? 'file_loaded' : 'idle')}>
            Dismiss
          </button>
        </section>
      )}

    </div>
  )
}
