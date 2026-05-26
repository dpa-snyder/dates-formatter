export type ThemePalette =
  | 'dpa'
  | 'default'
  | 'tokyonight'
  | 'gruvbox'
  | 'catppuccin'
  | 'nightowl'
  | 'cobalt2'
  | 'onedark'
  | 'dracula'
  | 'nord'
  | 'solarized'

export interface ThemeColors {
  blue: string; blueLt: string; orange: string
  bg: string; bg2: string; panel: string
  ink: string; muted: string; line: string
  okBg: string; okInk: string
  warnBg: string; warnInk: string
  errBg: string; errInk: string
  chipBg: string; chipLine: string
  codeBg: string; codeInk: string
  shadow: string; shadowSm: string
}

export interface ThemeDef {
  label: string
  swatch: string
  light: ThemeColors
  dark: ThemeColors
}

export const THEMES: Record<ThemePalette, ThemeDef> = {
  dpa: {
    label: 'DPA',
    swatch: 'linear-gradient(135deg, #0a1628 50%, #4d9ef5 50%)',
    light: {
      blue: '#1a5fb4', blueLt: '#2d74d0', orange: '#c0600a',
      bg: '#f2f5fc', bg2: '#e3eaf8', panel: '#ffffff',
      ink: '#0d1a2e', muted: '#3e5272', line: '#c8d4ea',
      okBg: '#daf2e4', okInk: '#144f2c',
      warnBg: '#fef3dc', warnInk: '#6e4200',
      errBg: '#fde4e4', errInk: '#7d1a1a',
      chipBg: '#e4ecfb', chipLine: '#bfd0f4',
      codeBg: '#eef2fc', codeInk: '#1a3e7e',
      shadow: '0 6px 22px rgba(10,22,40,0.10)',
      shadowSm: '0 2px 9px rgba(10,22,40,0.07)',
    },
    dark: {
      blue: '#4d9ef5', blueLt: '#78bbff', orange: '#f0a040',
      bg: '#060d1a', bg2: '#0a1628', panel: '#0f1e38',
      ink: '#e8f2ff', muted: '#7aa0cc', line: '#162844',
      okBg: '#082e1c', okInk: '#5dd49a',
      warnBg: '#2a1a00', warnInk: '#f0a040',
      errBg: '#2e0d0d', errInk: '#f07070',
      chipBg: '#102040', chipLine: '#1e3560',
      codeBg: '#081020', codeInk: '#c8e0ff',
      shadow: '0 6px 24px rgba(0,0,0,0.45)',
      shadowSm: '0 2px 9px rgba(0,0,0,0.28)',
    },
  },

  default: {
    label: 'Default',
    swatch: 'linear-gradient(135deg, #121d32 50%, #7cb4ff 50%)',
    light: {
      blue: '#235194', blueLt: '#4077c8', orange: '#d4720f',
      bg: '#f0f4fb', bg2: '#e5eaf6', panel: '#ffffff',
      ink: '#19263e', muted: '#4a5e7a', line: '#d2daea',
      okBg: '#dff3e7', okInk: '#175e35',
      warnBg: '#fff3dc', warnInk: '#7a4500',
      errBg: '#fee2e2', errInk: '#8b1c1c',
      chipBg: '#edf2ff', chipLine: '#c8d7f8',
      codeBg: '#f0f4ff', codeInk: '#1e3a6e',
      shadow: '0 6px 22px rgba(28,45,80,0.09)',
      shadowSm: '0 2px 9px rgba(28,45,80,0.07)',
    },
    dark: {
      blue: '#7cb4ff', blueLt: '#a8d0ff', orange: '#f5b87a',
      bg: '#0c1220', bg2: '#0f1828', panel: '#121d32',
      ink: '#e2ecff', muted: '#8aa3cc', line: '#1e3154',
      okBg: '#0e3322', okInk: '#6fd49e',
      warnBg: '#32220a', warnInk: '#f5b87a',
      errBg: '#3b1414', errInk: '#f87171',
      chipBg: '#152540', chipLine: '#2a4475',
      codeBg: '#0c1828', codeInk: '#d8e8ff',
      shadow: '0 6px 24px rgba(0,0,0,0.36)',
      shadowSm: '0 2px 9px rgba(0,0,0,0.22)',
    },
  },

  tokyonight: {
    label: 'Tokyo Night',
    swatch: 'linear-gradient(135deg, #24283b 50%, #82aaff 50%)',
    light: {
      blue: '#2e7de9', blueLt: '#399fd8', orange: '#b15c00',
      bg: '#e1e2e7', bg2: '#d0d1d6', panel: '#f7f7fb',
      ink: '#1e2a5e', muted: '#4a5898', line: '#c4c8da',
      okBg: '#d7eed9', okInk: '#3a5028',
      warnBg: '#f0e7d3', warnInk: '#7a4e10',
      errBg: '#f8d9d9', errInk: '#7a2428',
      chipBg: '#dde6f8', chipLine: '#b4c8ee',
      codeBg: '#eaebf0', codeInk: '#2e5ab0',
      shadow: '0 6px 22px rgba(30,50,100,0.09)',
      shadowSm: '0 2px 9px rgba(30,50,100,0.07)',
    },
    dark: {
      blue: '#82aaff', blueLt: '#b4befe', orange: '#ff9e64',
      bg: '#1a1b2e', bg2: '#13142a', panel: '#1e2030',
      ink: '#c0caf5', muted: '#8898d0', line: '#2a2f4a',
      okBg: '#182a20', okInk: '#9ece6a',
      warnBg: '#2a1e0a', warnInk: '#ffc777',
      errBg: '#2a1020', errInk: '#ff757f',
      chipBg: '#23284a', chipLine: '#3a4070',
      codeBg: '#13142a', codeInk: '#c099ff',
      shadow: '0 6px 24px rgba(0,8,30,0.6)',
      shadowSm: '0 2px 9px rgba(0,8,30,0.4)',
    },
  },

  gruvbox: {
    label: 'Gruvbox',
    swatch: 'linear-gradient(135deg, #282828 50%, #fe8019 50%)',
    light: {
      blue: '#458588', blueLt: '#689d6a', orange: '#d65d0e',
      bg: '#fbf1c7', bg2: '#f2e5bc', panel: '#fffade',
      ink: '#1d1c1a', muted: '#5e5648', line: '#d5c4a1',
      okBg: '#e4ecce', okInk: '#3a6a48',
      warnBg: '#f4eccc', warnInk: '#9a6010',
      errBg: '#f4d9cc', errInk: '#8a1606',
      chipBg: '#e5d9ab', chipLine: '#ccc098',
      codeBg: '#f2e5bc', codeInk: '#076678',
      shadow: '0 6px 22px rgba(60,56,54,0.10)',
      shadowSm: '0 2px 9px rgba(60,56,54,0.07)',
    },
    dark: {
      blue: '#83a598', blueLt: '#8ec07c', orange: '#fe8019',
      bg: '#282828', bg2: '#1d2021', panel: '#3c3836',
      ink: '#ebdbb2', muted: '#c4b8a4', line: '#504945',
      okBg: '#1e2b1e', okInk: '#b8bb26',
      warnBg: '#2b2118', warnInk: '#fabd2f',
      errBg: '#291e1e', errInk: '#fb4934',
      chipBg: '#3a3733', chipLine: '#504940',
      codeBg: '#1d2021', codeInk: '#ebdbb2',
      shadow: '0 6px 24px rgba(0,0,0,0.4)',
      shadowSm: '0 2px 9px rgba(0,0,0,0.25)',
    },
  },

  catppuccin: {
    label: 'Catppuccin',
    swatch: 'linear-gradient(135deg, #1e1e2e 50%, #89b4fa 50%)',
    light: {
      blue: '#1e66f5', blueLt: '#209fb5', orange: '#fe640b',
      bg: '#eff1f5', bg2: '#e6e9ef', panel: '#ffffff',
      ink: '#1e2030', muted: '#525572', line: '#bcc0cc',
      okBg: '#d8f5e4', okInk: '#2e8020',
      warnBg: '#fef5d4', warnInk: '#b07010',
      errBg: '#fde8e9', errInk: '#a80028',
      chipBg: '#dde3f7', chipLine: '#c0caec',
      codeBg: '#e6e9ef', codeInk: '#1e66f5',
      shadow: '0 6px 22px rgba(76,79,105,0.09)',
      shadowSm: '0 2px 9px rgba(76,79,105,0.06)',
    },
    dark: {
      blue: '#89b4fa', blueLt: '#b4befe', orange: '#fab387',
      bg: '#1e1e2e', bg2: '#181825', panel: '#313244',
      ink: '#cdd6f4', muted: '#9096b0', line: '#45475a',
      okBg: '#1b2b22', okInk: '#a6e3a1',
      warnBg: '#2b2118', warnInk: '#f9e2af',
      errBg: '#2a1524', errInk: '#f38ba8',
      chipBg: '#2a2c3e', chipLine: '#3d3f54',
      codeBg: '#181825', codeInk: '#cdd6f4',
      shadow: '0 6px 24px rgba(0,0,0,0.4)',
      shadowSm: '0 2px 9px rgba(0,0,0,0.25)',
    },
  },

  nightowl: {
    label: 'Night Owl',
    swatch: 'linear-gradient(135deg, #011627 50%, #7fdbca 50%)',
    light: {
      blue: '#4876d6', blueLt: '#2f68c8', orange: '#d57e1e',
      bg: '#fbfbfb', bg2: '#f2f2f2', panel: '#ffffff',
      ink: '#1e1e2e', muted: '#4e5868', line: '#d9d9e3',
      okBg: '#e3f4e8', okInk: '#165025',
      warnBg: '#fef3e2', warnInk: '#7a4800',
      errBg: '#fde8ec', errInk: '#720e22',
      chipBg: '#e5eaf8', chipLine: '#c8d3ed',
      codeBg: '#f0f0f7', codeInk: '#4876d6',
      shadow: '0 6px 22px rgba(1,22,39,0.08)',
      shadowSm: '0 2px 9px rgba(1,22,39,0.05)',
    },
    dark: {
      blue: '#7fdbca', blueLt: '#addb67', orange: '#f78c6c',
      bg: '#011627', bg2: '#0d2137', panel: '#0d2137',
      ink: '#d6deeb', muted: '#8a9eb0', line: '#1d3b53',
      okBg: '#0a2e1e', okInk: '#addb67',
      warnBg: '#241900', warnInk: '#ecc48d',
      errBg: '#270d11', errInk: '#ef5350',
      chipBg: '#0f2a3f', chipLine: '#1d3d57',
      codeBg: '#0d2137', codeInk: '#d6deeb',
      shadow: '0 6px 24px rgba(0,0,0,0.45)',
      shadowSm: '0 2px 9px rgba(0,0,0,0.28)',
    },
  },

  cobalt2: {
    label: 'Cobalt2',
    swatch: 'linear-gradient(135deg, #193549 50%, #ffc600 50%)',
    light: {
      blue: '#0e5a8a', blueLt: '#1270a8', orange: '#d97706',
      bg: '#e8f1f8', bg2: '#dce8f0', panel: '#f5f9fc',
      ink: '#0a1f30', muted: '#3e5e70', line: '#b8ceda',
      okBg: '#d8f0e4', okInk: '#145020',
      warnBg: '#fef0d2', warnInk: '#7a4800',
      errBg: '#fde0df', errInk: '#7a1414',
      chipBg: '#d4e5f2', chipLine: '#b4d0e5',
      codeBg: '#dce8f0', codeInk: '#0e5a8a',
      shadow: '0 6px 22px rgba(25,53,73,0.10)',
      shadowSm: '0 2px 9px rgba(25,53,73,0.07)',
    },
    dark: {
      blue: '#ffc600', blueLt: '#ffdb4d', orange: '#ff9d00',
      bg: '#193549', bg2: '#122738', panel: '#1a2e44',
      ink: '#ffffff', muted: '#a8c0cc', line: '#1f4662',
      okBg: '#0d2e1c', okInk: '#80fcff',
      warnBg: '#2b1a00', warnInk: '#ffc600',
      errBg: '#2e0f0f', errInk: '#ff5152',
      chipBg: '#1e3d56', chipLine: '#25506e',
      codeBg: '#122738', codeInk: '#80fcff',
      shadow: '0 6px 24px rgba(0,0,0,0.4)',
      shadowSm: '0 2px 9px rgba(0,0,0,0.25)',
    },
  },

  onedark: {
    label: 'One Dark',
    swatch: 'linear-gradient(135deg, #282c34 50%, #61afef 50%)',
    light: {
      blue: '#4078f2', blueLt: '#0184bc', orange: '#986801',
      bg: '#fafafa', bg2: '#f0f0f0', panel: '#ffffff',
      ink: '#1a1c22', muted: '#5e6370', line: '#d3d3d3',
      okBg: '#eef5eb', okInk: '#3a7e38',
      warnBg: '#fdf6e3', warnInk: '#7a5200',
      errBg: '#fef0f0', errInk: '#a80e30',
      chipBg: '#e5ecfc', chipLine: '#c8d5f8',
      codeBg: '#f0f0f0', codeInk: '#4078f2',
      shadow: '0 6px 22px rgba(0,0,0,0.08)',
      shadowSm: '0 2px 9px rgba(0,0,0,0.05)',
    },
    dark: {
      blue: '#61afef', blueLt: '#56b6c2', orange: '#d19a66',
      bg: '#282c34', bg2: '#21252b', panel: '#2c313c',
      ink: '#abb2bf', muted: '#828a96', line: '#3e4452',
      okBg: '#1e2e22', okInk: '#98c379',
      warnBg: '#2e2519', warnInk: '#e5c07b',
      errBg: '#2e1c1c', errInk: '#e06c75',
      chipBg: '#2f3747', chipLine: '#3d4860',
      codeBg: '#21252b', codeInk: '#abb2bf',
      shadow: '0 6px 24px rgba(0,0,0,0.4)',
      shadowSm: '0 2px 9px rgba(0,0,0,0.25)',
    },
  },

  dracula: {
    label: 'Dracula',
    swatch: 'linear-gradient(135deg, #282a36 50%, #bd93f9 50%)',
    light: {
      blue: '#5060a0', blueLt: '#6878b8', orange: '#cc5c00',
      bg: '#f8f8f2', bg2: '#eeeeec', panel: '#ffffff',
      ink: '#1a1c28', muted: '#4a5488', line: '#d5d5d0',
      okBg: '#e8f5e8', okInk: '#205020',
      warnBg: '#fff8e0', warnInk: '#6a4c00',
      errBg: '#fde8e8', errInk: '#7a1414',
      chipBg: '#ece9f8', chipLine: '#d4cfed',
      codeBg: '#eeeeec', codeInk: '#282a36',
      shadow: '0 6px 22px rgba(40,42,54,0.08)',
      shadowSm: '0 2px 9px rgba(40,42,54,0.05)',
    },
    dark: {
      blue: '#bd93f9', blueLt: '#cfa9fb', orange: '#ffb86c',
      bg: '#282a36', bg2: '#21222c', panel: '#1e1f29',
      ink: '#f8f8f2', muted: '#9098c0', line: '#44475a',
      okBg: '#1b2e1e', okInk: '#50fa7b',
      warnBg: '#2d2410', warnInk: '#f1fa8c',
      errBg: '#2e1c1c', errInk: '#ff5555',
      chipBg: '#353449', chipLine: '#464560',
      codeBg: '#21222c', codeInk: '#f8f8f2',
      shadow: '0 6px 24px rgba(0,0,0,0.4)',
      shadowSm: '0 2px 9px rgba(0,0,0,0.25)',
    },
  },

  nord: {
    label: 'Nord',
    swatch: 'linear-gradient(135deg, #2e3440 50%, #88c0d0 50%)',
    light: {
      blue: '#5e81ac', blueLt: '#81a1c1', orange: '#d08770',
      bg: '#eceff4', bg2: '#e5e9f0', panel: '#ffffff',
      ink: '#1e2530', muted: '#3e4c5e', line: '#d8dee9',
      okBg: '#daecd8', okInk: '#3a5838',
      warnBg: '#f0ead2', warnInk: '#6a4820',
      errBg: '#f0d9da', errInk: '#6a2428',
      chipBg: '#dae0eb', chipLine: '#c5cedc',
      codeBg: '#e5e9f0', codeInk: '#5e81ac',
      shadow: '0 6px 22px rgba(46,52,64,0.08)',
      shadowSm: '0 2px 9px rgba(46,52,64,0.05)',
    },
    dark: {
      blue: '#88c0d0', blueLt: '#8fbcbb', orange: '#d08770',
      bg: '#2e3440', bg2: '#292e39', panel: '#3b4252',
      ink: '#eceff4', muted: '#b0baca', line: '#434c5e',
      okBg: '#253430', okInk: '#a3be8c',
      warnBg: '#2e2c20', warnInk: '#ebcb8b',
      errBg: '#2d2022', errInk: '#bf616a',
      chipBg: '#3e4a5a', chipLine: '#4d5a6a',
      codeBg: '#292e39', codeInk: '#d8dee9',
      shadow: '0 6px 24px rgba(0,0,0,0.35)',
      shadowSm: '0 2px 9px rgba(0,0,0,0.22)',
    },
  },

  solarized: {
    label: 'Solarized',
    swatch: 'linear-gradient(135deg, #002b36 50%, #268bd2 50%)',
    light: {
      blue: '#268bd2', blueLt: '#2aa198', orange: '#cb4b16',
      bg: '#fdf6e3', bg2: '#eee8d5', panel: '#fffef8',
      ink: '#243640', muted: '#4e6068', line: '#d3cbb8',
      okBg: '#eef3d4', okInk: '#3e6000',
      warnBg: '#fdf3d1', warnInk: '#704e00',
      errBg: '#fce8e0', errInk: '#880000',
      chipBg: '#e8e2ce', chipLine: '#d5cfbb',
      codeBg: '#eee8d5', codeInk: '#268bd2',
      shadow: '0 6px 22px rgba(101,123,131,0.10)',
      shadowSm: '0 2px 9px rgba(101,123,131,0.07)',
    },
    dark: {
      blue: '#268bd2', blueLt: '#2aa198', orange: '#cb4b16',
      bg: '#002b36', bg2: '#073642', panel: '#07333f',
      ink: '#eee8d5', muted: '#93a8b0', line: '#094555',
      okBg: '#002f24', okInk: '#859900',
      warnBg: '#1a1600', warnInk: '#b58900',
      errBg: '#1e0606', errInk: '#dc322f',
      chipBg: '#0a3f4d', chipLine: '#0d526a',
      codeBg: '#00212b', codeInk: '#b0c4cc',
      shadow: '0 6px 24px rgba(0,0,0,0.4)',
      shadowSm: '0 2px 9px rgba(0,0,0,0.25)',
    },
  },
}

