/**
 * ISRC Analytics API service.
 * - Enrichment calls go to ISRCAnalytics.com API (which uses workers)
 * - Add calls go to Baserow backend API (which inserts rows)
 * - Slots calls use Baserow JWT token for authentication
 */

/**
 * Create ISRC Analytics service
 * @param {Object} client - Baserow API client
 * @param {string} accessToken - Optional Baserow JWT access token for authenticated requests
 * @param {string} apiBaseUrl - Optional API base URL (from runtime config)
 */
export default (client, accessToken = null, apiBaseUrl = '') => {
  // Use provided URL, fall back to build-time env, then empty string
  const ISRC_ANALYTICS_API_BASE = apiBaseUrl || process.env.ISRC_ANALYTICS_API_URL || ''
  return {
    /**
     * Enrich track data from ISRC or Spotify URL.
     * Calls ISRCAnalytics.com API which handles Spotify data fetching.
     * @param {string} input - ISRC code or Spotify track URL
     * @returns {Promise} Enriched track data
     */
    async enrichTrack(input) {
      const response = await fetch(`${ISRC_ANALYTICS_API_BASE}/api/catalogue/enrich`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ input }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to enrich track: ${response.status}`)
      }

      return { data: await response.json() }
    },

    /**
     * Add an enriched track to the user's Baserow catalogue table.
     * @param {Object} trackData - Enriched track data from enrichTrack
     * @returns {Promise} Result with track_id and row_id
     */
    addTrack(trackData) {
      return client.post('/isrc/catalogue/add/', trackData)
    },

    /**
     * Enrich artist data from Spotify artist URL.
     * Calls ISRCAnalytics.com API which fetches all artist tracks.
     * @param {string} input - Spotify artist URL or URI
     * @returns {Promise} Artist data with all tracks
     */
    async enrichArtist(input) {
      const response = await fetch(`${ISRC_ANALYTICS_API_BASE}/api/catalogue/enrich-artist`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ input }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to enrich artist: ${response.status}`)
      }

      return { data: await response.json() }
    },

    /**
     * Enrich playlist data from Spotify URL.
     * Calls ISRCAnalytics.com API which handles Spotify data fetching.
     * @param {string} input - Spotify playlist URL
     * @returns {Promise} Enriched playlist data
     */
    async enrichPlaylist(input) {
      const response = await fetch(`${ISRC_ANALYTICS_API_BASE}/api/playlists/enrich`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ input }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to enrich playlist: ${response.status}`)
      }

      return { data: await response.json() }
    },

    /**
     * Add an enriched playlist to the user's Baserow playlists table.
     * @param {Object} playlistData - Enriched playlist data from enrichPlaylist
     * @returns {Promise} Result with playlist_id and row_id
     */
    addPlaylist(playlistData) {
      return client.post('/isrc/playlists/add/', playlistData)
    },

    /**
     * Get track (ISRC) slot usage and limits.
     * Uses Baserow JWT token for authentication if provided.
     * @returns {Promise} { used, limit, remaining }
     */
    async getTrackSlots() {
      const headers = {}
      if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`
      }

      const response = await fetch(`${ISRC_ANALYTICS_API_BASE}/api/catalogue/slots`, {
        method: 'GET',
        headers,
        credentials: accessToken ? 'omit' : 'include',
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to fetch track slots: ${response.status}`)
      }

      return { data: await response.json() }
    },

    /**
     * Get playlist slot usage and limits.
     * Uses Baserow JWT token for authentication if provided.
     * @returns {Promise} { used, limit, unlimited, remaining }
     */
    async getPlaylistSlots() {
      const headers = {}
      if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`
      }

      const response = await fetch(`${ISRC_ANALYTICS_API_BASE}/api/playlists/slots`, {
        method: 'GET',
        headers,
        credentials: accessToken ? 'omit' : 'include',
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to fetch playlist slots: ${response.status}`)
      }

      return { data: await response.json() }
    },
  }
}
