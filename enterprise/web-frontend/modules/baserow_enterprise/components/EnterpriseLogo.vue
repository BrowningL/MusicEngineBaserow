<template functional>
  <!-- MusicEngine: Simplified logo component, always shows MusicEngine branding -->
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
      // MusicEngine: Always return the MusicEngine logo
      return require('@baserow/modules/core/static/img/logo.svg')
    },
  },
}
</script>
