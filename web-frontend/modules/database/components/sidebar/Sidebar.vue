<template>
  <SidebarApplication
    :workspace="workspace"
    :application="application"
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
    <template v-if="isAppSelected(application)" #body>
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
      </div>
      <AddTracksModal ref="addTracksModal" :database="application" />
      <AddPlaylistsModal ref="addPlaylistsModal" :database="application" />

      <!-- Show "+ New table" for non-read-only databases -->
      <a
        v-if="
          !isReadOnlyDatabase &&
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
  computed: {
    /**
     * ISRCAnalytics: Check if this is a read-only database.
     * Live Catalogue databases should not allow adding new tables.
     */
    isReadOnlyDatabase() {
      return this.application.name === 'Live Catalogue'
    },
    orderedTables() {
      return this.application.tables
        .map((table) => table)
        .sort((a, b) => a.order - b.order)
    },
    pendingJobs() {
      return this.$store.getters['job/getAll'].filter((job) =>
        this.$registry
          .get('job', job.type)
          .isJobPartOfApplication(job, this.application)
      )
    },
    ...mapGetters({ isAppSelected: 'application/isSelected' }),
  },
  methods: {
    async selected(application) {
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
  margin: 10px 0 10px 6px;
  padding-top: 8px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.sidebar-add-section__title {
  font-size: 11px;
  font-weight: 500;
  color: #6b7280;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sidebar-add-section__buttons {
  display: flex;
  gap: 8px;
}

.sidebar-add-section__button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 500;
  color: #374151;
  background-color: #f3f4f6;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background-color: #e5e7eb;
    color: #111827;
    text-decoration: none;
  }
}

</style>
