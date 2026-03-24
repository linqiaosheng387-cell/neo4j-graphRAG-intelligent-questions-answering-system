import { ref, watch } from 'vue'

type Theme = 'light' | 'dark'

const theme = ref<Theme>('light')

export const useTheme = () => {
  const initTheme = () => {
    const stored = localStorage.getItem('theme') as Theme | null
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches

    theme.value = stored || (prefersDark ? 'dark' : 'light')
    applyTheme(theme.value)
  }

  const applyTheme = (t: Theme) => {
    document.documentElement.setAttribute('data-theme', t)
    localStorage.setItem('theme', t)
  }

  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    applyTheme(theme.value)
  }

  watch(theme, (newTheme) => {
    applyTheme(newTheme)
  })

  return {
    theme,
    initTheme,
    toggleTheme
  }
}
