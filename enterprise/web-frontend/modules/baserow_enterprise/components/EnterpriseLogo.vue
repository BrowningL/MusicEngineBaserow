<template functional>
  <!-- ISRCAnalytics: Simplified logo component, always shows ISRCAnalytics branding -->
  <div class="logo">
    <img
      :src="$options.methods.getLogoUrl(parent)"
      v-bind="props"
      :class="[data.staticClass, data.class]"
    />
  </div>
</template>

<script>
export default {
  name: 'EnterpriseLogo',
  methods: {
    getLogoUrl(parent) {
      // ISRCAnalytics: Always return the ISRCAnalytics logo
      return require('@baserow/modules/core/static/img/logo.svg')
    },
  },
}
</script>
