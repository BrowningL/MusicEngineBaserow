<template>
  <div v-if="workspaceExists">
    <div class="dashboard__header" ph-autocapture="dashboard-header">
      <div class="dashboard__header-left">
        <h1
          ref="contextLink"
          class="dashboard__workspace-name"
          @click="
            $refs.context.toggle($refs.contextLink, 'bottom', 'left', -14)
          "
        >
          <div class="dashboard__workspace-name-text">
            <Editable
              ref="rename"
              :value="selectedWorkspace.name"
              @change="renameWorkspace(selectedWorkspace, $event)"
            ></Editable>
          </div>
          <i class="dashboard__workspace-name-icon iconoir-nav-arrow-down"></i>
        </h1>
        <component
          :is="component"
          v-for="(component, index) in dashboardWorkspacePlanBadge"
          :key="index"
          :workspace="selectedWorkspace"
          :component-arguments="workspaceComponentArguments"
        ></component>
      </div>
      <WorkspaceContext
        ref="context"
        :workspace="selectedWorkspace"
        @rename="enableRename()"
      ></WorkspaceContext>
      <div class="dashboard__header-right">
        <component
          :is="component"
          v-for="(component, index) in dashboardWorkspaceRowUsageComponent"
          :key="index"
          :workspace="selectedWorkspace"
          :component-arguments="workspaceComponentArguments"
          @workspace-updated="workspaceUpdated($event)"
        ></component>
        <span
          v-if="canCreateCreateApplication"
          ref="createApplicationContextLink"
        >
          <Button
            icon="iconoir-plus"
            tag="a"
            @click="
              $refs.createApplicationContext.toggle(
                $refs.createApplicationContextLink
              )
            "
            >{{ $t('dashboard.addNew') }}</Button
          >
        </span>
      </div>
    </div>
    <div
      class="dashboard__scroll-container"
      ph-autocapture="dashboard-container"
    >
      <div class="dashboard__main">
        <DashboardVerifyEmail
          class="margin-top-0 margin-bottom-0"
        ></DashboardVerifyEmail>
        <WorkspaceInvitation
          v-for="invitation in workspaceInvitations"
          :key="'invitation-' + invitation.id"
          :invitation="invitation"
          class="margin-top-0 margin-bottom-0"
        ></WorkspaceInvitation>
        <!-- MusicEngine: Removed suggested templates and resources sections -->
        <div class="dashboard__wrapper">
          <ul
            v-if="orderedApplicationsInSelectedWorkspace.length"
            class="dashboard__applications"
          >
            <template
              v-for="application in orderedApplicationsInSelectedWorkspace"
            >
              <li
                v-if="getApplicationType(application).isVisible(application)"
                :key="application.id"
              >
                <DashboardApplication
                  :application="application"
                  :workspace="selectedWorkspace"
                  @click="selectApplication(application)"
                />
                <div class="dashboard__application-separator"></div></li
            ></template>
          </ul>
          <div v-else class="dashboard__no-application">
            <img
              src="@baserow/modules/core/assets/images/empty_workspace_illustration.png"
              srcset="
                @baserow/modules/core/assets/images/empty_workspace_illustration@2x.png 2x
              "
            />
            <h4>{{ $t('dashboard.emptyWorkspace') }}</h4>
            <p v-if="canCreateCreateApplication">
              {{ $t('dashboard.emptyWorkspaceMessage') }}
            </p>
            <span
              v-if="canCreateCreateApplication"
              ref="createApplicationContextLink2"
            >
              <Button
                icon="iconoir-plus"
                tag="a"
                @click="
                  $refs.createApplicationContext.toggle(
                    $refs.createApplicationContextLink2
                  )
                "
                >{{ $t('dashboard.addNew') }}</Button
              >
            </span>
          </div>
        </div>
      </div>
      <CreateApplicationContext
        ref="createApplicationContext"
        :workspace="selectedWorkspace"
      ></CreateApplicationContext>
    </div>
    <DashboardHelp v-if="dashboardHelpComponents.length === 0"></DashboardHelp>
    <template v-else>
      <component
        :is="component"
        v-for="(component, index) in dashboardHelpComponents"
        :key="index"
      ></component>
    </template>
    <TemplateModal
      ref="templateModal"
      :workspace="selectedWorkspace"
    ></TemplateModal>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import WorkspaceContext from '@baserow/modules/core/components/workspace/WorkspaceContext'
import CreateApplicationContext from '@baserow/modules/core/components/application/CreateApplicationContext'
import DashboardApplication from '@baserow/modules/core/components/dashboard/DashboardApplication'
import WorkspaceInvitation from '@baserow/modules/core/components/workspace/WorkspaceInvitation'
import TemplateCard from '@baserow/modules/core/components/template/TemplateCard'
import editWorkspace from '@baserow/modules/core/mixins/editWorkspace'
import DashboardVerifyEmail from '@baserow/modules/core/components/dashboard/DashboardVerifyEmail'
import TemplateModal from '@baserow/modules/core/components/template/TemplateModal'
import DashboardHelp from '@baserow/modules/core/components/dashboard/DashboardHelp'

