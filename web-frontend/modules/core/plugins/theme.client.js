/**
 * MusicEngine Theme Plugin
 * Initializes theme from localStorage immediately on client load to prevent FOUC
 * (Flash Of Unstyled Content)
 */

const THEME_STORAGE_KEY = 'isrc-theme'

export default function () {
  // Only run on client side
  if (process.client) {
    initializeTheme()

    // Listen for storage changes (in case user has multiple tabs open)
    window.addEventListener('storage', (event) => {
      if (event.key === THEME_STORAGE_KEY) {
        applyTheme(event.newValue || 'light')
      }
    })
  }
}

function initializeTheme() {
  // Priority: URL param > localStorage > default 'light'
  // URL param allows parent frame (MusicEngine) to set theme for embedded iframe
  const urlParams = new URLSearchParams(window.location.search)
  const urlTheme = urlParams.get('theme')

  if (urlTheme && (urlTheme === 'light' || urlTheme === 'dark')) {
    // Save URL theme to localStorage for persistence
    localStorage.setItem(THEME_STORAGE_KEY, urlTheme)
    applyTheme(urlTheme)
  } else {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY) || 'light'
    applyTheme(savedTheme)
  }
}

function applyTheme(theme) {
  // Apply to both html and body for consistency
  document.documentElement.classList.remove('theme-light', 'theme-dark')
  document.documentElement.classList.add(`theme-${theme}`)
  document.body.classList.remove('theme-light', 'theme-dark')
  document.body.classList.add(`theme-${theme}`)
}