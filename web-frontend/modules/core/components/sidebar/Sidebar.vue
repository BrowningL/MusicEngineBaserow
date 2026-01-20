<template>
  <div class="sidebar" :class="{ 'sidebar--collapsed': collapsed }">
    <component
      :is="component"
      v-for="(component, index) in impersonateComponent"
      :key="index"
    ></component>
    <template v-if="showAdmin">
      <div class="sidebar__head">
        <a href="#" class="sidebar__back" @click="setShowAdmin(false)">
          <i class="sidebar__back-icon iconoir-nav-arrow-left"></i>
        </a>
        <div v-show="!collapsed" class="sidebar__title">
          {{ $t('sidebar.adminSettings') }}
        </div>
      </div>
      <SidebarAdmin v-show="!collapsed"></SidebarAdmin>
    </template>
    <template v-if="!showAdmin">
      <!-- ISRCAnalytics: Airtable-style layout - show ViewsSidebar when viewing a table -->
      <template v-if="isTableViewMode && currentDatabase && currentTable">
        <ViewsSidebar
          v-show="!collapsed"
          :database="currentDatabase"
          :table="currentTable"
          :views="currentViews"
          :read-only="false"
          @selected-view="navigateToView"
        />
      </template>
      <template v-else>
        <!-- ISRCAnalytics: Removed workspace selector entirely -->

        <SidebarMenu
          v-show="!collapsed"
          v-if="hasSelectedWorkspace"
          :selected-workspace="selectedWorkspace"
          :right-sidebar-open="rightSidebarOpen"
          @open-workspace-search="$emit('open-workspace-search')"
        ></SidebarMenu>

        <SidebarWithWorkspace
          v-show="!collapsed"
          v-if="hasSelectedWorkspace"
          :applications="applications"
          :selected-workspace="selectedWorkspace"
        ></SidebarWithWorkspace>

        <SidebarWithoutWorkspace
          v-show="!collapsed"
          v-if="!hasSelectedWorkspace"
          :workspaces="workspaces"
        ></SidebarWithoutWorkspace>
      </template>
    </template>
    <SidebarFoot
      :collapsed="collapsed"
      :width="width"
      @set-col1-width="$emit('set-col1-width', $event)"
    ></SidebarFoot>
  </div>
</template>

<script>
import { mapGetters, mapState } from 'vuex'

import SidebarUserContext from '@baserow/modules/core/components/sidebar/SidebarUserContext'
import SidebarWithWorkspace from '@baserow/modules/core/components/sidebar/SidebarWithWorkspace'
import SidebarWithoutWorkspace from '@baserow/modules/core/components/sidebar/SidebarWithoutWorkspace'
import SidebarAdmin from '@baserow/modules/core/components/sidebar/SidebarAdmin'
import SidebarFoot from '@baserow/modules/core/components/sidebar/SidebarFoot'
import SidebarMenu from '@baserow/modules/core/components/sidebar/SidebarMenu'
import SidebarAdminItem from './SidebarAdminItem.vue'
import ViewsSidebar from '@baserow/modules/database/components/view/ViewsSidebar'

export default {
  name: 'Sidebar',
  components: {
    SidebarAdmin,
    SidebarWithoutWorkspace,
    SidebarWithWorkspace,
    SidebarUserContext,
    SidebarMenu,
    SidebarFoot,
    ViewsSidebar,
  },
  props: {
    applications: {
      type: Array,
      required: true,
    },
    workspaces: {
      type: Array,
      required: true,
    },
    selectedWorkspace: {
      type: Object,
      required: true,
    },
    collapsed: {
      type: Boolean,
      required: false,
      default: () => false,
    },
    width: {
      type: Number,
      required: false,
      default: 240,
    },
    rightSidebarOpen: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      showAdmin: false,
    }
  },

  computed: {
    SidebarAdminItem() {
      return SidebarAdminItem
    },
    impersonateComponent() {
      return Object.values(this.$registry.getAll('plugin'))
        .map((plugin) => plugin.getImpersonateComponent())
        .filter((component) => component !== null)
    },
    hasSelectedWorkspace() {
      return Object.prototype.hasOwnProperty.call(this.selectedWorkspace, 'id')
    },
    ...mapGetters({
      name: 'auth/getName',
      unreadNotificationsInOtherWorkspaces:
        'notification/anyOtherWorkspaceWithUnread',
    }),
    ...mapState({
      allViews: (state) => state.view?.items || [],
      selectedView: (state) => state.view?.selected || null,
    }),
    // ISRCAnalytics: Airtable-style layout computed properties
    isTableViewMode() {
      return this.$route.matched.some(
        (r) => r.name === 'database-table' || r.name === 'database-table-row'
      )
    },
    currentDatabase() {
      if (!this.isTableViewMode) return null
      const databaseId = parseInt(this.$route.params.databaseId)
      return this.applications.find((app) => app.id === databaseId) || null
    },
    currentTable() {
      if (!this.isTableViewMode || !this.currentDatabase) return null
      const tableId = parseInt(this.$route.params.tableId)
      return (
        this.currentDatabase.tables?.find((t) => t.id === tableId) || null
      )
    },
    currentViews() {
      if (!this.isTableViewMode) return []
      return this.allViews || []
    },
  },
  created() {
    // Checks whether the rendered page is an admin page. If so, switch the left sidebar
    // navigation to the admin.
    this.showAdmin = Object.values(this.$registry.getAll('admin')).some(
      (adminType) => {
        return this.$route.matched.some(
          ({ name }) => name === adminType.routeName
        )
      }
    )
  },
  methods: {
    setShowAdmin(value) {
      this.showAdmin = value
      this.$forceUpdate()
    },
    // ISRCAnalytics: Navigate to selected view
    navigateToView(view) {
      if (!this.currentDatabase || !this.currentTable) return

      this.$nuxt.$router.push({
        name: 'database-table',
        params: {
          databaseId: this.currentDatabase.id,
          tableId: this.currentTable.id,
          viewId: view.id,
        },
      })
    },
  },
}
</script>
