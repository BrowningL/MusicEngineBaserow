<template>
  <Context
    ref="context"
    :overflow-scroll="true"
    :max-height-if-outside-viewport="true"
  >
    <div class="context__menu-title">
      {{ application.name }}
    </div>
    <!-- ISRCAnalytics: Hide context actions in global read-only mode -->
    <ul v-if="!isWorkspaceReadOnly" class="context__menu">
      <li
        v-for="(component, index) in additionalContextComponents"
        :key="index"
        class="context__menu-item"
        @click="$refs.context.hide()"
      >
        <component :is="component" :application="application"></component>
      </li>

      <slot name="additional-context-items"></slot>

      <li
        v-if="
          $hasPermission(
            'application.update',
            application,
            application.workspace.id
          )
        "
        class="context__menu-item"
      >
        <a class="context__menu-item-link" @click="handleRename()">
          <i class="context__menu-item-icon iconoir-edit-pencil"></i>
          {{
            $t('sidebarApplication.rename', {
              type: application._.type.name.toLowerCase(),
            })
          }}
        </a>
      </li>
      <li
        v-if="
          $hasPermission(
            'application.duplicate',
            application,
            application.workspace.id
          )
        "
        class="context__menu-item"
      >
        <SidebarDuplicateApplicationContextItem
          :application="application"
          :disabled="deleting"
          @click="$refs.context.hide()"
        ></SidebarDuplicateApplicationContextItem>
      </li>
      <!-- ISRCAnalytics: Removed Snapshots menu item -->
      <li
        v-if="
          applicationType.supportsTrash() &&
          $hasPermission(
            'application.read_trash',
            application,
            application.workspace.id
          )
        "
        class="context__menu-item"
      >
        <a class="context__menu-item-link" @click="showApplicationTrashModal">
          <i class="context__menu-item-icon iconoir-refresh-double"></i>
          {{ $t('sidebarApplication.viewTrash') }}
        </a>
      </li>
      <li
        v-if="
          $hasPermission(
            'application.delete',
            application,
            application.workspace.id
          )
        "
        class="context__menu-item context__menu-item--with-separator"
      >
        <a
          class="context__menu-item-link context__menu-item-link--delete"
          :class="{ 'context__menu-item-link--loading': deleting }"
          @click="deleteApplication()"
        >
          <i class="context__menu-item-icon iconoir-bin"></i>
          {{
            $t('sidebarApplication.delete', {
              type: application._.type.name.toLowerCase(),
            })
          }}
        </a>
      </li>
    </ul>
    <!-- ISRCAnalytics: Show read-only notice -->
    <div v-else class="context__menu-item context__menu-item--disabled" style="padding: 12px; color: #666; font-size: 12px;">
      <i class="iconoir-lock" style="margin-right: 8px;"></i>
      This workspace is read-only.
    </div>

    <TrashModal
      ref="applicationTrashModal"
      :initial-workspace="workspace"
      :initial-application="application"
    >
    </TrashModal>
  </Context>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import TrashModal from '@baserow/modules/core/components/trash/TrashModal'
import SidebarDuplicateApplicationContextItem from '@baserow/modules/core/components/sidebar/SidebarDuplicateApplicationContextItem.vue'
import applicationContext from '@baserow/modules/core/mixins/applicationContext'

export default {
  components: {
    TrashModal,
    SidebarDuplicateApplicationContextItem,
  },
  mixins: [applicationContext],
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
      deleting: false,
    }
  },
  computed: {
    isWorkspaceReadOnly() {
      return true
    },
    additionalContextComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .reduce(
          (components, plugin) =>
            components.concat(
              plugin.getAdditionalApplicationContextComponents(
                this.workspace,
                this.application
              )
            ),
          []
        )
        .filter((component) => component !== null)
    },
    applicationType() {
      return this.$registry.get('application', this.application.type)
    },
  },
  methods: {
    setLoading(application, value) {
      this.$store.dispatch('application/setItemLoading', {
        application,
        value,
      })
    },
    async deleteApplication() {
      if (this.deleting) {
        return
      }

      this.deleting = true

      try {
        await this.$store.dispatch('application/delete', this.application)
        await this.$store.dispatch('toast/restore', {
          trash_item_type: 'application',
          trash_item_id: this.application.id,
        })
      } catch (error) {
        notifyIf(error, 'application')
      }

      this.deleting = false
    },
    showApplicationTrashModal() {
      this.$refs.context.hide()
      this.$refs.applicationTrashModal.show()
    },
    handleRename() {
      this.$refs.context.hide()
      this.$parent.$emit('rename')
    },
  },
}
</script>
