<template>
  <SidebarApplication
    :workspace="workspace"
    :application="sidebarApplication"
    :custom-icon-class="customIconClass"
    :is-managed-database="isManagedDatabase"
    @selected="selected"
  >
    <template #context>
      <li class="context__menu-item">
        <nuxt-link
          :to="{
            name: 'database-api-docs-detail',
            params: {
              databaseId: application.id,
            },
          }"
          class="context__menu-item-link"
        >
          <i class="context__menu-item-icon iconoir-book"></i>
          {{ $t('sidebar.viewAPI') }}
        </nuxt-link>
      </li>
    </template>
    <template v-if="isAppSelected(application) || shouldAutoExpand" #body>
      <ul class="tree__subs">
        <SidebarItem
          v-for="table in orderedTables"
          :key="table.id"
          v-sortable="{
            id: table.id,
            update: orderTables,
            marginTop: -1.5,
            enabled: false,
          }"
          :database="sidebarApplication"
          :table="table"
        ></SidebarItem>
      </ul>
      <ul v-if="pendingJobs.length" class="tree__subs">
        <component
          :is="getPendingJobComponent(job)"
          v-for="job in pendingJobs"
          :key="job.id"
          :job="job"
        >
        </component>
      </ul>
      <!-- MusicEngine: Show Add Tracks/Playlists section for Live Catalogue -->
      <div v-if="isReadOnlyDatabase" class="sidebar-add-section">
        <div class="sidebar-add-section__title">Add to Live Catalogue</div>
        <div class="sidebar-add-section__buttons">
          <a
            class="sidebar-add-section__button"
            @click="$refs.addTracksModal.show()"
          >
            Tracks
          </a>
          <a
            class="sidebar-add-section__button"
            @click="$refs.addPlaylistsModal.show()"
          >
            Playlists
          </a>
        </div>

        <!-- Slot Usage Display -->
        <div class="sidebar-slots">
          <!-- Track Slots -->
          <div class="sidebar-slots__row">
            <span class="sidebar-slots__label">ISRC Slots</span>
            <span class="sidebar-slots__value">
              {{ trackSlotsDisplay }}
            </span>
            <a
              class="sidebar-slots__upgrade"
              :class="{ 'sidebar-slots__upgrade--disabled': false }"
              :href="upgradeUrl"
              target="_blank"
              title="Get more ISRC slots"
            >
              +
            </a>
          </div>

          <!-- Playlist Slots -->
          <div class="sidebar-slots__row">
            <span class="sidebar-slots__label">Playlist Slots</span>
            <span class="sidebar-slots__value">
              {{ playlistSlotsDisplay }}
            </span>
            <a
              class="sidebar-slots__upgrade"
              :class="{ 'sidebar-slots__upgrade--disabled': playlistSlots.unlimited }"
              :href="playlistSlots.unlimited ? null : upgradeUrl"
              :target="playlistSlots.unlimited ? null : '_blank'"
              :title="playlistSlots.unlimited ? 'Unlimited playlists' : 'Get more playlist slots'"
            >
              +
            </a>
          </div>
        </div>
      </div>
      <AddTracksModal ref="addTracksModal" :database="application" />
      <AddPlaylistsModal ref="addPlaylistsModal" :database="application" />

      <!-- MusicEngine: Hide "+ New table" for managed databases -->
      <a
        v-if="
          !shouldHideAddTable &&
          $hasPermission(
            'database.create_table',
            application,
            application.workspace.id
          )
        "
        class="tree__sub-add"
        data-highlight="create-table"
        @click="$refs.createTableModal.show()"
      >
        <i class="tree__sub-add-icon iconoir-plus"></i>
        {{ $t('sidebar.createTable') }}
      </a>
      <CreateTableModal ref="createTableModal" :database="application" />
    </template>
  </SidebarApplication>
</template>

<script>
import { mapGetters } from 'vuex'
import { notifyIf } from '@baserow/modules/core/utils/error'
import SidebarItem from '@baserow/modules/database/components/sidebar/SidebarItem'
import SidebarApplication from '@baserow/modules/core/components/sidebar/SidebarApplication'
import CreateTableModal from '@baserow/modules/database/components/table/CreateTableModal'
import AddTracksModal from '@baserow/modules/database/components/isrc/AddTracksModal'
import AddPlaylistsModal from '@baserow/modules/database/components/isrc/AddPlaylistsModal'
import IsrcService from '@baserow/modules/database/services/isrc'

