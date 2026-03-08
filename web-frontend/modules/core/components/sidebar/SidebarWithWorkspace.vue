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
            <template v-if="applicationGroup.applications.length > 0">
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
                  v-for="(application, index) in sortedApplications(applicationGroup.applications)"
                >
                  <component
                    :is="getApplicationComponent(application)"
                    :key="application.id"
                    v-sortable="{
                      id: application.id,
                      update: orderApplications,
                      handle: '[data-sortable-handle]',
                      marginTop: -1.5,
                      enabled: false,
                    }"
                    :application="application"
                    :pending-jobs="pendingJobs[application.type]"
                    :workspace="selectedWorkspace"
                  ></component>
                  <!-- MusicEngine: Arrow separators between the managed databases -->
                  <div
                    v-if="shouldShowWorkflowArrow(application, index, applicationGroup.applications)"
                    :key="'arrow-' + application.id"
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
        return {
          name: applicationType.getNamePlural(),
          type: applicationType.getType(),
          developmentStage: applicationType.developmentStage,
          applications: this.applications
            .filter((application) => {
              return (
                application.workspace.id === this.selectedWorkspace.id &&
                application.type === applicationType.getType() &&
                applicationType.isVisible(application)
              )
            })
            .sort((a, b) => a.order - b.order),
        }
      })
      return applicationTypes
    },
    applicationsCount() {
      return this.groupedApplicationsForSelectedWorkspace.reduce(
        (acc, group) => acc + group.applications.length,
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
    getPendingJobComponent(job) {
      return this.$registry.get('job', job.type).getSidebarComponent()
    },
    /**
     * MusicEngine: Sort the managed databases into the intended workflow order.
     */
    sortedApplications(applications) {
      return [...applications].sort((a, b) => {
        const rankA = this.getManagedDatabaseRank(a.name)
        const rankB = this.getManagedDatabaseRank(b.name)

        if (rankA !== rankB) return rankA - rankB

        return a.order - b.order
      })
    },
    /**
     * MusicEngine: Show arrows between Distribution Management, Production Pipeline,
     * and Live Catalogue when those databases appear consecutively.
     */
    shouldShowWorkflowArrow(application, index, applications) {
      const sorted = this.sortedApplications(applications)
      const currentRank = this.getManagedDatabaseRank(application.name)
      const nextApp = sorted[index + 1]

      return (
        currentRank < 2 &&
        nextApp &&
        this.getManagedDatabaseRank(nextApp.name) === currentRank + 1
      )
    },
    normalizeAppName(name) {
      return (name || '').trim().toLowerCase()
    },
    getManagedDatabaseRank(name) {
      const normalized = this.normalizeAppName(name)

      if (normalized === 'distribution management') {
        return 0
      }

      if (
        ['distribution pipeline', 'production pipeline', 'production catalogue'].includes(
          normalized
        )
      ) {
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
