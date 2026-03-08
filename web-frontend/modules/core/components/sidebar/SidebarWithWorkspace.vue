<template>
  <div class="sidebar__section sidebar__section--scrollable">
    <div v-if="hasItems" class="sidebar__section-scrollable">
      <div
        class="sidebar__section-scrollable-inner"
        data-highlight="applications"
      >
        <ul v-if="pendingJobs[null].length" class="tree">
          <component
            :is="getPendingJobComponent(job)"
            v-for="job in pendingJobs[null]"
            :key="job.id"
            :job="job"
          >
          </component>
        </ul>
        <ul v-if="applicationsCount" class="tree">
          <div
            v-for="applicationGroup in groupedApplicationsForSelectedWorkspace"
            :key="applicationGroup.type"
          >
            <template v-if="applicationGroup.sidebarEntries.length > 0">
              <!-- MusicEngine: Hide "Databases" heading to save space -->
              <div v-if="applicationGroup.name !== 'Databases'" class="tree__heading">
                {{ applicationGroup.name }}
              </div>
              <ul
                class="tree"
                :class="{
                  'margin-bottom-0': pendingJobs[applicationGroup.type].length,
                }"
                data-highlight="applications"
              >
                <template
                  v-for="(entry, index) in sortedApplications(applicationGroup.sidebarEntries)"
                >
                  <component
                    :is="getApplicationComponent(entry.application)"
                    :key="entry.key"
                    v-sortable="{
                      id: entry.sortableId,
                      update: orderApplications,
                      handle: '[data-sortable-handle]',
                      marginTop: -1.5,
                      enabled: false,
                    }"
                    :application="entry.application"
                    v-bind="getSidebarComponentProps(entry)"
                    :workspace="selectedWorkspace"
                  ></component>
                  <!-- MusicEngine: Arrow separators between the managed databases -->
                  <div
                    v-if="shouldShowWorkflowArrow(entry, index, applicationGroup.sidebarEntries)"
                    :key="'arrow-' + entry.key"
                    class="sidebar__pipeline-arrow"
                  >
                    <i class="iconoir-arrow-down"></i>
                  </div>
                </template>
              </ul>
              <ul v-if="pendingJobs[applicationGroup.type].length" class="tree">
                <component
                  :is="getPendingJobComponent(job)"
                  v-for="job in pendingJobs[applicationGroup.type]"
                  :key="job.id"
                  :job="job"
                >
                </component>
              </ul>
            </template>
          </div>
        </ul>
      </div>
    </div>
