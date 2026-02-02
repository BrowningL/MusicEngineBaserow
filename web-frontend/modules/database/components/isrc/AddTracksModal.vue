<template>
  <Modal :wide="true">
    <template #content>
      <div class="add-tracks-modal">
        <h2 class="add-tracks-modal__title">Add Tracks</h2>
        <p class="add-tracks-modal__description">
          Add tracks to your catalogue by entering an ISRC code, Spotify URL, or importing from CSV.
        </p>

        <!-- Tab Navigation -->
        <div class="add-tracks-modal__tabs">
          <button
            class="add-tracks-modal__tab"
            :class="{ 'add-tracks-modal__tab--active': activeTab === 'manual' }"
            @click="activeTab = 'manual'"
          >
            <i class="iconoir-music-double-note"></i>
            Manual Entry
          </button>
          <button
            class="add-tracks-modal__tab"
            :class="{ 'add-tracks-modal__tab--active': activeTab === 'csv' }"
            @click="activeTab = 'csv'"
          >
            <i class="iconoir-page"></i>
            CSV Import
          </button>
          <button
            class="add-tracks-modal__tab"
            :class="{ 'add-tracks-modal__tab--active': activeTab === 'artist' }"
            @click="activeTab = 'artist'"
          >
            <i class="iconoir-user"></i>
            By Artist
          </button>
        </div>

        <!-- Manual Entry Tab -->
        <div v-if="activeTab === 'manual'" class="add-tracks-modal__content">
          <div class="add-tracks-modal__form">
            <FormGroup
              :label="'ISRC or Spotify Track URL'"
              small-label
              required
            >
              <FormInput
                v-model="manualInput"
                :placeholder="'e.g., USRC17607839 or https://open.spotify.com/track/...'"
                :disabled="loading"
                @keyup.enter="enrichTrack"
              />
              <p class="add-tracks-modal__hint">
                Enter an ISRC code (12 characters) or a Spotify track URL
              </p>
            </FormGroup>

            <!-- Enriched Data Preview -->
            <div v-if="enrichedTrack" class="add-tracks-modal__preview">
              <div v-if="enrichedTrack.cover_url" class="add-tracks-modal__cover">
                <img :src="enrichedTrack.cover_url" alt="Album cover" />
              </div>
              <div class="add-tracks-modal__track-info">
                <div class="add-tracks-modal__track-title">{{ enrichedTrack.title }}</div>
                <div class="add-tracks-modal__track-artist">{{ enrichedTrack.artist }}</div>
                <div class="add-tracks-modal__track-meta">
                  <span v-if="enrichedTrack.album">{{ enrichedTrack.album }}</span>
                  <span v-if="enrichedTrack.isrc" class="add-tracks-modal__isrc">{{ enrichedTrack.isrc }}</span>
                </div>
              </div>
            </div>

            <!-- Error Message -->
            <div v-if="error" class="add-tracks-modal__error">
              {{ error }}
            </div>

            <!-- Success Message -->
            <div v-if="success" class="add-tracks-modal__success">
              <i class="iconoir-check-circle"></i>
              Track added successfully!
            </div>

            <div class="add-tracks-modal__actions">
              <button
                v-if="!enrichedTrack"
                class="button button--primary"
                :class="{ 'button--loading': loading }"
                :disabled="!manualInput || loading"
                @click="enrichTrack"
              >
                Fetch Track Info
              </button>
              <template v-else>
                <button
                  class="button"
                  :disabled="loading"
                  @click="resetForm"
                >
                  Clear
                </button>
                <button
                  class="button button--primary"
                  :class="{ 'button--loading': loading }"
                  :disabled="loading"
                  @click="addTrack"
                >
                  Add to Catalogue
                </button>
              </template>
            </div>
          </div>
        </div>

        <!-- CSV Import Tab -->
        <div v-if="activeTab === 'csv'" class="add-tracks-modal__content">
          <div class="add-tracks-modal__placeholder">
            <i class="iconoir-upload-square"></i>
            <p>CSV import coming soon</p>
            <p class="add-tracks-modal__hint">
              For now, use the
              <a :href="cataloguePageUrl" target="_blank" class="add-tracks-modal__link">
                full catalogue page
              </a>
              for CSV imports.
            </p>
          </div>
        </div>

        <!-- By Artist Tab -->
        <div v-if="activeTab === 'artist'" class="add-tracks-modal__content">
          <!-- Results Screen -->
          <div v-if="artistShowResults && artistAddResults" class="add-tracks-modal__results">
            <div class="add-tracks-modal__results-box">
              <h3 class="add-tracks-modal__results-title">
                {{ artistAddResults.succeeded > 0 ? 'Tracks Added Successfully' : 'Import Complete' }}
              </h3>
              <div class="add-tracks-modal__results-stats">
                <p>
                  <span class="add-tracks-modal__results-label">Total attempted:</span>
                  {{ artistAddResults.succeeded + artistAddResults.failed }}
                </p>
                <p class="add-tracks-modal__results-success">
                  <span class="add-tracks-modal__results-label">Succeeded:</span>
                  {{ artistAddResults.succeeded }}
                </p>
                <p v-if="artistAddResults.failed > 0" class="add-tracks-modal__results-failed">
                  <span class="add-tracks-modal__results-label">Failed:</span>
                  {{ artistAddResults.failed }}
                </p>
              </div>
              <div v-if="artistAddResults.errors.length > 0" class="add-tracks-modal__results-errors">
                <details>
                  <summary>View errors ({{ artistAddResults.errors.length }})</summary>
                  <ul>
                    <li v-for="(err, idx) in artistAddResults.errors.slice(0, 10)" :key="idx">
                      {{ err }}
                    </li>
                    <li v-if="artistAddResults.errors.length > 10" class="add-tracks-modal__results-more">
                      ...and {{ artistAddResults.errors.length - 10 }} more
                    </li>
                  </ul>
                </details>
              </div>
            </div>
            <div class="add-tracks-modal__results-actions">
              <button class="button" @click="resetArtistForm">
                Add Another Artist
              </button>
              <button
                class="button button--primary"
                @click="artistShowResults = false; artistAddResults = null; $emit('track-added')"
              >
                {{ artistAddResults.succeeded > 0 ? 'Done' : 'Close' }}
              </button>
            </div>
          </div>

          <!-- Input Screen -->
          <div v-else-if="!artistIsReviewing" class="add-tracks-modal__form">
            <FormGroup
              :label="'Spotify Artist URL or URI'"
              small-label
              required
            >
              <FormInput
                v-model="artistInput"
                :placeholder="'e.g., https://open.spotify.com/artist/... or spotify:artist:...'"
                :disabled="artistLoading"
                @keyup.enter="fetchArtistTracks"
              />
              <p class="add-tracks-modal__hint">
                Enter a Spotify artist URL or URI to fetch all their tracks
              </p>
            </FormGroup>

            <div v-if="artistError" class="add-tracks-modal__error">
              {{ artistError }}
            </div>

            <div class="add-tracks-modal__actions">
              <button
                class="button button--primary"
                :class="{ 'button--loading': artistLoading }"
                :disabled="!artistInput || artistLoading"
                @click="fetchArtistTracks"
              >
                {{ artistLoading ? 'Fetching Artist Tracks...' : 'Fetch Artist Tracks' }}
              </button>
            </div>
          </div>

          <!-- Track Selection Screen -->
          <div v-else class="add-tracks-modal__artist-review">
            <div class="add-tracks-modal__artist-header">
              <h3 class="add-tracks-modal__artist-name">
                {{ artistData.name }} - Select Tracks to Add
              </h3>
              <button class="add-tracks-modal__cancel-btn" @click="cancelArtistReview">
                Cancel
              </button>
            </div>

            <!-- Select All Checkbox -->
            <div class="add-tracks-modal__select-all">
              <label class="add-tracks-modal__checkbox-label">
                <input
                  type="checkbox"
                  :checked="allTracksSelected"
                  :indeterminate.prop="someTracksSelected && !allTracksSelected"
                  @change="toggleAllTracks($event.target.checked)"
                />
                <span>Select All ({{ selectedTrackCount }} of {{ trackSelections.length }} selected)</span>
              </label>
            </div>

            <!-- Track List -->
            <div class="add-tracks-modal__track-list">
              <table class="add-tracks-modal__table">
                <thead>
                  <tr>
                    <th class="add-tracks-modal__th-checkbox"></th>
                    <th class="add-tracks-modal__th-cover">Cover</th>
                    <th>Title</th>
                    <th>Artist</th>
                    <th>Album</th>
                    <th>ISRC</th>
                    <th>Release</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(ts, index) in trackSelections"
                    :key="ts.track.isrc || index"
                    class="add-tracks-modal__track-row"
                  >
                    <td>
                      <input
                        type="checkbox"
                        :checked="ts.selected"
                        @change="toggleTrackSelection(index)"
                      />
                    </td>
                    <td>
                      <img
                        v-if="ts.track.cover_url"
                        :src="ts.track.cover_url"
                        alt="Cover"
                        class="add-tracks-modal__table-cover"
                      />
                      <div v-else class="add-tracks-modal__table-cover-placeholder">
                        N/A
                      </div>
                    </td>
                    <td class="add-tracks-modal__track-cell-title">{{ ts.track.title }}</td>
                    <td>{{ ts.track.artist }}</td>
                    <td>{{ ts.track.album || '-' }}</td>
                    <td>
                      <code class="add-tracks-modal__isrc">{{ ts.track.isrc }}</code>
                    </td>
                    <td>{{ ts.track.release_date || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div v-if="artistError" class="add-tracks-modal__error">
              {{ artistError }}
            </div>

            <!-- Progress Bar -->
            <div v-if="artistAddingProgress" class="add-tracks-modal__progress">
              <p>Adding tracks: {{ artistAddingProgress.current }} of {{ artistAddingProgress.total }}</p>
              <div class="add-tracks-modal__progress-bar">
                <div
                  class="add-tracks-modal__progress-fill"
                  :style="{ width: `${(artistAddingProgress.current / artistAddingProgress.total) * 100}%` }"
                ></div>
              </div>
            </div>

            <div class="add-tracks-modal__actions">
              <button
                class="button button--primary"
                :class="{ 'button--loading': artistLoading }"
                :disabled="artistLoading || selectedTrackCount === 0"
                @click="addSelectedTracks"
              >
                {{ artistLoading ? 'Adding to Catalogue...' : `Add ${selectedTrackCount} Track${selectedTrackCount !== 1 ? 's' : ''} to Catalogue` }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import FormGroup from '@baserow/modules/core/components/FormGroup'
import FormInput from '@baserow/modules/core/components/FormInput'
import IsrcService from '@baserow/modules/database/services/isrc'

export default {
  name: 'AddTracksModal',
  components: {
    FormGroup,
    FormInput,
  },
  mixins: [modal],
  props: {
    database: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      activeTab: 'manual',
      // Manual entry state
      manualInput: '',
      enrichedTrack: null,
      loading: false,
      error: null,
      success: false,
      // Artist import state
      artistInput: '',
      artistData: null,
      trackSelections: [],
      artistLoading: false,
      artistError: null,
      artistIsReviewing: false,
      artistAddingProgress: null,
      artistShowResults: false,
      artistAddResults: null,
    }
  },
  computed: {
    isrcApiBaseUrl() {
      return this.$config?.isrcAnalyticsApiUrl || process.env.ISRC_ANALYTICS_API_URL || ''
    },
    cataloguePageUrl() {
      // TODO: Configure this via environment or settings
      return '/catalogue'
    },
    allTracksSelected() {
      return this.trackSelections.length > 0 && this.trackSelections.every(ts => ts.selected)
    },
    someTracksSelected() {
      return this.trackSelections.some(ts => ts.selected)
    },
    selectedTrackCount() {
      return this.trackSelections.filter(ts => ts.selected).length
    },
  },
  methods: {
    async enrichTrack() {
      if (!this.manualInput) return

      this.loading = true
      this.error = null
      this.success = false

      try {
        const { data } = await IsrcService(this.$client, null, this.isrcApiBaseUrl).enrichTrack(
          this.manualInput
        )
        this.enrichedTrack = data
      } catch (err) {
        const errorMessage =
          err.response?.data?.error ||
          err.message ||
          'Failed to fetch track information'
        this.error = errorMessage
      } finally {
        this.loading = false
      }
    },
    async addTrack() {
      if (!this.enrichedTrack) return

      this.loading = true
      this.error = null

      try {
        await IsrcService(this.$client, null, this.isrcApiBaseUrl).addTrack(this.enrichedTrack)

        this.success = true
        this.enrichedTrack = null
        this.manualInput = ''

        // Emit event to refresh table view if needed
        this.$emit('track-added')
      } catch (err) {
        const errorMessage =
          err.response?.data?.error ||
          err.message ||
          'Failed to add track to catalogue'
        this.error = errorMessage
      } finally {
        this.loading = false
      }
    },
    resetForm() {
      this.manualInput = ''
      this.enrichedTrack = null
      this.error = null
      this.success = false
    },
    // Artist import methods
    async fetchArtistTracks() {
      if (!this.artistInput) return

      this.artistLoading = true
      this.artistError = null

      try {
        const { data } = await IsrcService(this.$client, null, this.isrcApiBaseUrl).enrichArtist(this.artistInput)

        this.artistData = data.artist
        this.trackSelections = data.tracks.map(track => ({
          track,
          selected: true,
        }))
        this.artistIsReviewing = true
      } catch (err) {
        this.artistError = err.message || 'Failed to fetch artist tracks'
      } finally {
        this.artistLoading = false
      }
    },
    toggleAllTracks(checked) {
      this.trackSelections = this.trackSelections.map(ts => ({
        ...ts,
        selected: checked,
      }))
    },
    toggleTrackSelection(index) {
      this.trackSelections[index].selected = !this.trackSelections[index].selected
    },
    cancelArtistReview() {
      this.artistIsReviewing = false
      this.artistData = null
      this.trackSelections = []
    },
    resetArtistForm() {
      this.artistInput = ''
      this.artistData = null
      this.trackSelections = []
      this.artistError = null
      this.artistIsReviewing = false
      this.artistAddingProgress = null
      this.artistShowResults = false
      this.artistAddResults = null
    },
    async addSelectedTracks() {
      const selectedTracks = this.trackSelections.filter(ts => ts.selected).map(ts => ts.track)

      if (selectedTracks.length === 0) {
        this.artistError = 'Please select at least one track'
        return
      }

      this.artistError = null
      this.artistLoading = true
      this.artistAddingProgress = { current: 0, total: selectedTracks.length }

      let successCount = 0
      let failedCount = 0
      const errors = []

      try {
        // Process tracks in batches of 10
        const BATCH_SIZE = 10
        for (let i = 0; i < selectedTracks.length; i += BATCH_SIZE) {
          const batch = selectedTracks.slice(i, i + BATCH_SIZE)

          const results = await Promise.allSettled(
            batch.map(async (track) => {
              try {
                await IsrcService(this.$client, null, this.isrcApiBaseUrl).addTrack(track)
                return { success: true, track }
              } catch (err) {
                return {
                  success: false,
                  track,
                  error: err.response?.data?.error || err.message || 'Failed to add',
                }
              }
            })
          )

          for (const result of results) {
            if (result.status === 'fulfilled') {
              if (result.value.success) {
                successCount++
              } else {
                failedCount++
                errors.push(`${result.value.track.title}: ${result.value.error}`)
              }
            } else {
              failedCount++
              errors.push(`Network error: ${result.reason?.message || 'Unknown'}`)
            }
          }

          this.artistAddingProgress = {
            current: Math.min(i + BATCH_SIZE, selectedTracks.length),
            total: selectedTracks.length,
          }
        }

        this.artistAddResults = {
          succeeded: successCount,
          failed: failedCount,
          errors,
        }
        this.artistShowResults = true
        this.artistInput = ''
        this.artistData = null
        this.trackSelections = []
        this.artistIsReviewing = false
        this.artistAddingProgress = null
      } catch (err) {
        this.artistError = 'Network error. Please try again.'
      } finally {
        this.artistLoading = false
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.add-tracks-modal {
  min-height: 400px;
}

.add-tracks-modal__title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #111827;
}

.add-tracks-modal__description {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 24px;
}

.add-tracks-modal__tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 0;
}

.add-tracks-modal__tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.15s ease;
  margin-bottom: -1px;

  &:hover {
    color: #374151;
  }

  &--active {
    color: #2563eb;
    border-bottom-color: #2563eb;
  }

  i {
    font-size: 16px;
  }
}

.add-tracks-modal__content {
  min-height: 300px;
}

.add-tracks-modal__form {
  max-width: 500px;
}

.add-tracks-modal__hint {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 6px;
}

.add-tracks-modal__preview {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  margin: 16px 0;
}

.add-tracks-modal__cover {
  flex-shrink: 0;

  img {
    width: 80px;
    height: 80px;
    border-radius: 6px;
    object-fit: cover;
  }
}

.add-tracks-modal__track-info {
  flex: 1;
  min-width: 0;
}

.add-tracks-modal__track-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 4px;
}

.add-tracks-modal__track-artist {
  font-size: 14px;
  color: #374151;
  margin-bottom: 8px;
}

.add-tracks-modal__track-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #6b7280;
}

.add-tracks-modal__isrc {
  font-family: monospace;
  background: #e5e7eb;
  padding: 2px 6px;
  border-radius: 4px;
}

.add-tracks-modal__error {
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
  margin: 16px 0;
}

.add-tracks-modal__success {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  color: #16a34a;
  font-size: 14px;
  margin: 16px 0;

  i {
    font-size: 18px;
  }
}

.add-tracks-modal__actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.add-tracks-modal__placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: #9ca3af;

  i {
    font-size: 48px;
    margin-bottom: 16px;
    color: #d1d5db;
  }

  p {
    margin: 0;
    font-size: 14px;

    &:first-of-type {
      font-size: 16px;
      color: #6b7280;
      margin-bottom: 8px;
    }
  }
}

