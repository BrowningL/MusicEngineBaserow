<template>
  <li
    v-if="selectedRowsCount > 0 && canExportSelectedRows"
    class="header__filter-item"
  >
    <a
      class="header__filter-link active active--primary"
      :class="{ 'header__filter-link--disabled': exporting }"
      @click.prevent="exportSelectedRows"
    >
      <i class="header__filter-icon iconoir-download"></i>
      <span class="header__filter-name">{{ exportLabel }}</span>
    </a>
  </li>
</template>

<script>
import copyPasteHelper from '@baserow/modules/database/mixins/copyPasteHelper'
import { notifyIf } from '@baserow/modules/core/utils/error'
import {
  filterVisibleFieldsFunction,
  sortFieldsByOrderAndIdFunction,
} from '@baserow/modules/database/utils/view'

export default {
  name: 'GridViewSelectedRowsExport',
  mixins: [copyPasteHelper],
  props: {
    database: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      exporting: false,
    }
  },
  computed: {
    isPublic() {
      return this.$store.getters['page/view/public/getIsPublic'] || false
    },
    fieldOptions() {
      return (
        this.$store.getters[`${this.storePrefix}view/grid/getAllFieldOptions`] ||
        {}
      )
    },
    selectedRowIds() {
      return (
        this.$store.getters[
          `${this.storePrefix}view/grid/getCheckboxSelectedRowsIds`
        ] || []
      )
    },
    selectedRowsCount() {
      return this.selectedRowIds.length
    },
    exportableFields() {
      return this.fields
        .filter(filterVisibleFieldsFunction(this.fieldOptions))
        .sort(sortFieldsByOrderAndIdFunction(this.fieldOptions, true))
    },
    canExportSelectedRows() {
      if (this.isPublic) {
        return true
      }

      return this.$hasPermission(
        'database.table.run_export',
        this.table,
        this.database.workspace.id
      )
    },
    exportLabel() {
      if (this.exporting) {
        return this.$t('gridViewSelectedRowsExport.exporting')
      }

      return this.$tc('gridViewSelectedRowsExport.label', this.selectedRowsCount, {
        count: this.selectedRowsCount,
      })
    },
    exportFilename() {
      const parts = [
        'export',
        this.table?.name,
        this.view?.name,
        `${this.selectedRowsCount} selected row${
          this.selectedRowsCount === 1 ? '' : 's'
        }`,
      ]

      return `${parts
        .filter(Boolean)
        .map((part) => this.sanitizeFilenamePart(part))
        .join(' - ')}.csv`
    },
  },
  methods: {
    sanitizeFilenamePart(value) {
      return String(value).replace(/[\\/:*?"<>|]/g, '-').trim()
    },
    async exportSelectedRows() {
      if (this.exporting || this.selectedRowsCount === 0) {
        return
      }

      this.exporting = true

      try {
        const [fields, rows] = await this.$store.dispatch(
          `${this.storePrefix}view/grid/getCurrentSelection`,
          {
            fields: this.exportableFields,
          }
        )
        const { textData } = this.prepareValuesForCopy(fields, rows, true)
        const csvData = `\uFEFF${this.$papa.unparse(textData)}`

        this.downloadCsvFile(this.exportFilename, csvData)
      } catch (error) {
        notifyIf(error, 'view')
      } finally {
        this.exporting = false
      }
    },
    downloadCsvFile(filename, csvData) {
      const blob = new Blob([csvData], {
        type: 'text/csv;charset=utf-8;',
      })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')

      link.style.display = 'none'
      link.href = url
      link.download = filename

      document.body.appendChild(link)
      link.click()

      setTimeout(() => {
        if (link.parentNode) {
          link.parentNode.removeChild(link)
        }
        window.URL.revokeObjectURL(url)
      }, 0)
    },
  },
}
</script>
