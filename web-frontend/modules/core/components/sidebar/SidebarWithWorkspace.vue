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
                  <!-- MusicEngine: Arrow separator between Distribution Pipeline and Live Catalogue -->
                  <div
                    v-if="shouldShowPipelineArrow(application, index, applicationGroup.applications)"
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
     * MusicEngine: Sort databases so Distribution Pipeline comes before Live Catalogue.
     */
    sortedApplications(applications) {
      return [...applications].sort((a, b) => {
        // Distribution Pipeline (or Production Catalogue for legacy) should come first
        const isPipelineA = this.isPipelineApplication(a.name)
        const isPipelineB = this.isPipelineApplication(b.name)
        const isLiveCatalogueA = this.normalizeAppName(a.name) === 'live catalogue'
        const isLiveCatalogueB = this.normalizeAppName(b.name) === 'live catalogue'

        if (isPipelineA && !isPipelineB) return -1
        if (isPipelineB && !isPipelineA) return 1
        if (isLiveCatalogueA && !isLiveCatalogueB) return 1
        if (isLiveCatalogueB && !isLiveCatalogueA) return -1

        return a.order - b.order
      })
    },
    /**
     * MusicEngine: Show arrow between Distribution Pipeline and Live Catalogue.
     */
    shouldShowPipelineArrow(application, index, applications) {
      const sorted = this.sortedApplications(applications)
      const isPipeline = this.isPipelineApplication(application.name)
      const nextApp = sorted[index + 1]
      return (
        isPipeline &&
        nextApp &&
        this.normalizeAppName(nextApp.name) === 'live catalogue'
      )
    },
    normalizeAppName(name) {
      return (name || '').trim().toLowerCase()
    },
    isPipelineApplication(name) {
      return ['distribution pipeline', 'production pipeline', 'production catalogue'].includes(
        this.normalizeAppName(name)
      )
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
