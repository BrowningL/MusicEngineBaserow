<template>
  <div class="views-sidebar">
    <!-- Create new dropdown -->
    <div class="views-sidebar__header">
      <a
        ref="createLink"
        class="views-sidebar__create-link"
        @click="toggleCreateMenu"
      >
        <i class="iconoir-plus"></i>
        {{ $t('action.createNew') }}...
      </a>
      <Context ref="createContext" max-height-if-outside-viewport>
        <div class="views-sidebar__create-dropdown">
          <a
            v-for="viewType in availableViewTypes"
            :key="viewType.type"
            class="views-sidebar__create-item"
            @click="createView(viewType)"
          >
            <i :class="viewType.iconClass"></i>
            <div class="views-sidebar__create-item-info">
              <span class="views-sidebar__create-item-name">{{ viewType.getName() }}</span>
            </div>
          </a>
        </div>
      </Context>
    </div>

    <!-- Search -->
    <div class="views-sidebar__search">
      <i class="iconoir-search"></i>
      <input
        v-model="query"
        type="text"
        :placeholder="$t('viewsContext.searchView')"
      />
    </div>

    <!-- Loading state -->
    <div v-if="isLoading" class="context--loading">
      <div class="loading"></div>
    </div>

    <!-- Views list -->
    <div v-else class="views-sidebar__list">
      <template v-if="filteredViews.length > 0">
        <div
          v-for="type in activeViewOwnershipTypes"
          :key="type.getType()"
          class="views-sidebar__section"
        >
          <template v-if="viewsByOwnership(type.getType()).length > 0">
            <div
              v-if="activeViewOwnershipTypes.length > 1"
              class="views-sidebar__section-title"
            >
              {{ type.getName() }}
            </div>
            <ViewsSidebarItem
              v-for="view in viewsByOwnership(type.getType())"
              :key="view.id"
              :database="database"
              :view="view"
              :table="table"
              :read-only="readOnly"
              @selected="selectedView"
            />
          </template>
        </div>
      </template>

      <!-- Empty state -->
      <div v-else class="views-sidebar__empty">
        <i class="iconoir-view-grid"></i>
        <p>{{ $t('viewsContext.noViews') }}</p>
      </div>
    </div>

    <!-- Create view modal -->
    <CreateViewModal
      ref="createViewModal"
      :table="table"
      :database="database"
      :view-type="selectedViewType"
      @created="viewCreated"
    />
  </div>
</template>

<script>
import { mapState } from 'vuex'
import { escapeRegExp } from '@baserow/modules/core/utils/string'
import ViewsSidebarItem from '@baserow/modules/database/components/view/ViewsSidebarItem'
import CreateViewModal from '@baserow/modules/database/components/view/CreateViewModal'

export default {
  name: 'ViewsSidebar',
  components: {
    ViewsSidebarItem,
    CreateViewModal,
  },
  props: {
    database: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    views: {
      type: Array,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      query: '',
      selectedViewType: null,
    }
  },
  computed: {
    ...mapState({
      isLoading: (state) => state.view.loading,
    }),
    viewTypes() {
      return Object.values(this.$registry.getAll('view'))
    },
    availableViewTypes() {
      return this.viewTypes.filter((viewType) => {
        // Only show view types that are compatible with the table
        return viewType.isCompatibleWithDataSync(this.table.data_sync)
      })
    },
    viewOwnershipTypes() {
      return this.$registry.getAll('viewOwnershipType')
    },
    activeViewOwnershipTypes() {
      return Object.values(this.viewOwnershipTypes).sort(
        (a, b) => a.getListViewTypeSort() - b.getListViewTypeSort()
      )
    },
    filteredViews() {
      if (!this.query) {
        return this.views
      }
      const regex = new RegExp('(' + escapeRegExp(this.query) + ')', 'i')
      return this.views.filter((view) => view.name.match(regex))
    },
  },
  methods: {
    viewsByOwnership(ownershipType) {
      return this.filteredViews
        .filter((view) => view.ownership_type === ownershipType)
        .sort((a, b) => a.order - b.order)
    },
    toggleCreateMenu() {
      this.$refs.createContext.toggle(this.$refs.createLink, 'bottom', 'left', 0)
    },
    createView(viewType) {
      this.$refs.createContext.hide()
      this.selectedViewType = viewType
      this.$nextTick(() => {
        this.$refs.createViewModal.show()
      })
    },
    viewCreated(view) {
      this.$emit('view-created', view)
    },
    selectedView(view) {
      this.$emit('selected-view', view)
    },
  },
}
</script>
