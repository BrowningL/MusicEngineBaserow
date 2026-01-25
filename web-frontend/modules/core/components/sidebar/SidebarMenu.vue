<template>
  <div class="sidebar__section" ph-autocapture="sidebar" data-highlight="menu">
    <ul class="tree">
      <!-- ISRCAnalytics: Removed SidebarSearch and Home link -->

      <li class="tree__item">
        <div class="tree__action tree__action--has-counter">
          <a
            class="tree__link"
            @click="$refs.notificationPanel.toggle($event.currentTarget)"
          >
            <i class="tree__icon tree__icon--type iconoir-bell"></i>
            <span class="tree__link-text">{{
              $t('sidebar.notifications')
            }}</span>
          </a>
          <BadgeCounter
            v-show="unreadNotificationCount"
            class="tree__counter"
            :count="unreadNotificationCount"
            :limit="10"
          >
          </BadgeCounter>
        </div>
        <NotificationPanel ref="notificationPanel" />
      </li>

      <!-- ISRCAnalytics: Removed Members and Invite Others links -->
      <component
        :is="component"
        v-for="(component, index) in sidebarWorkspaceComponents"
        :key="'sidebarWorkspaceComponents' + index"
        :workspace="selectedWorkspace"
        :right-sidebar-open="rightSidebarOpen"
      ></component>
      <!-- ISRCAnalytics: Removed Trash item -->
    </ul>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import TrashModal from '@baserow/modules/core/components/trash/TrashModal'
import NotificationPanel from '@baserow/modules/core/components/NotificationPanel'
import WorkspaceMemberInviteModal from '@baserow/modules/core/components/workspace/WorkspaceMemberInviteModal'
import BadgeCounter from '@baserow/modules/core/components/BadgeCounter'
import SidebarSearch from '@baserow/modules/core/components/sidebar/SidebarSearch'

export default {
  name: 'SidebarMenu',
  components: {
    TrashModal,
    NotificationPanel,
    WorkspaceMemberInviteModal,
    BadgeCounter,
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
    ...mapGetters({
      unreadNotificationCount: 'notification/getUnreadCount',
    }),
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
