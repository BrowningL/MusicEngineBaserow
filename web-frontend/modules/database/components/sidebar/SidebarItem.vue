<template>
  <li class="tree__sub" :class="{ active: table._.selected }">
    <a
      class="tree__sub-link"
      :class="{ 'tree__sub-link--empty': table.name === '' }"
      :title="table.name"
      :href="resolveTableHref(database, table)"
      @mousedown.prevent
      @click.prevent="selectTable(database, table)"
    >
      <span
        class="sidebar-table-icon-wrap"
        :class="[tableToneClass, { 'sidebar-table-icon-wrap--readonly': isTableReadOnly }]"
      >
        <i class="sidebar-table-icon" :class="tableIconClass"></i>
        <span v-if="isTableReadOnly" class="sidebar-table-icon__badge">
          <i class="iconoir-lock"></i>
        </span>
      </span>
      <i
        v-if="table.data_sync"
        v-tooltip:[syncTooltipOptions]="
          `${$t('sidebarItem.lastSynced')}: ${lastSyncedDate}`
        "
        class="iconoir-data-transfer-down sidebar-table-sync-icon"
      ></i>
      <Editable
        ref="rename"
        :value="table.name"
        @change="renameTable(database, table, $event)"
      ></Editable>
    </a>

    <a
      v-if="showOptions"
      v-show="!database._.loading"
      class="tree__options"
      @click="$refs.context.toggle($event.currentTarget, 'bottom', 'right', 0)"
      @mousedown.stop
    >
      <i class="baserow-icon-more-vertical"></i>
    </a>

    <Context ref="context" overflow-scroll max-height-if-outside-viewport>
      <div class="context__menu-title">{{ table.name }}</div>
      <ul class="context__menu">
        <li
          v-for="(component, index) in additionalContextComponents"
          :key="index"
          class="context__menu-item"
          @click="$refs.context.hide()"
        >
          <component
            :is="component"
            :table="table"
            :database="database"
          ></component>
        </li>
        <li
          v-if="
            $hasPermission(
              'database.table.run_export',
              table,
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
        <!-- ISRCAnalytics: Removed webhooks menu item -->
        <li
          v-if="
            !isTableReadOnly &&
            table.data_sync &&
            $hasPermission(
              'database.data_sync.sync_table',
              table,
              database.workspace.id
            )
          "
          class="context__menu-item"
        >
          <a class="context__menu-item-link" @click="openSyncModal()">
            <i class="context__menu-item-icon iconoir-data-transfer-down"></i>
            {{ $t('sidebarItem.sync') }}
            <div v-if="dataSyncDeactivated" class="deactivated-label">
              <i class="iconoir-lock"></i>
            </div>
          </a>
          <component
            :is="dataSyncDeactivatedClickModal[0]"
            v-if="dataSyncDeactivatedClickModal !== null"
            ref="deactivatedDataSyncClickModal"
            v-bind="dataSyncDeactivatedClickModal[1]"
            :workspace="database.workspace"
            :name="dataSyncType.getName()"
          ></component>
        </li>
        <li
          v-if="
            !isTableReadOnly &&
            table.data_sync &&
            $hasPermission(
              'database.table.update',
              table,
              database.workspace.id
            ) &&
            $hasPermission(
              'database.data_sync.get',
              table,
              database.workspace.id
            )
          "
          class="context__menu-item"
        >
          <a
            class="context__menu-item-link"
            @click="openConfigureDataSyncModal()"
          >
            <i class="context__menu-item-icon iconoir-settings"></i>
            {{ $t('sidebarItem.updateSyncConfig') }}
            <div v-if="dataSyncDeactivated" class="deactivated-label">
              <i class="iconoir-lock"></i>
            </div>
          </a>
          <ConfigureDataSyncModal
            ref="configureDataSyncModal"
            :database="database"
            :table="table"
          ></ConfigureDataSyncModal>
        </li>
        <!-- ISRCAnalytics: Hide rename for managed databases -->
        <li
          v-if="
            !isTableReadOnly &&
            $hasPermission(
              'database.table.update',
              table,
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
        <!-- ISRCAnalytics: Hide duplicate for managed databases -->
        <li
          v-if="
            !isTableReadOnly &&
            $hasPermission(
              'database.table.duplicate',
              table,
              database.workspace.id
            )
          "
          class="context__menu-item"
        >
          <SidebarDuplicateTableContextItem
            :database="database"
            :table="table"
            :disabled="deleteLoading"
            @click="$refs.context.hide()"
          ></SidebarDuplicateTableContextItem>
        </li>
        <!-- ISRCAnalytics: Hide delete for managed databases -->
        <li
          v-if="
            !isTableReadOnly &&
            $hasPermission(
              'database.table.delete',
              table,
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
      <ExportTableModal
        ref="exportTableModal"
        :database="database"
        :table="table"
      />
      <WebhookModal ref="webhookModal" :database="database" :table="table" />
      <SyncTableModal ref="syncModal" :table="table"></SyncTableModal>
    </Context>
  </li>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import { getHumanPeriodAgoCount } from '@baserow/modules/core/utils/date'
import ExportTableModal from '@baserow/modules/database/components/export/ExportTableModal'
import WebhookModal from '@baserow/modules/database/components/webhook/WebhookModal'
import SidebarDuplicateTableContextItem from '@baserow/modules/database/components/sidebar/table/SidebarDuplicateTableContextItem'
import SyncTableModal from '@baserow/modules/database/components/dataSync/SyncTableModal'
import ConfigureDataSyncModal from '@baserow/modules/database/components/dataSync/ConfigureDataSyncModal.vue'

export default {
  name: 'SidebarItem',
  components: {
    ConfigureDataSyncModal,
    ExportTableModal,
    WebhookModal,
    SyncTableModal,
    SidebarDuplicateTableContextItem,
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
  },
  data() {
    return {
      deleteLoading: false,
    }
  },
  computed: {
    normalizedDatabaseName() {
      return (this.database.name || '').trim().toLowerCase()
    },
    tableIconClass() {
      const tableName = (this.table?.name || '').trim().toLowerCase()
      const iconMap = {
        artists: 'iconoir-user',
        'production workspace': 'iconoir-app-window',
        releases: 'iconoir-multiple-pages-empty',
        tracks: 'iconoir-music-double-note',
        uploads: 'iconoir-cloud-upload',
        'distributor accounts': 'iconoir-community',
        'distribution platforms': 'iconoir-globe',
        'browser profiles': 'iconoir-fingerprint',
        playlists: 'iconoir-playlist',
      }

      return iconMap[tableName] || 'iconoir-table'
    },
    tableToneClass() {
      const dbName = this.normalizedDatabaseName

      if (!this.isManagedDatabase) {
        return 'sidebar-table-icon-wrap--default'
      }

      if (dbName === 'distribution management') {
        return 'sidebar-table-icon-wrap--distribution'
      }

      if (dbName === 'live catalogue') {
        return 'sidebar-table-icon-wrap--catalogue'
      }

      return 'sidebar-table-icon-wrap--production'
    },
    /**
     * ISRCAnalytics: Check if this table is in a managed database.
     */
    isManagedDatabase() {
      const dbName = this.normalizedDatabaseName
      return ['live catalogue', 'distribution management', 'catalog pipeline', 'distribution pipeline', 'production pipeline', 'production catalogue'].includes(dbName)
    },
    isTableReadOnly() {
      const dbName = this.normalizedDatabaseName
      const tableName = (this.table?.name || '').trim().toLowerCase()

      if (dbName === 'live catalogue') return true

      if (dbName === 'distribution management') {
        const readOnlyTables = [
          'browser profiles',
          'distribution platforms',
        ]
        if (readOnlyTables.includes(tableName)) return true
      }

      if (['distribution pipeline', 'production catalogue'].includes(dbName)) {
        const readOnlyTables = [
          'browser profiles',
          'uploads',
          'tracks',
          'artists',
          'distribution platforms',
        ]
        if (readOnlyTables.includes(tableName)) return true
      }

      if (['production pipeline', 'catalog pipeline'].includes(dbName)) {
        const readOnlyTables = ['uploads', 'tracks', 'artists']
        if (readOnlyTables.includes(tableName)) return true
      }

      return false
    },
    showOptions() {
      // ISRCAnalytics: Show options for managed databases (only export visible)
      if (this.isTableReadOnly) {
        return this.$hasPermission(
          'database.table.run_export',
          this.table,
          this.database.workspace.id
        )
      }
      return (
        this.$hasPermission(
          'database.table.run_export',
          this.table,
          this.database.workspace.id
        ) ||
        this.$hasPermission(
          'database.table.create_webhook',
          this.table,
          this.database.workspace.id
        ) ||
        this.$hasPermission(
          'database.table.update',
          this.table,
          this.database.workspace.id
        ) ||
        this.$hasPermission(
          'database.table.duplicate',
          this.table,
          this.database.workspace.id
        )
      )
    },
    additionalContextComponents() {
      if (this.isManagedDatabase) {
        return []
      }
      return Object.values(this.$registry.getAll('plugin'))
        .reduce(
          (components, plugin) =>
            components.concat(
              plugin.getAdditionalTableContextComponents(
                this.database.workspace,
                this.table
              )
            ),
          []
        )
        .filter((component) => component !== null)
    },
    syncTooltipOptions() {
      return {
        contentClasses: ['tooltip__content--align-right'],
      }
    },
    lastSyncedDate() {
      if (!this.table.data_sync || !this.table.data_sync.last_sync) {
        return this.$t('sidebarItem.notSynced')
      }
      const { period, count } = getHumanPeriodAgoCount(
        this.table.data_sync.last_sync
      )
      return this.$tc(`datetime.${period}Ago`, count)
    },
    dataSyncType() {
      return this.$registry.get('dataSync', this.table.data_sync.type)
    },
    dataSyncDeactivated() {
      return this.dataSyncType.isDeactivated(this.database.workspace.id)
    },
    dataSyncDeactivatedClickModal() {
      return this.dataSyncType.getDeactivatedClickModal()
    },
  },
  methods: {
    setLoading(database, value) {
      this.$store.dispatch('application/setItemLoading', {
        application: database,
        value,
      })
    },
    async selectTable(database, table) {
      this.setLoading(database, true)

      try {
        await this.$nuxt.$router.push({
          name: 'database-table',
          params: {
            databaseId: database.id,
            tableId: table.id,
          },
        })
      } finally {
        this.setLoading(database, false)
      }
    },
    exportTable() {
      this.$refs.context.hide()
      this.$refs.exportTableModal.show()
    },
    openWebhookModal() {
      this.$refs.context.hide()
      this.$refs.webhookModal.show()
    },
    openSyncModal() {
      if (this.dataSyncDeactivated) {
        this.$refs.deactivatedDataSyncClickModal.show()
      } else {
        this.$refs.context.hide()
        this.$refs.syncModal.show()
      }
    },
    openConfigureDataSyncModal() {
      if (this.dataSyncDeactivated) {
        this.$refs.deactivatedDataSyncClickModal.show()
      } else {
        this.$refs.context.hide()
        this.$refs.configureDataSyncModal.show()
      }
    },
    enableRename() {
      this.$refs.context.hide()
      this.$refs.rename.edit()
    },
    async renameTable(database, table, event) {
      this.setLoading(database, true)

      try {
        await this.$store.dispatch('table/update', {
          database,
          table,
          values: {
            name: event.value,
          },
        })
      } catch (error) {
        this.$refs.rename.set(event.oldValue)
        notifyIf(error, 'table')
      }

      this.setLoading(database, false)
    },
    async deleteTable() {
      this.deleteLoading = true

      try {
        await this.$store.dispatch('table/delete', {
          database: this.database,
          table: this.table,
        })
        await this.$store.dispatch('toast/restore', {
          trash_item_type: 'table',
          trash_item_id: this.table.id,
        })
      } catch (error) {
        notifyIf(error, 'table')
      }

      this.deleteLoading = false
    },
    resolveTableHref(database, table) {
      const props = this.$nuxt.$router.resolve({
        name: 'database-table',
        params: {
          databaseId: database.id,
          tableId: table.id,
        },
      })

      return props.href
    },
  },
}
</script>

<style lang="scss" scoped>
.sidebar-table-icon-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 6px;
  flex-shrink: 0;
  background: #111111;
  color: #ffffff;
  box-shadow: inset 0 0 0 1px rgba(17, 17, 17, 0.08);
}

.sidebar-table-icon-wrap--default {
  background: #f4f4f5;
  color: #4b5563;
  box-shadow: inset 0 0 0 1px rgba(17, 17, 17, 0.08);
}

.sidebar-table-icon-wrap--production {
  background: #111111;
  color: #ffffff;
  box-shadow: inset 0 0 0 1px #111111;
}

.sidebar-table-icon-wrap--distribution {
  background: #5190ef;
  color: #ffffff;
  box-shadow: inset 0 0 0 1px #5190ef;
}

.sidebar-table-icon-wrap--catalogue {
  background: #6b8e6b;
  color: #ffffff;
  box-shadow: inset 0 0 0 1px #1a472a;
}

.sidebar-table-icon-wrap--readonly {
  opacity: 0.88;
}

.sidebar-table-icon {
  font-size: 12px;
  line-height: 1;
}

.sidebar-table-icon__badge {
  position: absolute;
  right: -3px;
  bottom: -3px;
  width: 11px;
  height: 11px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary, #fff);
  color: var(--text-muted, #7d8591);
  box-shadow: 0 0 0 1px var(--bg-primary, #fff);
}

.sidebar-table-icon__badge i {
  font-size: 7px;
  line-height: 1;
}

.sidebar-table-sync-icon {
  color: var(--text-muted, #7d8591);
  font-size: 14px;
}
</style>
