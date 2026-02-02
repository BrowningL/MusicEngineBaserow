<template>
  <Modal :wide="true">
    <template #content>
      <div class="add-playlists-modal">
        <h2 class="add-playlists-modal__title">Add Playlists</h2>
        <p class="add-playlists-modal__description">
          Add playlists to monitor by entering a Spotify playlist URL or importing from CSV.
        </p>

        <!-- Tab Navigation -->
        <div class="add-playlists-modal__tabs">
          <button
            class="add-playlists-modal__tab"
            :class="{ 'add-playlists-modal__tab--active': activeTab === 'manual' }"
            @click="activeTab = 'manual'"
          >
            <i class="iconoir-playlist"></i>
            Manual Entry
          </button>
          <button
            class="add-playlists-modal__tab"
            :class="{ 'add-playlists-modal__tab--active': activeTab === 'csv' }"
            @click="activeTab = 'csv'"
          >
            <i class="iconoir-page"></i>
            CSV Import
          </button>
        </div>

        <!-- Manual Entry Tab -->
        <div v-if="activeTab === 'manual'" class="add-playlists-modal__content">
          <div class="add-playlists-modal__form">
            <FormGroup
              :label="'Spotify Playlist URL'"
              small-label
              required
            >
              <FormInput
                v-model="manualInput"
                :placeholder="'e.g., https://open.spotify.com/playlist/...'"
                :disabled="loading"
                @keyup.enter="enrichPlaylist"
              />
              <p class="add-playlists-modal__hint">
                Enter a Spotify playlist URL to fetch playlist information
              </p>
            </FormGroup>

            <!-- Enriched Data Preview -->
            <div v-if="enrichedPlaylist" class="add-playlists-modal__preview">
              <div v-if="enrichedPlaylist.cover_url" class="add-playlists-modal__cover">
                <img :src="enrichedPlaylist.cover_url" alt="Playlist cover" />
              </div>
              <div class="add-playlists-modal__playlist-info">
                <div class="add-playlists-modal__playlist-title">{{ enrichedPlaylist.name }}</div>
                <div class="add-playlists-modal__playlist-owner">by {{ enrichedPlaylist.owner_name || enrichedPlaylist.owner_uri }}</div>
                <div class="add-playlists-modal__playlist-meta">
                  <span v-if="enrichedPlaylist.track_count">{{ enrichedPlaylist.track_count }} tracks</span>
                </div>
              </div>
            </div>

            <!-- Error Message -->
            <div v-if="error" class="add-playlists-modal__error">
              {{ error }}
            </div>

            <!-- Success Message -->
            <div v-if="success" class="add-playlists-modal__success">
              <i class="iconoir-check-circle"></i>
              Playlist added successfully!
            </div>

            <div class="add-playlists-modal__actions">
              <button
                v-if="!enrichedPlaylist"
                class="button button--primary"
                :class="{ 'button--loading': loading }"
                :disabled="!manualInput || loading"
                @click="enrichPlaylist"
              >
                Fetch Playlist Info
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
                  @click="addPlaylist"
                >
                  Add to Playlists
                </button>
              </template>
            </div>
          </div>
        </div>

        <!-- CSV Import Tab -->
        <div v-if="activeTab === 'csv'" class="add-playlists-modal__content">
          <div class="add-playlists-modal__placeholder">
            <i class="iconoir-upload-square"></i>
            <p>CSV import coming soon</p>
            <p class="add-playlists-modal__hint">
              For now, use the
              <a :href="playlistsPageUrl" target="_blank" class="add-playlists-modal__link">
                full playlists page
              </a>
              for CSV imports.
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
  name: 'AddPlaylistsModal',
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
      enrichedPlaylist: null,
      loading: false,
      error: null,
      success: false,
    }
  },
  computed: {
    isrcApiBaseUrl() {
      return this.$config?.isrcAnalyticsApiUrl || process.env.ISRC_ANALYTICS_API_URL || 'https://isrcanalytics.com'
    },
    playlistsPageUrl() {
      // TODO: Configure this via environment or settings
      return '/playlists'
    },
  },
  methods: {
    async enrichPlaylist() {
      if (!this.manualInput) return

      this.loading = true
      this.error = null
      this.success = false

      try {
        const { data } = await IsrcService(this.$client, null, this.isrcApiBaseUrl).enrichPlaylist(
          this.manualInput
        )
        this.enrichedPlaylist = data
      } catch (err) {
        const errorMessage =
          err.response?.data?.error ||
          err.message ||
          'Failed to fetch playlist information'
        this.error = errorMessage
      } finally {
        this.loading = false
      }
    },
    async addPlaylist() {
      if (!this.enrichedPlaylist) return

      this.loading = true
      this.error = null

      try {
        await IsrcService(this.$client, null, this.isrcApiBaseUrl).addPlaylist(this.enrichedPlaylist)

        this.success = true
        this.enrichedPlaylist = null
        this.manualInput = ''

        // Emit event to refresh table view if needed
        this.$emit('playlist-added')
      } catch (err) {
        const errorMessage =
          err.response?.data?.error ||
          err.message ||
          'Failed to add playlist'
        this.error = errorMessage
      } finally {
        this.loading = false
      }
    },
    resetForm() {
      this.manualInput = ''
      this.enrichedPlaylist = null
      this.error = null
      this.success = false
    },
  },
}
</script>

<style lang="scss" scoped>
.add-playlists-modal {
  min-height: 400px;
}

.add-playlists-modal__title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #111827;
}

.add-playlists-modal__description {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 24px;
}

.add-playlists-modal__tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 0;
}

.add-playlists-modal__tab {
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

.add-playlists-modal__content {
  min-height: 300px;
}

.add-playlists-modal__form {
  max-width: 500px;
}

.add-playlists-modal__hint {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 6px;
}

.add-playlists-modal__preview {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  margin: 16px 0;
}

.add-playlists-modal__cover {
  flex-shrink: 0;

  img {
    width: 80px;
    height: 80px;
    border-radius: 6px;
    object-fit: cover;
  }
}

.add-playlists-modal__playlist-info {
  flex: 1;
  min-width: 0;
}

.add-playlists-modal__playlist-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 4px;
}

.add-playlists-modal__playlist-owner {
  font-size: 14px;
  color: #374151;
  margin-bottom: 8px;
}

.add-playlists-modal__playlist-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #6b7280;
}

.add-playlists-modal__error {
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
  margin: 16px 0;
}

.add-playlists-modal__success {
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

.add-playlists-modal__actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.add-playlists-modal__placeholder {
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

.add-playlists-modal__link {
  color: #2563eb;
  text-decoration: underline;

  &:hover {
    color: #1d4ed8;
  }
}
</style>
