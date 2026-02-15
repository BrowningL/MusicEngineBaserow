/**
 * ISRCAnalytics Iframe Messages Plugin
 * Listens for postMessage events from the parent ISRCAnalytics app
 * and translates them into Vue global events.
 */

export default function ({ app }) {
  if (!process.client) return

  window.addEventListener('message', (event) => {
    // Only handle messages with a known type
    const { type } = event.data || {}
    if (!type) return

    switch (type) {
      case 'open-release-modal':
        app.$root.$emit('open-release-modal')
        break
      case 'open-account-modal':
        app.$root.$emit('open-account-modal')
        break
    }
  })
}
