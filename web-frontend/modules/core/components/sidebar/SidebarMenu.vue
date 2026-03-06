<template>
  <div class="sidebar__section" ph-autocapture="sidebar" data-highlight="menu">
    <ul class="tree">
      <!-- MusicEngine: Removed SidebarSearch, Home, Notifications, Members, and Invite Others links -->
      <component
        :is="component"
        v-for="(component, index) in sidebarWorkspaceComponents"
        :key="'sidebarWorkspaceComponents' + index"
        :workspace="selectedWorkspace"
        :right-sidebar-open="rightSidebarOpen"
      ></component>
      <!-- MusicEngine: Removed Trash item -->
    </ul>
  </div>
</template>

<script>
import TrashModal from '@baserow/modules/core/components/trash/TrashModal'
import WorkspaceMemberInviteModal from '@baserow/modules/core/components/workspace/WorkspaceMemberInviteModal'
import SidebarSearch from '@baserow/modules/core/components/sidebar/SidebarSearch'

export default {
  name: 'SidebarMenu',
  components: {
    TrashModal,
    WorkspaceMemberInviteModal,
    SidebarSearch,
  },
  props: {
    selectedWorkspace: {
      type: Object,
      required: true,
    },
    rightSidebarOpen: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    sidebarWorkspaceComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .flatMap((plugin) =>
          plugin.getSidebarWorkspaceComponents(this.selectedWorkspace)
        )
        .filter((component) => component !== null)
    },
  },
  methods: {
    openWorkspaceSearch() {
      this.$emit('open-workspace-search')
    },

    handleInvite(event) {
      if (this.$route.name !== 'settings-invites') {
        this.$router.push({
          name: 'settings-invites',
          params: {
            workspaceId: this.selectedWorkspace.id,
          },
        })
      }
    },
  },
}
</script>
