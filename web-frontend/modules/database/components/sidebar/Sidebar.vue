<template>
  <SidebarApplication
    :workspace="workspace"
    :application="application"
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
            enabled: $hasPermission(
              'database.order_tables',
              application,
              application.workspace.id
            ),
          }"
          :database="application"
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
      <!-- ISRCAnalytics: Add Release & Account buttons for Production Pipeline -->
      <div v-if="isProductionPipelineDatabase" class="sidebar-add-section">
        <div class="sidebar-add-section__title">Add to Pipeline</div>
        <div class="sidebar-add-section__buttons">
          <button
            class="sidebar-add-section__button"
            @click="openCreateReleaseModal"
          >
            <i class="iconoir-plus"></i> Release
          </button>
          <button
            class="sidebar-add-section__button"
            @click="openCreateAccountModal"
          >
            <i class="iconoir-plus"></i> Account
          </button>
        </div>
      </div>
      <!-- ISRCAnalytics: Show Add Tracks/Playlists section for Live Catalogue -->
      <div v-if="isReadOnlyDatabase" class="sidebar-add-section">
        <div class="sidebar-add-section__title">Add to Catalogue</div>
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
              {{ trackSlots.used }} / {{ trackSlots.limit }}
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
              <template v-if="playlistSlots.unlimited">
                {{ playlistSlots.used }} / Unlimited
              </template>
              <template v-else>
                {{ playlistSlots.used }} / {{ playlistSlots.limit }}
              </template>
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

      <!-- ISRCAnalytics: Hide "+ New table" for managed databases -->
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
    workspace: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      trackSlots: { used: 0, limit: 0 },
      playlistSlots: { used: 0, limit: 0, unlimited: false },
    }
  },
  computed: {
    /**
     * ISRCAnalytics: Check if this is the Production Pipeline database.
     */
    isProductionPipelineDatabase() {
      return this.application.name === 'Production Pipeline'
    },
    /**
     * ISRCAnalytics: Check if this is a read-only database.
     * Live Catalogue databases should not allow adding new tables.
     */
    isReadOnlyDatabase() {
      return this.application.name === 'Live Catalogue'
    },
    /**
     * ISRCAnalytics: Check if this is a managed database (disables clicking).
     */
    isManagedDatabase() {
      const dbName = this.application.name
      return dbName === 'Live Catalogue' || dbName === 'Production Pipeline' || dbName === 'Production Catalogue'
    },
    /**
     * ISRCAnalytics: Custom icon for Live Catalogue (music note).
     * Production Pipeline uses the default database icon.
     */
    customIconClass() {
      if (this.application.name === 'Live Catalogue') {
        return 'iconoir-music-double-note'
      }
      return null
    },
    /**
     * ISRCAnalytics: Check if we should hide the "Add table" button.
     * Both Live Catalogue and Production Pipeline should not allow adding new tables.
     */
    shouldHideAddTable() {
      const dbName = this.application.name
      return dbName === 'Live Catalogue' || dbName === 'Production Pipeline' || dbName === 'Production Catalogue'
    },
    /**
     * ISRCAnalytics: Auto-expand Production Pipeline and Live Catalogue databases.
     * These databases are always expanded (not collapsible).
     */
    shouldAutoExpand() {
      const dbName = this.application.name
      return dbName === 'Production Pipeline' || dbName === 'Live Catalogue' || dbName === 'Production Catalogue'
    },
    /**
     * ISRCAnalytics: Hidden junction tables that should not be shown in the sidebar.
     * These are internal tables used for many-to-many relationships.
     */
    hiddenTableNames() {
      return ['Track_Artists', 'Playlist_Tracks']
    },
    orderedTables() {
      return this.application.tables
        .filter((table) => {
          // ISRCAnalytics: Hide junction tables from Live Catalogue sidebar
          if (this.isReadOnlyDatabase && this.hiddenTableNames.includes(table.name)) {
            return false
          }
          return true
        })
        .sort((a, b) => a.order - b.order)
    },
    pendingJobs() {
      return this.$store.getters['job/getAll'].filter((job) =>
        this.$registry
          .get('job', job.type)
          .isJobPartOfApplication(job, this.application)
      )
    },
    upgradeUrl() {
      const baseUrl = this.$config?.isrcAnalyticsApiUrl || process.env.ISRC_ANALYTICS_API_URL || 'https://isrcanalytics.com'
      return `${baseUrl}/settings/billing`
    },
    isrcApiBaseUrl() {
      return this.$config?.isrcAnalyticsApiUrl || process.env.ISRC_ANALYTICS_API_URL || 'https://isrcanalytics.com'
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
          this.fetchSlots()
        }
      },
    },
  },
  methods: {
    async fetchSlots() {
      try {
        // ISRCAnalytics: Pass auth token for cross-origin authentication
        const token = this.authToken
        const apiUrl = this.isrcApiBaseUrl
        const [trackResponse, playlistResponse] = await Promise.all([
          IsrcService(this.$client, token, apiUrl).getTrackSlots(),
          IsrcService(this.$client, token, apiUrl).getPlaylistSlots(),
        ])
        this.trackSlots = trackResponse.data
        this.playlistSlots = playlistResponse.data
      } catch (error) {
        console.error('Failed to fetch slot usage:', error)
      }
    },
    async selected(application) {
      // ISRCAnalytics: Managed databases don't need selection handling - they're always expanded
      const isManagedDb = ['Production Pipeline', 'Live Catalogue', 'Production Catalogue'].includes(application.name)
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
    openCreateReleaseModal() {
      // Emit global event that GridView listens to
      this.$root.$emit('open-release-modal')
    },
    openCreateAccountModal() {
      // Emit global event that GridView listens to
      this.$root.$emit('open-account-modal')
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
