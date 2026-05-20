// Manual TS types for event payloads (not in Wails-generated models).

export interface ProcessProgress {
  row: number
  total: number
  column: string
  flagged: number
}

export interface ProcessResult {
  rowsProcessed: number
  flaggedRows: number
  outputPath: string
  columns: string[]
}

// Mode constants matching Go iota: 0=Single, 1=AE, 2=DC
export const MODE_SINGLE = 0
export const MODE_AE     = 1
export const MODE_DC     = 2

export interface ModeInfo {
  id: number
  label: string
  subtitle: string
  example: string
  description: string
}

export const MODES: ModeInfo[] = [
  {
    id: MODE_SINGLE,
    label: 'Single Date',
    subtitle: 'MM/DD/YYYY',
    example: '05/08/1962',
    description: 'Resolves each row to a single date. Ranges collapse to start date. Vague values flagged.',
  },
  {
    id: MODE_AE,
    label: 'ArchivEra',
    subtitle: 'MM/DD/YYYY – MM/DD/YYYY',
    example: '01/01/1962 – 12/31/1962',
    description: 'Outputs date ranges. Years expand to full spans. Fuzzy values preserved and flagged.',
  },
  {
    id: MODE_DC,
    label: 'Dublin Core',
    subtitle: 'ISO / DC formats',
    example: '06/05/1962 – 08/12/1965',
    description: 'Accepts ISO 8601 and Dublin Core partial formats in addition to all ArchivEra inputs.',
  },
]
