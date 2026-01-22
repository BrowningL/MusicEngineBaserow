<template>
  <div>
    <h2 class="box__title">{{ $t('appearanceSettings.title') }}</h2>
    <p class="margin-bottom-3">{{ $t('appearanceSettings.description') }}</p>

    <div class="control margin-bottom-3">
      <label class="control__label">{{ $t('appearanceSettings.theme') }}</label>
      <div class="appearance-settings__theme-options">
        <div
          class="appearance-settings__theme-option"
          :class="{ 'appearance-settings__theme-option--active': currentTheme === 'light' }"
          @click="setTheme('light')"
        >
          <div class="appearance-settings__theme-preview appearance-settings__theme-preview--light">
            <div class="appearance-settings__preview-sidebar"></div>
            <div class="appearance-settings__preview-content">
              <div class="appearance-settings__preview-header"></div>
              <div class="appearance-settings__preview-rows">
                <div class="appearance-settings__preview-row"></div>
                <div class="appearance-settings__preview-row"></div>
                <div class="appearance-settings__preview-row"></div>
              </div>
            </div>
          </div>
          <span class="appearance-settings__theme-label">{{ $t('appearanceSettings.light') }}</span>
        </div>

        <div
          class="appearance-settings__theme-option"
          :class="{ 'appearance-settings__theme-option--active': currentTheme === 'dark' }"
          @click="setTheme('dark')"
        >
          <div class="appearance-settings__theme-preview appearance-settings__theme-preview--dark">
            <div class="appearance-settings__preview-sidebar"></div>
            <div class="appearance-settings__preview-content">
              <div class="appearance-settings__preview-header"></div>
              <div class="appearance-settings__preview-rows">
                <div class="appearance-settings__preview-row"></div>
                <div class="appearance-settings__preview-row"></div>
                <div class="appearance-settings__preview-row"></div>
              </div>
            </div>
          </div>
          <span class="appearance-settings__theme-label">{{ $t('appearanceSettings.dark') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
const THEME_STORAGE_KEY = 'isrc-theme'

export default {
  name: 'AppearanceSettings',
  data() {
    return {
      currentTheme: 'light',
    }
  },
  mounted() {
    this.currentTheme = this.getStoredTheme()
  },
  methods: {
    getStoredTheme() {
      if (typeof window !== 'undefined') {
        return localStorage.getItem(THEME_STORAGE_KEY) || 'light'
      }
      return 'light'
    },
    setTheme(theme) {
      this.currentTheme = theme
      localStorage.setItem(THEME_STORAGE_KEY, theme)
      this.applyTheme(theme)
    },
    applyTheme(theme) {
      // Apply to both html and body for consistency
      document.documentElement.classList.remove('theme-light', 'theme-dark')
      document.documentElement.classList.add(`theme-${theme}`)
      document.body.classList.remove('theme-light', 'theme-dark')
      document.body.classList.add(`theme-${theme}`)
    },
  },
}
</script>

<style lang="scss" scoped>
.appearance-settings__theme-options {
  display: flex;
  gap: 16px;
}

.appearance-settings__theme-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  border: 2px solid transparent;
  transition: border-color 0.2s ease;

  &:hover {
    border-color: var(--border-color, #ededed);
  }

  &--active {
    border-color: #5190ef;
  }
}

.appearance-settings__theme-preview {
  width: 120px;
  height: 80px;
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  border: 1px solid var(--border-color, #ededed);

  &--light {
    .appearance-settings__preview-sidebar {
      background-color: #fafafa;
      border-right: 1px solid #ededed;
    }
    .appearance-settings__preview-content {
      background-color: #ffffff;
    }
    .appearance-settings__preview-header {
      background-color: #f5f5f5;
      border-bottom: 1px solid #ededed;
    }
    .appearance-settings__preview-row {
      background-color: #ffffff;
      border-bottom: 1px solid #ededed;
    }
  }

  &--dark {
    .appearance-settings__preview-sidebar {
      background-color: #1a1a1a;
      border-right: 1px solid #333333;
    }
    .appearance-settings__preview-content {
      background-color: #1f1f1f;
    }
    .appearance-settings__preview-header {
      background-color: #262626;
      border-bottom: 1px solid #333333;
    }
    .appearance-settings__preview-row {
      background-color: #1f1f1f;
      border-bottom: 1px solid #333333;
    }
  }
}

.appearance-settings__preview-sidebar {
  width: 30px;
  flex-shrink: 0;
}

.appearance-settings__preview-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.appearance-settings__preview-header {
  height: 12px;
  flex-shrink: 0;
}

.appearance-settings__preview-rows {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.appearance-settings__preview-row {
  flex: 1;
}

.appearance-settings__theme-label {
  margin-top: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary, #202128);
}
</style>