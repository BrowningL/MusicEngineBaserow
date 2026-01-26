<template>
  <div
    ref="cell"
    class="grid-view__cell grid-field-file__cell"
    :class="{ active: selected }"
    @drop.prevent="onDrop($event)"
    @dragover.prevent
    @dragenter.prevent="dragEnter($event)"
    @dragleave="dragLeave($event)"
  >
    <div v-show="dragging" class="grid-field-file__dragging">
      <div>
        <i class="grid-field-file__drop-icon iconoir-cloud-upload"></i>
        {{ $t('gridViewFieldFile.dropHere') }}
      </div>
    </div>
    <ul v-if="Array.isArray(value)" class="grid-field-file__list">
      <li
        v-for="(file, index) in value"
        :key="file.name + index"
        class="grid-field-file__item"
      >
        <a
          v-tooltip="file.visible_name"
          class="grid-field-file__link"
          @click.prevent="showFileModal(index)"
        >
          <img
            v-if="file.is_image"
            class="grid-field-file__image"
            :src="file.thumbnails.tiny.url"
          />
          <i
            v-else
            class="grid-field-file__icon"
            :class="getIconClass(file.mime_type)"
          ></i>
        </a>
      </li>
      <li
        v-for="loading in loadings"
        :key="loading.id"
        class="grid-field-file__item"
      >
        <div class="grid-field-file__loading"></div>
      </li>
      <!-- Inspiration Download Button - shows only when file is empty and Inspiration URL exists -->
      <li
        v-if="!readOnly && showInspirationDownloadButton && !inspirationDownloading"
        class="grid-field-file__item"
      >
        <a
          v-tooltip="'Download from Inspiration URL'"
          class="grid-field-file__item-add grid-field-file__inspiration-download"
          @click.prevent="triggerInspirationDownload()"
        >
          <i class="iconoir-download"></i>
        </a>
      </li>
      <!-- Inspiration Download Loading State -->
      <li
        v-if="inspirationDownloading"
        class="grid-field-file__item"
      >
        <div class="grid-field-file__loading"></div>
      </li>
      <li v-if="!readOnly" v-show="selected" class="grid-field-file__item">
        <a class="grid-field-file__item-add" @click.prevent="showUploadModal()">
          <i class="iconoir-plus"></i>
        </a>
        <div v-if="value.length == 0 && !showInspirationDownloadButton" class="grid-field-file__drop">
          <i class="grid-field-file__drop-icon iconoir-cloud-upload"></i>
          {{ $t('gridViewFieldFile.dropFileHere') }}
        </div>
      </li>
    </ul>
    <UserFilesModal
      v-if="Array.isArray(value) && !readOnly"
      ref="uploadModal"
      @uploaded="addFiles(value, $event)"
      @hidden="hideModal"
    ></UserFilesModal>
    <FileFieldModal
      v-if="Array.isArray(value)"
      ref="fileModal"
      :files="value"
      :read-only="readOnly"
      @hidden="hideModal"
      @removed="removeFile(value, $event)"
      @renamed="renameFile(value, $event.index, $event.value)"
    ></FileFieldModal>
  </div>
</template>

<script>
import { uuid } from '@baserow/modules/core/utils/string'
import { isElement } from '@baserow/modules/core/utils/dom'
import { notifyIf } from '@baserow/modules/core/utils/error'
import UserFilesModal from '@baserow/modules/core/components/files/UserFilesModal'
import { UploadFileUserFileUploadType } from '@baserow/modules/core/userFileUploadTypes'
import UserFileService from '@baserow/modules/core/services/userFile'
import FileFieldModal from '@baserow/modules/database/components/field/FileFieldModal'
import gridField from '@baserow/modules/database/mixins/gridField'
import fileField from '@baserow/modules/database/mixins/fileField'

