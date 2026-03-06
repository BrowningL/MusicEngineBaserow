import { PremiumPlugin } from '@baserow_premium/plugins'
import {
  JSONTableExporter,
  XMLTableExporter,
  ExcelTableExporterType,
  FileTableExporter,
} from '@baserow_premium/tableExporterTypes'
// MusicEngine: Removed LicensesAdminType import
import rowCommentsStore from '@baserow_premium/store/row_comments'
// MusicEngine: Removed Kanban, Calendar, Timeline view stores
import impersonatingStore from '@baserow_premium/store/impersonating'
import { PremiumDatabaseApplicationType } from '@baserow_premium/applicationTypes'
import { registerRealtimeEvents } from '@baserow_premium/realtime'
// MusicEngine: Removed Kanban, Calendar, Timeline view types

import {
  LeftBorderColorViewDecoratorType,
  BackgroundColorViewDecoratorType,
} from '@baserow_premium/viewDecorators'

import {
  SingleSelectColorValueProviderType,
  ConditionalColorValueProviderType,
} from '@baserow_premium/decoratorValueProviders'
// MusicEngine: Removed FormViewSurveyModeType
import {
  TextFieldType,
  LongTextFieldType,
  URLFieldType,
  EmailFieldType,
  NumberFieldType,
  RatingFieldType,
  BooleanFieldType,
  SingleSelectFieldType,
  PhoneNumberFieldType,
  AutonumberFieldType,
} from '@baserow/modules/database/fieldTypes'
import {
  CountViewAggregationType,
  EmptyCountViewAggregationType,
  NotEmptyCountViewAggregationType,
  CheckedCountViewAggregationType,
  NotCheckedCountViewAggregationType,
  EmptyPercentageViewAggregationType,
  NotEmptyPercentageViewAggregationType,
  CheckedPercentageViewAggregationType,
  NotCheckedPercentageViewAggregationType,
  UniqueCountViewAggregationType,
  MinViewAggregationType,
  MaxViewAggregationType,
  SumViewAggregationType,
  AverageViewAggregationType,
  StdDevViewAggregationType,
  VarianceViewAggregationType,
  MedianViewAggregationType,
} from '@baserow/modules/database/viewAggregationTypes'
// MusicEngine: Removed ChartWidgetType, PieChartWidgetType
// MusicEngine: Removed SingleSelectFormattingType (chart formatting)
// MusicEngine: Removed GenerateAIValuesJobType, GenerateAIValuesContextItemType
import en from '@baserow_premium/locales/en.json'
import fr from '@baserow_premium/locales/fr.json'
import nl from '@baserow_premium/locales/nl.json'
import de from '@baserow_premium/locales/de.json'
import es from '@baserow_premium/locales/es.json'
import it from '@baserow_premium/locales/it.json'
import pl from '@baserow_premium/locales/pl.json'
import ko from '@baserow_premium/locales/ko.json'
import { PremiumLicenseType } from '@baserow_premium/licenseTypes'
import { PersonalViewOwnershipType } from '@baserow_premium/viewOwnershipTypes'
import { ViewOwnershipPermissionManagerType } from '@baserow_premium/permissionManagerTypes'
import {
  RowCommentMentionNotificationType,
  RowCommentNotificationType,
} from '@baserow_premium/notificationTypes'
import { CommentsRowModalSidebarType } from '@baserow_premium/rowModalSidebarTypes'
import {
  // MusicEngine: Removed AIFieldType
  PremiumFormulaFieldType,
} from '@baserow_premium/fieldTypes'
// MusicEngine: Removed AI field output types
import {
  // MusicEngine: Removed AI, Kanban, Calendar, Timeline, Survey, Chart paid features
  ExportsPaidFeature,
  PersonalViewsPaidFeature,
  PublicLogoRemovalPaidFeature,
  RowColoringPaidFeature,
  RowCommentsPaidFeature,
  RowNotificationsPaidFeature,
} from '@baserow_premium/paidFeatures'

