/**
 * MusicEngine API service.
 * - Enrichment calls go to MusicEngine.ai API (which uses workers)
 * - Add calls go to Baserow backend API (which inserts rows)
 * - Slots calls use Baserow JWT token for authentication
 */

/**
 * Create MusicEngine service
 * @param {Object} client - Baserow API client
 * @param {string} accessToken - Optional Baserow JWT access token for authenticated requests
 * @param {string} apiBaseUrl - Optional API base URL (from runtime config)
 */
export default (client, accessToken = null, apiBaseUrl = '') => {
  // Use provided URL, fall back to build-time env, then production URL
  const ISRC_ANALYTICS_API_BASE = apiBaseUrl || process.env.ISRC_ANALYTICS_API_URL || 'https://musicengine.ai'
  const SLOT_AUTH_REQUIRED_ERROR_CODE = 'SLOT_AUTH_REQUIRED'

  const buildAuthHeaders = (token = accessToken) => {
    const headers = { Accept: 'application/json' }
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
    return headers
  }

  const requestSlots = async (endpoint, label) => {
    const doRequest = async (token) => {
      return await fetch(`${ISRC_ANALYTICS_API_BASE}${endpoint}`, {
        method: 'GET',
        headers: buildAuthHeaders(token),
        credentials: 'include',
      })
    }

    const buildSlotAuthRequiredError = (message = 'Authentication required') => {
      const error = new Error(message)
      error.code = SLOT_AUTH_REQUIRED_ERROR_CODE
      return error
    }

    const parseJson = async (response) => {
      return await response.json().catch(() => null)
    }

    let response = await doRequest(accessToken)
    let responseData = await parseJson(response)

    // Retry once using cookie-only auth if bearer token auth is rejected.
    if (
      accessToken &&
      (
        response.status === 401 ||
        response.status === 403 ||
        responseData?.requireAuth === true
      )
    ) {
      response = await doRequest(null)
      responseData = await parseJson(response)
    }

    if (
      responseData?.requireAuth === true ||
      response.status === 401 ||
      response.status === 403
    ) {
      throw buildSlotAuthRequiredError(responseData?.error)
    }

    if (!response.ok) {
      throw new Error(
        responseData?.error || `Failed to fetch ${label}: ${response.status}`
      )
    }

    return { data: responseData }
  }

  return {
    /**
     * Enrich track data from ISRC or Spotify URL.
     * Calls MusicEngine.ai API which handles Spotify data fetching.
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
     * Calls MusicEngine.ai API which fetches all artist tracks.
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
     * Calls MusicEngine.ai API which handles Spotify data fetching.
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
      return await requestSlots('/api/catalogue/slots', 'track slots')
    },

    /**
     * Get playlist slot usage and limits.
     * Uses Baserow JWT token for authentication if provided.
     * @returns {Promise} { used, limit, unlimited, remaining }
     */
    async getPlaylistSlots() {
      return await requestSlots('/api/playlists/slots', 'playlist slots')
    },
  }
}