export default {
  components: {
    WorkspaceContext,
    CreateApplicationContext,
    DashboardApplication,
    WorkspaceInvitation,
    TemplateCard,
    DashboardVerifyEmail,
    TemplateModal,
    DashboardHelp,
  },
  mixins: [editWorkspace],
  layout: 'app',
  /**
   * Fetches the data that must be shown on the dashboard, this could for example be
   * pending workspace invitations.
   */

  async asyncData(context) {
    const { error, app, store, params, redirect } = context
    let workspace = null

    try {
      workspace = await store.dispatch(
        'workspace/selectById',
        parseInt(params.workspaceId, 10)
      )
    } catch (e) {
      return error({ statusCode: 404, message: 'Workspace not found.' })
    }

    // MusicEngine: Auto-redirect to first database's first table (server-side)
    try {
      const applications = store.getters['application/getAllOfWorkspace'](workspace)
      const databases = applications
        .filter((a) => a.type === 'database')
        .sort((a, b) => a.order - b.order)

      if (databases.length > 0) {
        const firstDatabase = databases[0]
        const tables = firstDatabase.tables || []
        if (tables.length > 0) {
          const firstTable = [...tables].sort((a, b) => a.order - b.order)[0]
          return redirect({
            name: 'database-table',
            params: {
              databaseId: firstDatabase.id,
              tableId: firstTable.id,
            },
          })
        }
      }
    } catch (redirectError) {
      // If redirect fails, continue to normal workspace page
      console.error('MusicEngine: Auto-redirect failed', redirectError)
    }

    try {
      await store.dispatch('auth/fetchWorkspaceInvitations')
      let asyncData = {
        workspaceComponentArguments: {},
        selectedWorkspace: workspace,
      }

      // Loop over all the plugin and call the `fetchAsyncDashboardData` because there
      // might be plugins that extend the dashboard and we want to fetch that async data
      // here.
      const plugins = Object.values(app.$registry.getAll('plugin'))
      for (let i = 0; i < plugins.length; i++) {
        asyncData = await plugins[i].fetchAsyncDashboardData(
          context,
          asyncData,
          workspace.id
        )
      }
      return asyncData
    } catch (e) {
      return error({ statusCode: 400, message: 'Error loading dashboard.' })
    }
  },
  data() {
    return {
      workspaceComponentArguments: null,
      templates: [
        {
          name: 'Project Management',
          slug: 'project-management',
          type: 'calendar',
          color: 'yellow',
        },
        {
          name: 'Performance Reviews',
          slug: 'performance-reviews',
          type: 'table',
          color: 'purple',
        },
      ],
    }
  },
  head() {
    return {
      title: this.$t('dashboard.title'),
    }
  },
  computed: {
    ...mapGetters({
      workspaceInvitations: 'auth/getWorkspaceInvitations',
      getAllOfWorkspace: 'application/getAllOfWorkspace',
    }),
    dashboardHelpComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .reduce(
          (components, plugin) =>
            components.concat(plugin.getDashboardHelpComponents()),
          []
        )
        .filter((component) => component !== null)
    },
    dashboardWorkspaceRowUsageComponent() {
      return Object.values(this.$registry.getAll('plugin'))
        .map((plugin) => plugin.getDashboardWorkspaceRowUsageComponent())
        .filter((component) => component !== null)
    },
    dashboardWorkspacePlanBadge() {
      return Object.values(this.$registry.getAll('plugin'))
        .map((plugin) => plugin.getDashboardWorkspacePlanBadge())
        .filter((component) => component !== null)
    },
    canCreateCreateApplication() {
      return this.$hasPermission(
        'workspace.create_application',
        this.selectedWorkspace,
        this.selectedWorkspace.id
      )
    },
    resourceLinksComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .map((plugin) => plugin.getDashboardResourceLinksComponent())
        .filter((component) => component !== null)
    },
    orderedApplicationsInSelectedWorkspace() {
      return this.getAllOfWorkspace(this.selectedWorkspace).sort(
        (a, b) => a.order - b.order
      )
    },
    /**
     * Check if the workspace exists, because if not, it doesn't make any sense to
     * render anything. This can happen when the workspace is a state where it's
     * deleted, for example.
     */
    workspaceExists() {
      return (
        this.$store.getters['workspace/getAll'].find(
          (w) => w.id === this.selectedWorkspace.id
        ) !== undefined
      )
    },
  },
  methods: {
    getApplicationType(application) {
      return this.$registry.get('application', application.type)
    },
    selectApplication(application) {
      const type = this.$registry.get('application', application.type)
      type.select(application, this)
    },
    async workspaceUpdated(workspace) {
      await this.fetchWorkspaceExtraData(workspace)
    },
    async fetchWorkspaceExtraData(workspace) {
      const plugins = Object.values(this.$registry.getAll('plugin'))
      const asyncData = {}
      for (let i = 0; i < plugins.length; i++) {
        const workspaceData = await plugins[i].fetchAsyncDashboardData(
          this.$root.$nuxt.context,
          asyncData,
          workspace.id
        )
        const data = {
          workspaceComponentArguments: this.workspaceComponentArguments,
        }
        this.workspaceComponentArguments = plugins[i].mergeDashboardData(
          JSON.parse(JSON.stringify(data)),
          workspaceData
        ).workspaceComponentArguments
      }
    },
  },
}
</script>