export default {
  name: 'Sidebar',
  components: {
    CreateTableModal,
    SidebarApplication,
    SidebarItem,
    AddTracksModal,
    AddPlaylistsModal,
  },
  props: {
    application: {
      type: Object,
      required: true,
    },
    displayName: {
      type: String,
      required: false,
      default: null,
    },
    visibleTableNames: {
      type: Array,
      required: false,
      default: null,
    },
    showPendingJobs: {
      type: Boolean,
      required: false,
      default: true,
    },
    workspace: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      trackSlots: { used: null, limit: null },
      playlistSlots: { used: null, limit: null, unlimited: false },
      slotsLoading: false,
      slotFetchAttempts: 0,
      slotRetryTimeoutId: null,
      slotRefreshIntervalId: null,
    }
  },
  computed: {
    sidebarApplication() {
      if (!this.displayName) {
        return this.application
      }

      return {
        ...this.application,
        name: this.displayName,
      }
    },
    normalizedDatabaseName() {
      return (this.sidebarApplication.name || '').trim().toLowerCase()
    },
    /**
     * MusicEngine: Check if this database is part of the managed workflow.
     */
    isDistributionPipelineDatabase() {
      return ['distribution management', 'catalog pipeline', 'distribution pipeline', 'production pipeline', 'production catalogue'].includes(
        this.normalizedDatabaseName
      )
    },
    /**
     * MusicEngine: Check if this is a read-only database.
     * Live Catalogue databases should not allow adding new tables.
     */
    isReadOnlyDatabase() {
      return this.normalizedDatabaseName === 'live catalogue'
    },
    /**
     * MusicEngine: Check if this is a managed database (disables clicking).
     */
    isManagedDatabase() {
      return this.isReadOnlyDatabase || this.isDistributionPipelineDatabase
    },
    /**
     * MusicEngine: Give each workflow stage a distinct icon treatment.
     */
    customIconClass() {
      if (this.normalizedDatabaseName === 'catalog pipeline') {
        return 'iconoir-db sidebar-application-icon sidebar-application-icon--production'
      }

      if (this.normalizedDatabaseName === 'distribution management') {
        return 'iconoir-git-fork sidebar-application-icon sidebar-application-icon--distribution'
      }

      if (this.isReadOnlyDatabase) {
        return 'iconoir-music-double-note sidebar-application-icon sidebar-application-icon--catalogue'
      }

      if (['distribution pipeline', 'production pipeline', 'production catalogue'].includes(this.normalizedDatabaseName)) {
        return 'iconoir-db sidebar-application-icon sidebar-application-icon--production'
      }

      return null
    },
    /**
     * MusicEngine: Check if we should hide the "Add table" button.
     * The managed workflow databases should not allow adding new tables.
     */
    shouldHideAddTable() {
      return true
    },
    /**
     * MusicEngine: Auto-expand the managed workflow databases.
     * These databases are always expanded (not collapsible).
     */
    shouldAutoExpand() {
      return this.isManagedDatabase
    },
    /**
     * MusicEngine: Hidden junction tables that should not be shown in the sidebar.
     * These are internal tables used for many-to-many relationships.
     */
    hiddenTableNames() {
      return ['Track_Artists', 'Playlist_Tracks']
    },
    orderedTables() {
      return this.application.tables
        .filter((table) => {
          if (
            Array.isArray(this.visibleTableNames) &&
            this.visibleTableNames.length > 0 &&
            !this.visibleTableNames.includes(table.name)
          ) {
            return false
          }

          // MusicEngine: Hide junction tables from Live Catalogue sidebar
          if (this.isReadOnlyDatabase && this.hiddenTableNames.includes(table.name)) {
            return false
          }
          return true
        })
        .sort((a, b) => a.order - b.order)
    },
    pendingJobs() {
      if (!this.showPendingJobs) {
        return []
      }

      return this.$store.getters['job/getAll'].filter((job) =>
        this.$registry
          .get('job', job.type)
          .isJobPartOfApplication(job, this.application)
      )
    },
    upgradeUrl() {
      const baseUrl = this.$config?.isrcAnalyticsApiUrl || process.env.ISRC_ANALYTICS_API_URL || 'https://musicengine.ai'
      return `${baseUrl}/settings/billing`
    },
    isrcApiBaseUrl() {
      return this.$config?.isrcAnalyticsApiUrl || process.env.ISRC_ANALYTICS_API_URL || 'https://musicengine.ai'
    },
    trackSlotsDisplay() {
      if (this.hasValidTrackSlots) {
        return `${this.trackSlots.used} / ${this.trackSlots.limit}`
      }
      return this.slotsLoading ? 'Loading...' : 'Unavailable'
    },
    playlistSlotsDisplay() {
      if (!this.hasValidPlaylistSlots) {
        return this.slotsLoading ? 'Loading...' : 'Unavailable'
      }
      if (this.playlistSlots.unlimited) {
        return `${this.playlistSlots.used} / Unlimited`
      }
      return `${this.playlistSlots.used} / ${this.playlistSlots.limit}`
    },
    hasValidTrackSlots() {
      return (
        Number.isFinite(this.trackSlots.used) &&
        Number.isFinite(this.trackSlots.limit) &&
        this.trackSlots.limit > 0
      )
    },
    hasValidPlaylistSlots() {
      if (!Number.isFinite(this.playlistSlots.used)) {
        return false
      }
      if (this.playlistSlots.unlimited) {
        return true
      }
      return (
        Number.isFinite(this.playlistSlots.limit) &&
        this.playlistSlots.limit > 0
      )
    },
    ...mapGetters({
      isAppSelected: 'application/isSelected',
      authToken: 'auth/token',
    }),
  },
  watch: {
    isReadOnlyDatabase: {
      immediate: true,
      handler(isReadOnly) {
        if (isReadOnly) {
          this.restoreSlotsFromCache()
          this.startSlotsAutoRefresh()
          this.fetchSlots()
        } else {
          this.stopSlotsAutoRefresh()
        }
      },
    },
    authToken(newValue, oldValue) {
      if (this.isReadOnlyDatabase && newValue && newValue !== oldValue) {
        this.fetchSlots()
      }
    },
    isrcApiBaseUrl(newValue, oldValue) {
      if (this.isReadOnlyDatabase && newValue !== oldValue) {
        this.fetchSlots()
      }
    },
  },
  mounted() {
    this.$nextTick(() => {
      this.pruneLegacyPipelineActions()
    })
  },
  updated() {
    this.$nextTick(() => {
      this.pruneLegacyPipelineActions()
    })
  },
  beforeDestroy() {
    this.stopSlotsAutoRefresh()
  },
  methods: {
    pruneLegacyPipelineActions() {
      if (!this.isDistributionPipelineDatabase || !this.$el) {
        return
      }

      // Defensive cleanup: ensure stale Release/Account quick actions never render.
      const sections = this.$el.querySelectorAll('.sidebar-add-section')
      sections.forEach((section) => {
        const title = (
          section.querySelector('.sidebar-add-section__title')?.textContent || ''
        )
          .trim()
          .toLowerCase()
        const hasLegacyFullButton = !!section.querySelector(
          '.sidebar-add-section__button--full'
        )

        if (hasLegacyFullButton || title === 'releases' || title === 'accounts') {
          section.remove()
        }
      })
    },
    normalizeTrackSlots(data) {
      const used = Number(data?.used)
      const limit = Number(data?.limit)
      if (!Number.isFinite(used) || !Number.isFinite(limit) || limit <= 0) {
        return null
      }
      return { used, limit }
    },
    normalizePlaylistSlots(data) {
      const used = Number(data?.used)
      const unlimited = Boolean(data?.unlimited)
      if (!Number.isFinite(used)) {
        return null
      }
      if (unlimited) {
        return { used, limit: null, unlimited: true }
      }
      const limit = Number(data?.limit)
      if (!Number.isFinite(limit) || limit <= 0) {
        return null
      }
      return { used, limit, unlimited: false }
    },
    restoreSlotsFromCache() {
      if (process.server) {
        return
      }
      try {
        const raw = window.localStorage.getItem('isrc-slot-cache-v1')
        if (!raw) {
          return
        }
        const parsed = JSON.parse(raw)
        const trackSlots = this.normalizeTrackSlots(parsed?.trackSlots)
        const playlistSlots = this.normalizePlaylistSlots(parsed?.playlistSlots)
        if (trackSlots && playlistSlots) {
          this.trackSlots = trackSlots
          this.playlistSlots = playlistSlots
        }
      } catch (error) {
        console.warn('Failed to restore slot cache:', error)
      }
    },
    persistSlotsToCache() {
      if (process.server || !this.hasValidTrackSlots || !this.hasValidPlaylistSlots) {
        return
      }
      try {
        window.localStorage.setItem(
          'isrc-slot-cache-v1',
          JSON.stringify({
            trackSlots: this.trackSlots,
            playlistSlots: this.playlistSlots,
            updatedAt: new Date().toISOString(),
          })
        )
      } catch (error) {
        console.warn('Failed to persist slot cache:', error)
      }
    },
    queueSlotsRetry() {
      if (this.slotFetchAttempts >= 5) {
        return
      }
      const delay = Math.min(2000 * 2 ** (this.slotFetchAttempts - 1), 30000)
      clearTimeout(this.slotRetryTimeoutId)
      this.slotRetryTimeoutId = setTimeout(() => {
        this.fetchSlots()
      }, delay)
    },
    startSlotsAutoRefresh() {
      if (this.slotRefreshIntervalId) {
        return
      }
      this.slotRefreshIntervalId = setInterval(() => {
        this.fetchSlots()
      }, 60000)
    },
    stopSlotsAutoRefresh() {
      clearTimeout(this.slotRetryTimeoutId)
      this.slotRetryTimeoutId = null
      clearInterval(this.slotRefreshIntervalId)
      this.slotRefreshIntervalId = null
    },
    async fetchSlots() {
      if (!this.isReadOnlyDatabase || this.slotsLoading) {
        return
      }
      try {
        this.slotsLoading = true
        // MusicEngine: Pass auth token for cross-origin authentication
        const token = this.authToken
        const apiUrl = this.isrcApiBaseUrl
        const [trackResponse, playlistResponse] = await Promise.all([
          IsrcService(this.$client, token, apiUrl).getTrackSlots(),
          IsrcService(this.$client, token, apiUrl).getPlaylistSlots(),
        ])
        const trackSlots = this.normalizeTrackSlots(trackResponse.data)
        const playlistSlots = this.normalizePlaylistSlots(playlistResponse.data)
        if (!trackSlots || !playlistSlots) {
          throw new Error('Invalid slot payload received from API.')
        }

        this.trackSlots = trackSlots
        this.playlistSlots = playlistSlots
        this.slotFetchAttempts = 0
        this.persistSlotsToCache()
      } catch (error) {
        if (error?.code === 'SLOT_AUTH_REQUIRED') {
          // Auth can expire while the iframe sits idle. Keep cached values and wait
          // for the next normal refresh instead of spamming retries/errors.
          this.slotFetchAttempts = 0
          return
        }
        this.slotFetchAttempts += 1
        this.queueSlotsRetry()
        console.error('Failed to fetch slot usage:', error)
      } finally {
        this.slotsLoading = false
      }
    },
    async selected(application) {
      // MusicEngine: Managed databases don't need selection handling - they're always expanded
      const normalizedName = (application.name || '').trim().toLowerCase()
      const isManagedDb = [
        'catalog pipeline',
        'distribution pipeline',
        'production pipeline',
        'production catalogue',
        'live catalogue',
      ].includes(normalizedName)
      if (isManagedDb) {
        return // Do nothing - clicking is handled by SidebarApplication
      }
      try {
        await this.$store.dispatch('application/select', application)
      } catch (error) {
        notifyIf(error, 'workspace')
      }
    },
    async orderTables(order, oldOrder) {
      try {
        await this.$store.dispatch('table/order', {
          database: this.application,
          order,
          oldOrder,
        })
      } catch (error) {
        notifyIf(error, 'table')
      }
    },
    getPendingJobComponent(job) {
      return this.$registry.get('job', job.type).getSidebarComponent()
    },
  },
}
</script>

