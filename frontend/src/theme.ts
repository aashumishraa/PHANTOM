import { extendTheme, type ThemeConfig } from '@chakra-ui/react'

const config: ThemeConfig = {
  initialColorMode: 'dark',
  useSystemColorMode: false,
}

const theme = extendTheme({
  config,
  colors: {
    brand: {
      50: '#e0f7ff',
      100: '#b8efff',
      200: '#82e0ff',
      300: '#40c7f9',
      400: '#22d3ee',
      500: '#0fb2d2',
      600: '#0b8ba1',
      700: '#086c79',
      800: '#06535f',
      900: '#053f4a',
    },
  },
  fonts: {
    heading: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    body: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  },
  styles: {
    global: {
      'html, body, #root': {
        minHeight: '100%',
      },
      body: {
        bg: 'gray.900',
        color: 'whiteAlpha.900',
        lineHeight: 'tall',
      },
      '*': {
        'scrollbarWidth': 'thin',
        'scrollbarColor': '#22d3ee #0f172a',
      },
      '*::-webkit-scrollbar': {
        width: '10px',
        height: '10px',
      },
      '*::-webkit-scrollbar-track': {
        background: '#0f172a',
      },
      '*::-webkit-scrollbar-thumb': {
        background: '#22d3ee',
        borderRadius: '10px',
      },
    },
  },
})

export default theme
