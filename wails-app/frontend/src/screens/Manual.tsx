import { useEffect, useRef } from 'react'
import { ThemePalette, THEMES, getManualVars } from '../themes'

interface Props {
  palette: ThemePalette
  dark: boolean
}

export default function Manual({ palette, dark }: Props) {
  const iframeRef = useRef<HTMLIFrameElement>(null)

  function sendTheme() {
    const vars = getManualVars(THEMES[palette][dark ? 'dark' : 'light'])
    iframeRef.current?.contentWindow?.postMessage(
      { type: 'df-theme', vars, mode: dark ? 'dark' : 'light' },
      '*'
    )
  }

  useEffect(() => { sendTheme() }, [palette, dark])

  return (
    <iframe
      ref={iframeRef}
      className="manual-frame"
      src="/user-manual.html"
      title="Date Formatter User Manual"
      onLoad={sendTheme}
    />
  )
}
