<template>
  <!-- MusicEngine: Removed "Hide Baserow Logo" toggle, only show export option -->
  <div>
    <div
      v-if="hasValidExporter"
      class="view-sharing__option"
    >
      <SwitchInput
        small
        :value="view.allow_public_export"
        @input="update('allow_public_export', $event)"
      >
        <i class="iconoir iconoir-share-ios"></i>
        <span>
          {{ $t('shareLinkOptions.allowPublicExportLabel') }}
        </span>
      </SwitchInput>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import ViewPremiumService from '@baserow_premium/services/view'
import { notifyIf } from '@baserow/modules/core/utils/error'
import PremiumFeatures from '@baserow_premium/features'
import viewTypeHasExporterTypes from '@baserow/modules/database/utils/viewTypeHasExporterTypes'
import PaidFeaturesModal from '@baserow_premium/components/PaidFeaturesModal'

export default {
  name: 'PremiumViewOptions',
  components: { PaidFeaturesModal },

  props: {
    view: {
      type: Object,
      required: true,
    },
  },
  computed: {
    ...mapGetters({
      additionalUserData: 'auth/getAdditionalUserData',
    }),
    workspace() {
      return this.$store.getters['application/get'](this.view.table.database_id)
        .workspace
    },
    hasPremiumFeatures() {
      return this.$hasFeature(PremiumFeatures.PREMIUM, this.workspace.id)
    },
    tooltipText() {
      if (this.hasPremiumFeatures) {
        return null
      } else {
        return this.$t('premium.deactivated')
      }
    },
    hasValidExporter() {
      return viewTypeHasExporterTypes(this.view.type, this.$registry)
    },
  },
  methods: {
    async update(key, value) {
      try {
        // We are being optimistic that the request will succeed.
        this.$emit('update-view', { ...this.view, [key]: value })
        await ViewPremiumService(this.$client).update(this.view.id, {
          [key]: value,
        })
      } catch (error) {
        // In case it didn't we will roll back the change.
        this.$emit('update-view', { ...this.view, [key]: !value })
        notifyIf(error, 'view')
      }
    },
    click() {
      if (!this.hasPremiumFeatures) {
        this.$refs.paidFeaturesModal.show()
      }
    },
  },
}
</script>