export default (context) => {
  const { store, app, isDev } = context

  app.$clientErrorMap.setError(
    'ERROR_FEATURE_NOT_AVAILABLE',
    'License required',
    'This functionality requires an active premium license. Please refresh the page.'
  )

  app.$clientErrorMap.setError(
    'ERROR_USER_NOT_COMMENT_AUTHOR',
    app.i18n.t('rowComment.errorUserNotCommentAuthorTitle'),
    app.i18n.t('rowComment.errorUserNotCommentAuthor')
  )
  app.$clientErrorMap.setError(
    'ERROR_INVALID_COMMENT_MENTION',
    app.i18n.t('rowComment.errorInvalidCommentMentionTitle'),
    app.i18n.t('rowComment.errorInvalidCommentMention')
  )

  // Allow locale file hot reloading
  if (isDev && app.i18n) {
    const { i18n } = app
    i18n.mergeLocaleMessage('en', en)
    i18n.mergeLocaleMessage('fr', fr)
    i18n.mergeLocaleMessage('nl', nl)
    i18n.mergeLocaleMessage('de', de)
    i18n.mergeLocaleMessage('es', es)
    i18n.mergeLocaleMessage('it', it)
    i18n.mergeLocaleMessage('pl', pl)
    i18n.mergeLocaleMessage('ko', ko)
  }

  store.registerModule('row_comments', rowCommentsStore)
  // MusicEngine: Removed Kanban, Calendar, Timeline view store registrations
  store.registerModule('impersonating', impersonatingStore)

  // MusicEngine: Removed aiFieldOutputType namespace registration
  app.$registry.registerNamespace('paidFeature')

  app.$registry.register('plugin', new PremiumPlugin(context))
  // MusicEngine: Removed Licenses admin page registration
  app.$registry.register('exporter', new JSONTableExporter(context))
  app.$registry.register('exporter', new XMLTableExporter(context))
  app.$registry.register('exporter', new ExcelTableExporterType(context))
  app.$registry.register('exporter', new FileTableExporter(context))
  // MusicEngine: Removed AIFieldType registration
  app.$registry.register('field', new PremiumFormulaFieldType(context))
  // MusicEngine: Removed Kanban, Calendar, Timeline view registrations

  app.$registry.register(
    'viewDecorator',
    new LeftBorderColorViewDecoratorType(context)
  )
  app.$registry.register(
    'viewDecorator',
    new BackgroundColorViewDecoratorType(context)
  )

  app.$registry.register(
    'decoratorValueProvider',
    new SingleSelectColorValueProviderType(context)
  )
  app.$registry.register(
    'decoratorValueProvider',
    new ConditionalColorValueProviderType(context)
  )

  app.$registry.register(
    'viewOwnershipType',
    new PersonalViewOwnershipType(context)
  )

  // MusicEngine: Removed FormViewSurveyModeType registration

  app.$registry.register('license', new PremiumLicenseType(context))

  app.$registry.register(
    'permissionManager',
    new ViewOwnershipPermissionManagerType(context)
  )

  registerRealtimeEvents(app.$realtime)

  // Overwrite the existing database application type with the one customized for
  // premium use.
  app.$registry.register(
    'application',
    new PremiumDatabaseApplicationType(context)
  )
  app.$registry.register(
    'notification',
    new RowCommentMentionNotificationType(context)
  )
  app.$registry.register(
    'notification',
    new RowCommentNotificationType(context)
  )

  app.$registry.register(
    'rowModalSidebar',
    new CommentsRowModalSidebarType(context)
  )

  // MusicEngine: Removed AI field output types, AI job type, and AI context item registrations

  app.$registry.register(
    'groupedAggregation',
    new MinViewAggregationType(context)
  )
  app.$registry.register(
    'groupedAggregation',
    new MaxViewAggregationType(context)
  )
  app.$registry.register(
    'groupedAggregation',
    new SumViewAggregationType(context)
  )
  app.$registry.register(
    'groupedAggregation',
    new AverageViewAggregationType(context)
  )
  app.$registry.register(
    'groupedAggregation',
    new MedianViewAggregationType(context)
  )
  app.$registry.register(
    'groupedAggregation',
    new StdDevViewAggregationType(context)
  )
  app.$registry.register(
    'groupedAggregation',
    new VarianceViewAggregationType(context)
  )
  app.$registry.register(
    'groupedAggregation',
    new CountViewAggregationType(context)
  )
  app.$registry.register(
    'groupedAggregation',
    new EmptyCountViewAggregationType(context)
  )
  app.$registry.register(
    'groupedAggregation',
    new NotEmptyCountViewAggregationType(context)
  )
  app.$registry.register(
    'groupedAggregation',
    new CheckedCountViewAggregationType(context)
  )
  app.$registry.register(
    'groupedAggregation',
    new NotCheckedCountViewAggregationType(context)
  )
  app.$registry.register(
    'groupedAggregation',
    new EmptyPercentageViewAggregationType(context)
  )
  app.$registry.register(
    'groupedAggregation',
    new NotEmptyPercentageViewAggregationType(context)
  )
  app.$registry.register(
    'groupedAggregation',
    new CheckedPercentageViewAggregationType(context)
  )
  app.$registry.register(
    'groupedAggregation',
    new NotCheckedPercentageViewAggregationType(context)
  )
  app.$registry.register(
    'groupedAggregation',
    new UniqueCountViewAggregationType(context)
  )

  app.$registry.register(
    'groupedAggregationGroupedBy',
    new TextFieldType(context)
  )
  app.$registry.register(
    'groupedAggregationGroupedBy',
    new LongTextFieldType(context)
  )
  app.$registry.register(
    'groupedAggregationGroupedBy',
    new NumberFieldType(context)
  )
  app.$registry.register(
    'groupedAggregationGroupedBy',
    new URLFieldType(context)
  )
  app.$registry.register(
    'groupedAggregationGroupedBy',
    new RatingFieldType(context)
  )
  app.$registry.register(
    'groupedAggregationGroupedBy',
    new BooleanFieldType(context)
  )
  app.$registry.register(
    'groupedAggregationGroupedBy',
    new EmailFieldType(context)
  )
  app.$registry.register(
    'groupedAggregationGroupedBy',
    new SingleSelectFieldType(context)
  )
  app.$registry.register(
    'groupedAggregationGroupedBy',
    new PhoneNumberFieldType(context)
  )
  app.$registry.register(
    'groupedAggregationGroupedBy',
    new AutonumberFieldType(context)
  )

  // MusicEngine: Removed Chart widgets and chart field formatting registrations

  // MusicEngine: Only register features we want to keep (removed Kanban, Calendar, Timeline, AI, Survey, Chart)
  app.$registry.register('paidFeature', new RowColoringPaidFeature(context))
  app.$registry.register('paidFeature', new RowCommentsPaidFeature(context))
  app.$registry.register(
    'paidFeature',
    new RowNotificationsPaidFeature(context)
  )
  app.$registry.register('paidFeature', new PersonalViewsPaidFeature(context))
  app.$registry.register('paidFeature', new ExportsPaidFeature(context))
  app.$registry.register(
    'paidFeature',
    new PublicLogoRemovalPaidFeature(context)
  )

  // MusicEngine: Removed timelineFieldRules namespace registration
}