export default {
  name: 'GridViewFieldFile',
  components: { UserFilesModal, FileFieldModal },
  mixins: [gridField, fileField],
  data() {
    return {
      modalOpen: false,
      dragging: false,
      loadings: [],
      dragTarget: null,
      inspirationDownloading: false,
    }
  },
  computed: {
    /**
     * Check if this is the "Inspiration File" field and if there's an
     * "Inspiration" URL field with a valid URL in the same row.
     * Only show the download button if the file field is empty.
     */
    showInspirationDownloadButton() {
      // Only show for "Inspiration File" field
      if (this.field.name !== 'Inspiration File') {
        return false
      }

      // Don't show if file field already has files
      if (Array.isArray(this.value) && this.value.length > 0) {
        return false
      }

      // Find the "Inspiration" URL field
      const inspirationUrl = this.getInspirationUrl()
      if (!inspirationUrl) {
        return false
      }

      // Validate it's a supported URL
      return this.isValidInspirationUrl(inspirationUrl)
    },
  },
  methods: {
    /**
     * Get the Inspiration URL value from the same row.
     */
    getInspirationUrl() {
      if (!this.row || !this.allFieldsInTable) {
        return null
      }

      // Find the "Inspiration" field in the table
      const inspirationField = this.allFieldsInTable.find(
        (f) => f.name === 'Inspiration' && f.type === 'url'
      )
      if (!inspirationField) {
        return null
      }

      // Get the value from the row
      const fieldKey = `field_${inspirationField.id}`
      const value = this.row[fieldKey]

      return typeof value === 'string' && value.trim() !== '' ? value.trim() : null
    },
    /**
     * Validate that a URL is from a supported platform.
     */
    isValidInspirationUrl(url) {
      if (!url || typeof url !== 'string') return false

      const supportedDomains = [
        'youtube.com',
        'youtu.be',
        'www.youtube.com',
        'music.youtube.com',
        'soundcloud.com',
        'www.soundcloud.com',
        'tiktok.com',
        'www.tiktok.com',
        'vm.tiktok.com',
      ]

      try {
        const urlObj = new URL(url)
        return supportedDomains.some((domain) => urlObj.hostname.includes(domain))
      } catch {
        return false
      }
    },
    /**
     * Trigger the inspiration download via the ISRCAnalytics webhook API.
     * We simulate a Baserow webhook payload to trigger the download.
     */
    async triggerInspirationDownload() {
      if (this.inspirationDownloading || this.readOnly) {
        return
      }

      const inspirationUrl = this.getInspirationUrl()
      if (!inspirationUrl) {
        return
      }

      this.inspirationDownloading = true

      try {
        // Get the table ID from the store
        const tableId = this.$store.getters[`${this.storePrefix}view/grid/getTableId`]
        // Get database and workspace info from the application store
        const application = this.$store.getters['application/getSelected']
        const workspaceId = application?.workspace?.id || application?.group?.id || 0
        const databaseId = application?.id || 0
        const rowId = this.row.id

        // Simulate a Baserow webhook payload
        // The webhook endpoint expects this format for rows.updated events
        const webhookPayload = {
          table_id: tableId,
          database_id: databaseId,
          workspace_id: workspaceId,
          event_id: `manual-${Date.now()}`,
          event_type: 'rows.updated',
          items: [
            {
              id: rowId,
              order: this.row.order || '1',
              Inspiration: inspirationUrl,
            },
          ],
          old_items: [
            {
              id: rowId,
              order: this.row.order || '1',
              Inspiration: '', // Old value was empty (triggers the webhook logic)
            },
          ],
        }

        // Call the ISRCAnalytics webhook endpoint
        // This is a public endpoint that doesn't require authentication
        // The URL is configured via environment variable or defaults to production
        const webhookUrl =
          this.$config?.isrcanalyticsWebhookUrl ||
          process.env.ISRCANALYTICS_WEBHOOK_URL ||
          'https://isrcanalytics.com/api/webhooks/baserow/inspiration'

        const response = await fetch(webhookUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(webhookPayload),
        })

        const data = await response.json()

        if (!response.ok || data.status === 'error') {
          throw new Error(data.message || 'Failed to trigger download')
        }

        // Show success notification
        this.$store.dispatch('toast/success', {
          title: 'Download started',
          message: 'The file is being downloaded. It will appear shortly.',
        })

        // Refresh the row after a delay to pick up the new file
        // The download typically takes 10-30 seconds
        setTimeout(() => {
          this.$emit('refresh-row')
        }, 5000)

        // Set up additional refresh attempts
        const refreshAttempts = [15000, 30000, 60000]
        refreshAttempts.forEach((delay) => {
          setTimeout(() => {
            this.$emit('refresh-row')
          }, delay)
        })
      } catch (error) {
        console.error('Inspiration download error:', error)
        this.$store.dispatch('toast/error', {
          title: 'Download failed',
          message: error.message || 'Failed to start the download. Please try again.',
        })
      } finally {
        this.inspirationDownloading = false
      }
    },
    /**
     * Method is called when the user drops his files into the field. The files should
     * automatically be uploaded to the user files and added to the field after that.
     */
    async onDrop(event) {
      const files = [...event.dataTransfer.items].map((item) =>
        item.getAsFile()
      )
      await this.uploadFiles(files)
    },
    async uploadFiles(fileArray) {
      if (this.readOnly) {
        return
      }

      this.dragging = false

      // Indicates that this component must not be destroyed even though the user might
      // select another cell.
      this.$emit('add-keep-alive')

      const files = fileArray.map((file) => {
        return {
          id: uuid(),
          file,
        }
      })

      if (files === null) {
        return
      }

      this.$emit('select')

      // First add the file ids to the loading list so the user sees a visual loading
      // indication for each file.
      files.forEach((file) => {
        this.loadings.push({ id: file.id })
      })

      // Now upload the files one by one to not overload the backend. When finished,
      // regardless of is has succeeded, the loading state for that file can be removed
      // because it has already been added as a file.
      for (let i = 0; i < files.length; i++) {
        const id = files[i].id
        const file = files[i].file

        try {
          const { data } = await UserFileService(this.$client).uploadFile(file)
          this.addFiles(this.value, [data])
        } catch (error) {
          notifyIf(error, 'userFile')
        }

        const index = this.loadings.findIndex((l) => l.id === id)
        this.loadings.splice(index, 1)
      }

      // Indicates that this component can be destroyed if it is not selected.
      this.$emit('remove-keep-alive')
    },
    select() {
      // While the field is selected we want to open the select row toast by pressing
      // the enter key.
      this.$el.keydownEvent = (event) => {
        if (event.key === 'Enter' && !this.modalOpen) {
          this.showUploadModal()
        }
      }
      document.body.addEventListener('keydown', this.$el.keydownEvent)
    },
    beforeUnSelect() {
      document.body.removeEventListener('keydown', this.$el.keydownEvent)
    },
    /**
     * If the user clicks inside the select row modal we do not want to unselect the
     * field. The modal lives in the root of the body element and not inside the cell,
     * so the system naturally wants to unselect when the user clicks inside one of
     * these contexts.
     */
    canUnselectByClickingOutside(event) {
      return (
        (!this.$refs.uploadModal ||
          !isElement(this.$refs.uploadModal.$el, event.target)) &&
        !isElement(this.$refs.fileModal.$el, event.target)
      )
    },
    /**
     * Prevent unselecting the field cell by changing the event. Because the deleted
     * item is not going to be part of the dom anymore after deleting it will get
     * noticed as if the user clicked outside the cell which wasn't the case.
     */
    removeFile(event, index) {
      event.preventFieldCellUnselect = true
      return fileField.methods.removeFile.call(this, event, index)
    },
    showUploadModal() {
      if (this.readOnly) {
        return
      }

      this.modalOpen = true
      this.$refs.uploadModal.show(UploadFileUserFileUploadType.getType())
    },
    showFileModal(index) {
      this.modalOpen = true
      this.$refs.fileModal.show(index)
    },
    hideModal() {
      this.modalOpen = false
    },
    /**
     * While the modal is open, all key combinations related to the field must be
     * ignored.
     */
    canSelectNext() {
      return !this.modalOpen
    },
    canKeyDown() {
      return !this.modalOpen
    },
    canKeyboardShortcut() {
      return !this.modalOpen
    },
    dragEnter(event) {
      if (this.readOnly) {
        return
      }

      this.dragging = true
      this.dragTarget = event.target
    },
    dragLeave(event) {
      if (this.dragTarget === event.target && !this.readOnly) {
        event.stopPropagation()
        event.preventDefault()
        this.dragging = false
        this.dragTarget = null
      }
    },
    onPaste(event) {
      if (
        !event.clipboardData.types.includes('text/plain') ||
        event.clipboardData.getData('text/plain').startsWith('file:///')
      ) {
        const { items } = event.clipboardData
        for (let i = 0; i < items.length; i++) {
          const item = items[i]
          if (item.type.includes('image')) {
            const file = item.getAsFile()
            this.uploadFiles([file])
            return true
          }
        }
      }
      return false
    },
  },
}
</script>
