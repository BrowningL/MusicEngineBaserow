<template>
  <div class="table-tabs-bar">
    <div ref="scrollContainer" class="table-tabs-bar__scroll-container">
      <div class="table-tabs-bar__tabs">
        <a
          v-for="table in orderedTables"
          :key="table.id"
          class="table-tabs-bar__tab"
          :class="{
            'table-tabs-bar__tab--active': table.id === selectedTableId,
            'table-tabs-bar__tab--loading': loadingTableId === table.id,
          }"
          :href="resolveTableHref(table)"
          :title="table.name"
          @click.prevent="selectTable(table)"
          @contextmenu.prevent="openTableContext($event, table)"
        >
          <i v-if="table.data_sync" class="table-tabs-bar__tab-icon iconoir-data-transfer-down"></i>
          <!-- ISRCAnalytics: Show lock/unlock icons for managed tables -->
          <i v-if="isTableReadOnly(table)" class="table-tabs-bar__tab-icon iconoir-lock" style="margin-right: 4px; font-size: 14px; opacity: 0.7;"></i>
          <i v-else-if="!isTableReadOnly(table) && ['distribution management', 'distribution pipeline', 'production pipeline', 'production catalogue'].includes((database.name || '').trim().toLowerCase())" class="table-tabs-bar__tab-icon iconoir-unlock" style="margin-right: 4px; font-size: 14px; opacity: 0.7;"></i>
          <span class="table-tabs-bar__tab-name">{{ table.name }}</span>
        </a>
      </div>
    </div>

    <button
      v-if="canCreateTable"
      class="table-tabs-bar__add-btn"
      :title="$t('sidebar.createTable')"
      @click="$refs.createTableModal.show()"
    >
      <i class="iconoir-plus"></i>
    </button>

    <CreateTableModal ref="createTableModal" :database="database" />

    <!-- Context menu for table right-click -->
    <Context ref="tableContext" overflow-scroll max-height-if-outside-viewport>
      <div v-if="contextTable" class="context__menu-title">
        {{ contextTable.name }} ({{ contextTable.id }})
      </div>
      <ul v-if="contextTable" class="context__menu">
        <li
          v-if="
            $hasPermission(
              'database.table.run_export',
              contextTable,
              database.workspace.id
            )
          "
          class="context__menu-item"
        >
          <a class="context__menu-item-link" @click="exportTable()">
            <i class="context__menu-item-icon iconoir-share-ios"></i>
            {{ $t('sidebarItem.exportTable') }}
          </a>
        </li>
        <li
          v-if="
            !isTableReadOnly(contextTable) &&
            $hasPermission(
              'database.table.update',
              contextTable,
              database.workspace.id
            )
          "
          class="context__menu-item"
        >
          <a class="context__menu-item-link" @click="enableRename()">
            <i class="context__menu-item-icon iconoir-edit-pencil"></i>
            {{ $t('action.rename') }}
          </a>
        </li>
        <li
          v-if="
            !isTableReadOnly(contextTable) &&
            $hasPermission(
              'database.table.duplicate',
              contextTable,
              database.workspace.id
            )
          "
          class="context__menu-item"
        >
          <SidebarDuplicateTableContextItem
            :database="database"
            :table="contextTable"
            @click="$refs.tableContext.hide()"
          />
        </li>
        <li
          v-if="
            !isTableReadOnly(contextTable) &&
            $hasPermission(
              'database.table.delete',
              contextTable,
              database.workspace.id
            )
          "
          class="context__menu-item"
        >
          <a
            class="context__menu-item-link context__menu-item-link--delete"
            :class="{ 'context__menu-item-link--loading': deleteLoading }"
            @click="deleteTable()"
          >
            <i class="context__menu-item-icon iconoir-bin"></i>
            {{ $t('action.delete') }}
          </a>
        </li>
      </ul>
    </Context>

    <ExportTableModal
      ref="exportTableModal"
      :database="database"
      :table="contextTable"
    />
  </div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import CreateTableModal from '@baserow/modules/database/components/table/CreateTableModal'
import SidebarDuplicateTableContextItem from '@baserow/modules/database/components/sidebar/table/SidebarDuplicateTableContextItem'
import ExportTableModal from '@baserow/modules/database/components/export/ExportTableModal'