export function getAppVars(t: ThemeColors): Record<string, string> {
  return {
    '--blue': t.blue, '--blue-lt': t.blueLt, '--orange': t.orange,
    '--bg': t.bg, '--bg2': t.bg2, '--panel': t.panel,
    '--ink': t.ink, '--muted': t.muted, '--line': t.line,
    '--shadow': t.shadow, '--shadow-sm': t.shadowSm,
    '--ok-bg': t.okBg, '--ok-ink': t.okInk,
    '--warn-bg': t.warnBg, '--warn-ink': t.warnInk,
    '--err-bg': t.errBg, '--err-ink': t.errInk,
    '--chip-bg': t.chipBg, '--chip-line': t.chipLine,
    '--code-bg': t.codeBg, '--code-ink': t.codeInk,
  }
}

export function getManualVars(t: ThemeColors): Record<string, string> {
  return {
    '--bg': t.bg, '--panel': t.panel, '--panel-border': t.line,
    '--text': t.ink, '--muted': t.muted, '--accent': t.blue,
    '--accent-soft': hexAlpha(t.blue, 0.09), '--shadow': t.shadow,
    '--nav-bg': t.panel, '--flag': t.orange,
    '--flag-bg': hexAlpha(t.orange, 0.10), '--alert': t.orange,
    '--alert-soft': hexAlpha(t.orange, 0.08), '--alert-border': hexAlpha(t.orange, 0.22),
  }
}

function hexAlpha(hex: string, a: number): string {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r},${g},${b},${a})`
}