<style lang="scss" scoped>
.sidebar-add-section {
  margin: 6px 0 0 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
  overflow: hidden;
}

:deep(.sidebar-application-icon) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1;
  box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.04);
}

:deep(.sidebar-application-icon--production) {
  background: rgba(84, 101, 255, 0.12);
  color: #5465ff;
}

:deep(.sidebar-application-icon--distribution) {
  background: rgba(24, 148, 112, 0.14);
  color: #118468;
}

:deep(.sidebar-application-icon--catalogue) {
  background: rgba(204, 137, 28, 0.14);
  color: #b56b09;
}

.sidebar-add-section__title {
  font-size: 10px;
  font-weight: 500;
  color: var(--text-muted);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.sidebar-add-section__buttons {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  max-width: 100%;
}

.sidebar-add-section__button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
  background-color: var(--bg-tertiary);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  border: none;
  white-space: nowrap;
  min-width: 0;

  &:hover {
    background-color: var(--bg-hover);
    color: var(--text-primary);
    text-decoration: none;
  }

  &--full {
    width: 100%;
    justify-content: center;
    padding: 8px 12px;
  }
}

.sidebar-slots {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar-slots__row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
}

.sidebar-slots__label {
  color: var(--text-secondary);
  min-width: 70px;
}

.sidebar-slots__value {
  color: var(--text-primary);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.sidebar-slots__upgrade {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  font-size: 12px;
  font-weight: 600;
  color: #5190ef;
  background-color: var(--bg-tertiary);
  border-radius: 4px;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.15s ease;
  margin-left: auto;

  &:hover {
    background-color: var(--bg-hover);
    color: #5190ef;
    text-decoration: none;
  }

  &--disabled {
    color: var(--text-muted);
    background-color: var(--bg-tertiary);
    cursor: default;
    pointer-events: none;
  }
}

</style>
