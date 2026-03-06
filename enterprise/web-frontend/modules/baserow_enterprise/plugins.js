import { BaserowPlugin } from '@baserow/modules/core/plugins'
// MusicEngine: Removed MemberRolesDatabaseContextItem import (no longer used)
import EnterpriseFeatures from '@baserow_enterprise/features'
import SnapshotModalWarning from '@baserow_enterprise/components/SnapshotModalWarning'
import EnterpriseSettings from '@baserow_enterprise/components/EnterpriseSettings'
import EnterpriseSettingsOverrideDashboardHelp from '@baserow_enterprise/components/EnterpriseSettingsOverrideDashboardHelp'
import EnterpriseLogo from '@baserow_enterprise/components/EnterpriseLogo'
// MusicEngine: Removed DatabaseApplicationType import (no longer used)
import AssistantPanel from '@baserow_enterprise/components/assistant/AssistantPanel'
import DateDependencyFieldTypeIcon from '@baserow_enterprise/components/dateDependency/DateDependencyFieldTypeIcon'
import ExportWorkspaceModalWarning from '@baserow_enterprise/components/ExportWorkspaceModalWarning'

export class EnterprisePlugin extends BaserowPlugin {
  static getType() {
    return 'enterprise'
  }

  getSidebarWorkspaceComponents(workspace) {
    // MusicEngine: Removed Direct Support (Chatwoot) and Audit Log
    // Users can contact support via Telegram @BrownieSE
    return []
  }

  getAdditionalApplicationContextComponents(workspace, application) {
    // MusicEngine: Removed MemberRolesDatabaseContextItem (Manage members)
    // All users are in individual workspaces, member roles not needed
    return []
  }

  getRightSidebarWorkspaceComponents(workspace) {
    const rightSidebarItems = []
    rightSidebarItems.push(AssistantPanel)
    return rightSidebarItems
  }

  getAdditionalTableContextComponents(workspace, table) {
    // MusicEngine: Removed MemberRolesTableContextItem and DateDependencyMenuItem
    return []
  }

  getGridViewFieldTypeIconsBefore(workspace, view, field) {
    const out = []
    out.push(DateDependencyFieldTypeIcon)
    return out
  }

  getAdditionalViewContextComponents() {
    // MusicEngine: Removed MemberRolesViewContextItem and DateDependencyMenuItem
    return []
  }

  getExtraSnapshotModalComponents(workspace) {
    const rbacSupport = this.app.$hasFeature(
      EnterpriseFeatures.RBAC,
      workspace.id
    )
    return rbacSupport ? SnapshotModalWarning : null
  }

  getExtraExportWorkspaceModalComponents(workspace) {
    const rbacSupport = this.app.$hasFeature(
      EnterpriseFeatures.RBAC,
      workspace.id
    )
    return rbacSupport ? ExportWorkspaceModalWarning : null
  }

  getSettingsPageComponents() {
    return [EnterpriseSettings]
  }

  getDashboardHelpComponents() {
    if (this.app.$hasFeature(EnterpriseFeatures.ENTERPRISE_SETTINGS)) {
      return [EnterpriseSettingsOverrideDashboardHelp]
    } else {
      return []
    }
  }

  getLogoComponent() {
    if (this.app.$hasFeature(EnterpriseFeatures.ENTERPRISE_SETTINGS)) {
      return EnterpriseLogo
    } else {
      return null
    }
  }

  getLogoComponentOrder() {
    return 100
  }

  /**
   * This method can be used to hide certain features in `EnterpriseFeatures.vue`.
   * If the array contains `[EnterpriseFeatures.RBAC]`, for example, then that entry
   * will be hidden in the features.
   */
  getVisuallyHiddenFeatures() {
    return []
  }

  /**
   * Adds the custom CSS/JS defined for this builder.
   */
  getBuilderApplicationHeaderAddition({ builder, mode }) {
    const css = `${this.app.$config.PUBLIC_BACKEND_URL}/api/custom_code/${
      builder.id
    }/css/${mode === 'preview' ? '' : 'public/'}`
    const js = `${this.app.$config.PUBLIC_BACKEND_URL}/api/custom_code/${
      builder.id
    }/js/${mode === 'preview' ? '' : 'public/'}`

    const script = []
    const link = []

    builder.scripts.forEach((s) => {
      if (!s.url) {
        return
      }

      const crossorigin =
        s.crossorigin === 'credentials'
          ? 'use-credentials'
          : s.crossorigin === 'anonymous'
          ? 'anonymous'
          : null

      if (s.type === 'javascript') {
        script.push({
          src: s.url,
          crossorigin,
          defer: s.load_type === 'defer',
          async: s.load_type === 'async',
          body: true,
        })
      }

      if (s.type === 'stylesheet') {
        script.push({
          rel: 'stylesheet',
          href: s.url,
          crossorigin,
          body: true,
        })
      }
    })

    if (builder.custom_code.css) {
      link.push({
        rel: 'stylesheet',
        href: css,
        body: true,
      })
    }
    if (builder.custom_code.js) {
      script.push({
        src: js,
        defer: true,
        body: true,
      })
    }

    return {
      link,
      script,
    }
  }
}