.add-tracks-modal__link {
  color: #2563eb;
  text-decoration: underline;

  &:hover {
    color: #1d4ed8;
  }
}

// Artist import styles
.add-tracks-modal__artist-review {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.add-tracks-modal__artist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.add-tracks-modal__artist-name {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.add-tracks-modal__cancel-btn {
  background: none;
  border: none;
  color: #6b7280;
  font-size: 14px;
  cursor: pointer;

  &:hover {
    color: #374151;
  }
}

.add-tracks-modal__select-all {
  padding: 12px 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.add-tracks-modal__checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;

  input {
    width: 16px;
    height: 16px;
    cursor: pointer;
  }
}

.add-tracks-modal__track-list {
  max-height: 350px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.add-tracks-modal__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;

  thead {
    background: #f9fafb;
    position: sticky;
    top: 0;

    th {
      padding: 10px 12px;
      text-align: left;
      font-weight: 500;
      color: #6b7280;
      border-bottom: 1px solid #e5e7eb;
    }
  }

  tbody tr {
    border-bottom: 1px solid #f3f4f6;

    &:hover {
      background: #f9fafb;
    }

    td {
      padding: 10px 12px;
      vertical-align: middle;
    }
  }
}

.add-tracks-modal__th-checkbox {
  width: 40px;
}

.add-tracks-modal__th-cover {
  width: 52px;
}

.add-tracks-modal__table-cover {
  width: 40px;
  height: 40px;
  border-radius: 4px;
  object-fit: cover;
}

.add-tracks-modal__table-cover-placeholder {
  width: 40px;
  height: 40px;
  background: #e5e7eb;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: #9ca3af;
}

.add-tracks-modal__track-cell-title {
  font-weight: 500;
  color: #111827;
}

.add-tracks-modal__progress {
  padding: 12px 16px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 6px;

  p {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: #2563eb;
  }
}

.add-tracks-modal__progress-bar {
  width: 100%;
  height: 6px;
  background: #dbeafe;
  border-radius: 3px;
  overflow: hidden;
}

.add-tracks-modal__progress-fill {
  height: 100%;
  background: #2563eb;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.add-tracks-modal__results {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.add-tracks-modal__results-box {
  padding: 20px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.add-tracks-modal__results-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 16px 0;
}

.add-tracks-modal__results-stats {
  font-size: 14px;

  p {
    margin: 0 0 4px 0;
  }
}

.add-tracks-modal__results-label {
  font-weight: 500;
}

.add-tracks-modal__results-success {
  color: #16a34a;
}

.add-tracks-modal__results-failed {
  color: #dc2626;
}

.add-tracks-modal__results-errors {
  margin-top: 12px;

  details {
    font-size: 13px;

    summary {
      cursor: pointer;
      color: #6b7280;

      &:hover {
        color: #374151;
      }
    }

    ul {
      margin: 8px 0 0 0;
      padding-left: 20px;
      color: #dc2626;
      max-height: 120px;
      overflow-y: auto;
    }
  }
}

.add-tracks-modal__results-more {
  font-style: italic;
}

.add-tracks-modal__results-actions {
  display: flex;
  gap: 12px;
}
</style>
