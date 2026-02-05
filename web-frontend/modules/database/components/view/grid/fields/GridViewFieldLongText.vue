<template>
  <div
    ref="cell"
    class="grid-view__cell grid-field-long-text__cell active"
    :class="{ editing: opened }"
    @contextmenu="stopContextIfEditing($event)"
  >
    <!-- ACR Scan Button - shows for ACR Report field when Inspiration File exists -->
    <div
      v-if="showAcrScanButton && !opened"
      class="grid-field-long-text__acr-controls"
    >
      <a
        v-if="!acrScanning"
        v-tooltip="'Run ACR fingerprint scan'"
        class="grid-field-long-text__acr-btn"
        @click.prevent="triggerAcrScan()"
      >
        <i class="iconoir-fingerprint"></i>
      </a>
      <div v-else class="grid-field-long-text__acr-loading">
        <div class="loading"></div>
      </div>
    </div>
    <div v-if="!opened" class="grid-field-long-text">{{ value }}</div>
    <textarea
      v-else-if="editing"
      ref="input"
      v-model="copy"
      v-prevent-parent-scroll
      :disabled="readOnly"
      type="text"
      class="grid-field-long-text__textarea"
    />
    <div v-else class="grid-field-long-text__textarea">{{ value }}</div>
    <slot name="default" :slot-props="{ editing, opened }"></slot>
  </div>
</template>

<script>
import gridField from '@baserow/modules/database/mixins/gridField'
import gridFieldInput from '@baserow/modules/database/mixins/gridFieldInput'

export default {
  mixins: [gridField, gridFieldInput],
  data() {
    return {
      acrScanning: false,
      acrRefreshTimeouts: [],
    }
  },
  computed: {
    /**
     * Check if this is the "ACR Report" field and if there's an
     * "Inspiration File" with a file in the same row.
     */
    showAcrScanButton() {
      // Only show for "Fingerprint Report" field (formerly "ACR Report")
      if (this.field.name !== 'Fingerprint Report') {
        return false
      }

      // Don't show in read-only mode
      if (this.readOnly) {
        return false
      }

      // Don't show if there's already text/output in the cell
      if (this.value && this.value.trim() !== '') {
        return false
      }

      // Check if there's a file in the Inspiration File field
      const inspirationFile = this.getInspirationFile()
      return inspirationFile !== null
    },
  },
  beforeDestroy() {
    // Clean up any pending refresh timeouts
    this.acrRefreshTimeouts.forEach((timeoutId) => {
      clearTimeout(timeoutId)
    })
  },
  methods: {
    afterEdit(event) {
      // If the enter key is pressed we do not want to add a new line to the textarea.
      if (event.type === 'keydown' && event.key === 'Enter') {
        event.preventDefault()
      }
      this.$nextTick(() => {
        this.$refs.input.focus()
        this.$refs.input.selectionStart = this.$refs.input.selectionEnd = 100000
      })
    },
    canSaveByPressingEnter(event) {
      // Save only if shiftKey is pressed
      return event.shiftKey
    },
    /**
     * Get the Inspiration File value from the same row.
     */
    getInspirationFile() {
      if (!this.row || !this.allFieldsInTable) {
        return null
      }

      // Find the "Inspiration File" field in the table
      const fileField = this.allFieldsInTable.find(
        (f) => f.name === 'Inspiration File' && f.type === 'file'
      )
      if (!fileField) {
        return null
      }

      // Get the value from the row
      const fieldKey = `field_${fileField.id}`
      const value = this.row[fieldKey]

      // Check if there's at least one file
      if (Array.isArray(value) && value.length > 0) {
        return value[0] // Return the first file
      }

      return null
    },
    /**
     * Trigger the ACR scan via the ISRCAnalytics webhook API.
     */
    async triggerAcrScan() {
      if (this.acrScanning || this.readOnly) {
        return
      }

      const inspirationFile = this.getInspirationFile()
      if (!inspirationFile) {
        return
      }

      this.acrScanning = true

      try {
        // Get the table ID from the field object
        const tableId = this.field.table_id
        if (!tableId) {
          throw new Error('Could not determine table ID for this field')
        }

        // Get database and workspace info from the application store
        const application = this.$store.getters['application/getSelected']
        const workspaceId = application?.workspace?.id || application?.group?.id || 0
        const databaseId = application?.id || 0
        const rowId = this.row.id

        // Create ACR scan request payload
        const payload = {
          table_id: tableId,
          database_id: databaseId,
          workspace_id: workspaceId,
          row_id: rowId,
          file_url: inspirationFile.url,
          file_name: inspirationFile.name || inspirationFile.visible_name,
          user_jwt_token: this.$store.state.auth.token,
        }

        // Get the webhook URL from config
        const baseWebhookUrl = this.$config?.ISRCANALYTICS_WEBHOOK_URL
        if (!baseWebhookUrl) {
          throw new Error(
            'ISRCANALYTICS_WEBHOOK_URL not configured. Please set this environment variable.'
          )
        }

        // Build the ACR scan endpoint URL
        // Replace /inspiration with /acr-scan in the URL
        const acrScanUrl = baseWebhookUrl.replace('/inspiration', '/acr-scan')

        const response = await fetch(acrScanUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        })

        const data = await response.json()

        if (!response.ok || data.status === 'error') {
          throw new Error(data.message || 'Failed to trigger ACR scan')
        }

        // Show success notification
        this.$store.dispatch('toast/success', {
          title: 'ACR scan started',
          message: 'The fingerprint scan is running. Results will appear shortly.',
        })

        // Refresh the row after delays to pick up the ACR report
        this.acrRefreshTimeouts = []
        const refreshDelays = [5000, 15000, 30000, 60000]
        refreshDelays.forEach((delay) => {
          const timeoutId = setTimeout(() => {
            this.$emit('refresh-row')
          }, delay)
          this.acrRefreshTimeouts.push(timeoutId)
        })
      } catch (error) {
        console.error('ACR scan error:', error)
        this.$store.dispatch('toast/error', {
          title: 'Scan failed',
          message: error.message || 'Failed to start the ACR scan. Please try again.',
        })
      } finally {
        this.acrScanning = false
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.grid-field-long-text__acr-controls {
  position: absolute;
  top: 4px;
  left: 4px;
  z-index: 1;
}

.grid-field-long-text__acr-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 3px;
  background-color: #e8f5e9;
  color: #2e7d32;
  cursor: pointer;
  transition: background-color 0.15s ease;

  &:hover {
    background-color: #c8e6c9;
  }

  i {
    font-size: 12px;
  }
}

.grid-field-long-text__acr-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
}
</style>