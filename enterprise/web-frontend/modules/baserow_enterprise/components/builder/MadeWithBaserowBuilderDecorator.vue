<template>
  <!-- ISRCAnalytics: Removed "Made with Baserow" badge -->
  <div>
    <slot></slot>
  </div>
</template>

<script>
export default {
  props: {
    showPaidFeaturesModal: {
      type: Boolean,
      default: false,
    },
  },
}
</script>