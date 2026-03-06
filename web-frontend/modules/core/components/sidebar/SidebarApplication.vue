<template>
  <li
    class="tree__item"
    :class="{
      'tree__item--loading': application._.loading,
    }"
  >
    <div
      class="tree__action tree__action--has-options"
      :class="{
        'tree__action--highlighted': highlighted,
        'tree__action--no-hover': isManagedDatabase,
        'tree__action--always-show-options': isManagedDatabase
      }"
      data-sortable-handle
      :data-highlight="`sidebar-application-${application.id}`"
      @mousedown="handleMousedown"
    >
      <a
        class="tree__link"
        :class="{
          'tree__link--empty': application.name === '',
          'tree__link--disabled': isManagedDatabase
        }"
        :title="application.name"
        :aria-label="application.name"
        @click="handleClick"
      >
        <i class="tree__icon" :class="iconClass"></i>
        <span class="tree__link-text">
          <template v-if="application.name === ''">&nbsp;</template>
          <Editable
            ref="rename"
            :value="application.name"
            @change="renameApplication(application, $event)"
          ></Editable>
        </span>
      </a>

      <a
        ref="contextLink"
        class="tree__options"
        @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 0)"
        @mousedown.stop
      >
        <i class="baserow-icon-more-vertical"></i>
      </a>

      <component
        :is="getApplicationContextComponent(application)"
        ref="context"
        :application="application"
        :workspace="workspace"
        @rename="handleRenameApplication()"
      ></component>

      <TrashModal
        ref="applicationTrashModal"
        :initial-workspace="workspace"
        :initial-application="application"
      >
      </TrashModal>
    </div>
    <slot name="body"></slot>
  </li>
</template>

<script>
import SidebarDuplicateApplicationContextItem from '@baserow/modules/core/components/sidebar/SidebarDuplicateApplicationContextItem.vue'
import TrashModal from '@baserow/modules/core/components/trash/TrashModal'
import SnapshotsModal from '@baserow/modules/core/components/snapshots/SnapshotsModal'
import application from '@baserow/modules/core/mixins/application'

export default {
  name: 'SidebarApplication',
  components: {
    TrashModal,
    SidebarDuplicateApplicationContextItem,
    SnapshotsModal,
  },
  mixins: [application],
  props: {
    application: {
      type: Object,
      required: true,
    },
    workspace: {
      type: Object,
      required: true,
    },
    highlighted: {
      type: Boolean,
      default: false,
    },
    customIconClass: {
      type: String,
      default: null,
    },
    // MusicEngine: Disable clicking for managed databases
    isManagedDatabase: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      deleting: false,
    }
  },
  computed: {
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
    iconClass() {
      return this.customIconClass || this.application._.type.iconClass
    },
  },
  methods: {
    // MusicEngine: Stop mousedown for managed databases to prevent sortable pixel shift
    handleMousedown(event) {
      if (this.isManagedDatabase) {
        event.stopPropagation()
        event.preventDefault()
      }
    },
    // MusicEngine: Proper click handler that does nothing for managed databases
    handleClick() {
      if (!this.isManagedDatabase) {
        this.$emit('selected', this.application)
      }
      // Do nothing for managed databases - no event, no action
    },
  },
}
</script>

<style lang="scss" scoped>
/* MusicEngine: Disabled link style for managed databases */
.tree__link--disabled {
  cursor: default;
  pointer-events: none;  /* Completely prevents click events */

  &:hover {
    background-color: transparent;
  }
}

/* MusicEngine: Remove hover and ALL clicks for managed databases */
.tree__action--no-hover {
  pointer-events: none;  /* Disable clicks on entire row including sortable handle */

  &:hover {
    background-color: transparent !important;
  }
}

/* MusicEngine: Always show three dots and re-enable clicks on them */
.tree__action--always-show-options :deep(.tree__options) {
  display: flex;
  pointer-events: auto;  /* Re-enable clicks on three dots only */
}
</style>