export default {
  name: 'TableTabsBar',
  components: {
    CreateTableModal,
    SidebarDuplicateTableContextItem,
    ExportTableModal,
  },
  props: {
    database: {
      type: Object,
      required: true,
    },
    tables: {
      type: Array,
      required: true,
    },
    selectedTableId: {
      type: Number,
      required: false,
      default: null,
    },
    readOnly: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      loadingTableId: null,
      contextTable: null,
      deleteLoading: false,
    }
  },
  computed: {
    orderedTables() {
      return [...this.tables].sort((a, b) => a.order - b.order)
    },
    canCreateTable() {
      // ISRCAnalytics: Custom logic to disable table creation on read-only databases
      const dbName = (this.database?.name || '').trim().toLowerCase()
      if (dbName === 'live catalogue' || ['distribution management', 'distribution pipeline', 'production pipeline', 'production catalogue'].includes(dbName)) {
        return false
      }

      return (
        !this.readOnly &&
        this.$hasPermission(
          'database.create_table',
          this.database,
          this.database.workspace.id
        )
      )
    },
    isTableReadOnly() {
      return (table) => {
        const dbName = (this.database?.name || '').trim().toLowerCase()
        const tableName = (table?.name || '').trim().toLowerCase()

        if (dbName === 'live catalogue') return true

        if (dbName === 'distribution management') {
          const readOnlyTables = [
            'browser profiles',
            'distribution platforms',
          ]
          if (readOnlyTables.includes(tableName)) return true
        }

        if (['distribution pipeline', 'production pipeline', 'production catalogue'].includes(dbName)) {
          const readOnlyTables = dbName === 'production pipeline'
            ? ['uploads', 'tracks', 'artists']
            : [
            'browser profiles',
            'uploads',
            'tracks',
            'artists',
            'distribution platforms',
          ]
          if (readOnlyTables.includes(tableName)) return true
        }

        return this.readOnly
      }
    },
  },
  watch: {
    selectedTableId() {
      this.$nextTick(() => {
        this.scrollToActiveTab()
      })
    },
  },
  mounted() {
    this.scrollToActiveTab()
  },
  methods: {
    scrollToActiveTab() {
      const container = this.$refs.scrollContainer
      if (!container) return

      const activeTab = container.querySelector('.table-tabs-bar__tab--active')
      if (!activeTab) return

      const containerRect = container.getBoundingClientRect()
      const tabRect = activeTab.getBoundingClientRect()

      if (tabRect.left < containerRect.left) {
        container.scrollLeft -= containerRect.left - tabRect.left + 16
      } else if (tabRect.right > containerRect.right) {
        container.scrollLeft += tabRect.right - containerRect.right + 16
      }
    },
    resolveTableHref(table) {
      const props = this.$nuxt.$router.resolve({
        name: 'database-table',
        params: {
          databaseId: this.database.id,
          tableId: table.id,
        },
      })
      return props.href
    },
    async selectTable(table) {
      if (table.id === this.selectedTableId) return

      this.loadingTableId = table.id

      try {
        await this.$nuxt.$router.push({
          name: 'database-table',
          params: {
            databaseId: this.database.id,
            tableId: table.id,
          },
        })
      } finally {
        this.loadingTableId = null
      }
    },
    openTableContext(event, table) {
      this.contextTable = table
      this.$refs.tableContext.toggle(event.currentTarget, 'bottom', 'left', 0)
    },
    exportTable() {
      this.$refs.tableContext.hide()
      this.$refs.exportTableModal.show()
    },
    enableRename() {
      this.$refs.tableContext.hide()
      // Emit event for parent to handle rename
      this.$emit('rename-table', this.contextTable)
    },
    async deleteTable() {
      if (!this.contextTable) return

      this.deleteLoading = true

      try {
        await this.$store.dispatch('table/delete', {
          database: this.database,
          table: this.contextTable,
        })
        await this.$store.dispatch('toast/restore', {
          trash_item_type: 'table',
          trash_item_id: this.contextTable.id,
        })
      } catch (error) {
        notifyIf(error, 'table')
      }

      this.deleteLoading = false
      this.$refs.tableContext.hide()
    },
  },
}
</script>
