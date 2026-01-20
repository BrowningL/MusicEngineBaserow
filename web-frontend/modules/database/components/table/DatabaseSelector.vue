<template>
  <div class="database-selector">
    <div class="database-selector__workspace">
      {{ workspaceName }}
    </div>
    <div class="database-selector__divider">/</div>
    <a
      ref="databaseLink"
      class="database-selector__database"
      @click="toggleDatabaseMenu"
    >
      <span class="database-selector__database-name">{{ database.name }}</span>
      <i class="iconoir-nav-arrow-down database-selector__database-arrow"></i>
    </a>
    <Context ref="databaseContext" overflow-scroll max-height-if-outside-viewport>
      <ul class="context__menu">
        <li
          v-for="app in databases"
          :key="app.id"
          class="context__menu-item"
        >
          <a
            class="context__menu-item-link"
            :class="{ 'context__menu-item-link--active': app.id === database.id }"
            @click="selectDatabase(app)"
          >
            <i class="context__menu-item-icon iconoir-db"></i>
            {{ app.name }}
          </a>
        </li>
      </ul>
    </Context>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'DatabaseSelector',
  props: {
    database: {
      type: Object,
      required: true,
    },
  },
  computed: {
    ...mapGetters({
      applications: 'application/getAll',
    }),
    workspaceName() {
      return this.database.workspace?.name || 'Workspace'
    },
    databases() {
      // Filter only database applications
      return this.applications.filter((app) => app.type === 'database')
    },
  },
  methods: {
    toggleDatabaseMenu() {
      this.$refs.databaseContext.toggle(
        this.$refs.databaseLink,
        'bottom',
        'left',
        0
      )
    },
    async selectDatabase(app) {
      this.$refs.databaseContext.hide()

      if (app.id === this.database.id) return

      // Navigate to the first table in the selected database
      const tables = app.tables || []
      if (tables.length > 0) {
        const firstTable = [...tables].sort((a, b) => a.order - b.order)[0]
        await this.$nuxt.$router.push({
          name: 'database-table',
          params: {
            databaseId: app.id,
            tableId: firstTable.id,
          },
        })
      }
    },
  },
}
</script>
