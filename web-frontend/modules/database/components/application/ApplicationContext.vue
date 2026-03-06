<template>
  <ApplicationContext
    ref="context"
    :application="application"
    :workspace="workspace"
  >
    <!-- MusicEngine: Removed View API Docs menu item -->
  </ApplicationContext>
</template>

<script>
import ApplicationContext from '@baserow/modules/core/components/application/ApplicationContext.vue'
import applicationContext from '@baserow/modules/core/mixins/applicationContext'

export default {
  components: {
    ApplicationContext,
  },
  mixins: [applicationContext],
  props: {
    application: {
      type: Object,
      required: true,
    },
    workspace: {
      type: Object,
      required: true,
    },
  },
}
</script>
