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
          <div class="add-tracks-modal__placeholder">
            <i class="iconoir-user"></i>
            <p>Artist import coming soon</p>
            <p class="add-tracks-modal__hint">
              For now, use the
              <a :href="cataloguePageUrl" target="_blank" class="add-tracks-modal__link">
                full catalogue page
              </a>
              for artist imports.
            </p>
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
      manualInput: '',
      enrichedTrack: null,
      loading: false,
      error: null,
      success: false,
    }
  },
  computed: {
    cataloguePageUrl() {
      // TODO: Configure this via environment or settings
      return '/catalogue'
    },
  },
  methods: {
    async enrichTrack() {
      if (!this.manualInput) return

      this.loading = true
      this.error = null
      this.success = false

      try {
        const { data } = await IsrcService(this.$client).enrichTrack(
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
        await IsrcService(this.$client).addTrack(this.enrichedTrack)

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
</style>