<!-- MusicEngine: Removed "Add new..." button and CreateApplicationContext -->
  </div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'SidebarWithWorkspace',
  components: {},
  props: {
    applications: {
      type: Array,
      required: true,
    },
    selectedWorkspace: {
      type: Object,
      required: true,
    },
  },
  computed: {
    /**
     * Because all the applications that belong to the user are in the store we will
     * filter on the selected workspace here.
     */
    groupedApplicationsForSelectedWorkspace() {
      const applicationTypes = Object.values(
        this.$registry.getAll('application')
      ).map((applicationType) => {
        const applications = this.applications
          .filter((application) => {
            return (
              application.workspace.id === this.selectedWorkspace.id &&
              application.type === applicationType.getType() &&
              applicationType.isVisible(application)
            )
          })
          .sort((a, b) => a.order - b.order)

        return {
          name: applicationType.getNamePlural(),
          type: applicationType.getType(),
          developmentStage: applicationType.developmentStage,
          applications,
          sidebarEntries: this.buildSidebarEntries(applications),
        }
      })
      return applicationTypes
    },
    applicationsCount() {
      return this.groupedApplicationsForSelectedWorkspace.reduce(
        (acc, group) => acc + group.sidebarEntries.length,
        0
      )
    },
    pendingJobs() {
      const grouped = { null: [] }
      Object.values(this.$registry.getAll('application')).forEach(
        (applicationType) => {
          grouped[applicationType.getType()] = []
        }
      )
      this.$store.getters['job/getAll'].forEach((job) => {
        const jobType = this.$registry.get('job', job.type)
        if (jobType.isJobPartOfWorkspace(job, this.selectedWorkspace)) {
          grouped[jobType.getSidebarApplicationTypeLocation(job)].push(job)
        }
      })
      return grouped
    },
    hasItems() {
      return this.applicationsCount || this.pendingJobs.null.length
    },
  },
  methods: {
    getApplicationComponent(application) {
      return this.$registry
        .get('application', application.type)
        .getSidebarComponent()
    },
    getSidebarComponentProps(entry) {
      if (entry.application.type !== 'database') {
        return {}
      }

      return {
        displayName: entry.displayName,
        visibleTableNames: entry.visibleTableNames,
        showPendingJobs: entry.showPendingJobs,
      }
    },
    getPendingJobComponent(job) {
      return this.$registry.get('job', job.type).getSidebarComponent()
    },
    buildSidebarEntries(applications) {
      const hasDedicatedDistributionManagement = applications.some(
        (application) =>
          this.normalizeAppName(application.name) === 'distribution management'
      )

      return applications.flatMap((application) => {
        if (
          application.type === 'database' &&
          !hasDedicatedDistributionManagement &&
          this.shouldSplitCombinedPipeline(application)
        ) {
          return [
            {
              key: `${application.id}-catalog-pipeline`,
              sortableId: `${application.id}-catalog-pipeline`,
              application,
              displayName: 'Catalogue Pipeline',
              visibleTableNames: [
                'Artists',
                'Production Workspace',
                'Releases',
                'Tracks',
                'Uploads',
              ],
              showPendingJobs: true,
            },
            {
              key: `${application.id}-distribution-management`,
              sortableId: `${application.id}-distribution-management`,
              application,
              displayName: 'Distribution Management',
              visibleTableNames: [
                'Distributor Accounts',
                'Distribution Platforms',
                'Browser Profiles',
              ],
              showPendingJobs: false,
            },
          ]
        }

        return [
          {
            key: `${application.id}`,
            sortableId: `${application.id}`,
            application,
            displayName: null,
            visibleTableNames: null,
            showPendingJobs: true,
          },
        ]
      })
    },
    shouldSplitCombinedPipeline(application) {
      const normalized = this.normalizeAppName(application.name)
      const isCombinedPipeline = [
        'distribution pipeline',
        'production pipeline',
        'production catalogue',
      ].includes(normalized)

      if (!isCombinedPipeline) {
        return false
      }

      const tableNames = (application.tables || []).map((table) =>
        this.normalizeAppName(table.name)
      )
      const hasDistributionManagementTables = [
        'distributor accounts',
        'distribution platforms',
        'browser profiles',
      ].some((tableName) => tableNames.includes(tableName))
      const hasCatalogPipelineTables = [
        'artists',
        'production workspace',
        'releases',
        'tracks',
        'uploads',
      ].some((tableName) => tableNames.includes(tableName))

      return hasDistributionManagementTables && hasCatalogPipelineTables
    },
    /**
     * MusicEngine: Sort the managed databases into the intended workflow order.
     */
    sortedApplications(entries) {
      return [...entries].sort((a, b) => {
        const rankA = this.getManagedDatabaseRank(this.getEntryName(a))
        const rankB = this.getManagedDatabaseRank(this.getEntryName(b))

        if (rankA !== rankB) return rankA - rankB

        return a.application.order - b.application.order
      })
    },
    /**
     * MusicEngine: Show arrows between Catalogue Pipeline,
     * Distribution Management, and Live Catalogue when those databases appear consecutively.
     */
    shouldShowWorkflowArrow(entry, index, entries) {
      const sorted = this.sortedApplications(entries)
      const currentRank = this.getManagedDatabaseRank(this.getEntryName(entry))
      const nextApp = sorted[index + 1]

      return (
        currentRank < 2 &&
        nextApp &&
        this.getManagedDatabaseRank(this.getEntryName(nextApp)) === currentRank + 1
      )
    },
    getEntryName(entry) {
      return entry.displayName || entry.application.name
    },
    normalizeAppName(name) {
      return (name || '').trim().toLowerCase()
    },
    getManagedDatabaseRank(name) {
      const normalized = this.normalizeAppName(name)

      if (
        ['catalog pipeline', 'distribution pipeline', 'production pipeline', 'production catalogue'].includes(
          normalized
        )
      ) {
        return 0
      }

      if (normalized === 'distribution management') {
        return 1
      }

      if (normalized === 'live catalogue') {
        return 2
      }

      return 3
    },
    async orderApplications(order, oldOrder) {
      try {
        await this.$store.dispatch('application/order', {
          workspace: this.selectedWorkspace,
          order,
          oldOrder,
        })
      } catch (error) {
        notifyIf(error, 'application')
      }
    },
  },
}
</script>
