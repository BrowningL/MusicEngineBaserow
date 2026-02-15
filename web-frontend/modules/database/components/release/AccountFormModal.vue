<template>
  <div v-if="open" class="account-modal-overlay" @click.self="cancel">
    <div class="account-modal" @click.stop>
      <!-- Header -->
      <div class="account-modal__header">
        <div class="account-modal__header-left">
          <h1 class="account-modal__title">
            {{ isNew ? 'New Distributor Account' : 'Edit Account' }}
          </h1>
        </div>
        <div class="account-modal__header-actions">
          <button class="account-modal__btn account-modal__btn--ghost" @click="cancel">
            Cancel
          </button>
          <button
            class="account-modal__btn account-modal__btn--primary"
            :disabled="saving || !isValid"
            @click="save"
          >
            <i v-if="saving" class="iconoir-refresh-double account-modal__spin"></i>
            {{ saving ? 'Saving...' : (isNew ? 'Create Account' : 'Save Account') }}
          </button>
        </div>
      </div>

      <!-- Body -->
      <div class="account-modal__body">
        <div class="account-modal__form">
          <!-- Email Address -->
          <div class="account-modal__field">
            <label class="account-modal__label">
              Email Address <span class="account-modal__required">*</span>
            </label>
            <input
              v-model="formData.email_address"
              type="email"
              class="account-modal__input"
              :class="{ 'account-modal__input--error': errors.email_address }"
              placeholder="e.g. artist@distrokid.com"
              @blur="validateField('email_address')"
            />
            <span v-if="errors.email_address" class="account-modal__error">{{ errors.email_address }}</span>
          </div>

          <!-- Platform -->
          <div class="account-modal__field">
            <label class="account-modal__label">
              Distribution Platform <span class="account-modal__required">*</span>
            </label>
            <div class="account-modal__platform-grid">
              <button
                v-for="p in platformOptions"
                :key="p.value"
                class="account-modal__platform-btn"
                :class="{
                  'account-modal__platform-btn--selected': formData.platform === p.value,
                }"
                @click="formData.platform = p.value"
              >
                <i :class="p.icon"></i>
                {{ p.label }}
              </button>
            </div>
          </div>

          <!-- Phone & Address row -->
          <div class="account-modal__row">
            <div class="account-modal__field account-modal__field--half">
              <label class="account-modal__label">Phone Number</label>
              <input
                v-model="formData.phone_number"
                type="tel"
                class="account-modal__input"
                placeholder="+1 555-0123"
              />
            </div>
            <div class="account-modal__field account-modal__field--half">
              <label class="account-modal__label">Address</label>
              <input
                v-model="formData.address"
                type="text"
                class="account-modal__input"
                placeholder="123 Main St, City, State"
              />
            </div>
          </div>

          <!-- GoLogin fields -->
          <div class="account-modal__row">
            <div class="account-modal__field account-modal__field--half">
              <label class="account-modal__label">GoLogin Profile ID</label>
              <input
                v-model="formData.gologin_profile_id"
                type="text"
                class="account-modal__input"
                placeholder="Optional"
              />
              <span class="account-modal__hint">From GoLogin browser manager</span>
            </div>
            <div class="account-modal__field account-modal__field--half">
              <label class="account-modal__label">GoLogin API Token</label>
              <input
                v-model="formData.gologin_api_token"
                type="text"
                class="account-modal__input"
                placeholder="Optional"
              />
            </div>
          </div>

          <!-- Save error -->
          <div v-if="errors._save" class="account-modal__save-error">
            {{ errors._save }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AccountFormModal',
  props: {
    database: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    allFieldsInTable: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      open: false,
      saving: false,
      rowId: null,
      formData: this.getDefaultFormData(),
      errors: {},
      fieldMap: {},
      platformOptions: [
        { value: 'distrokid', label: 'DistroKid', icon: 'iconoir-music-double-note' },
        { value: 'tunecore', label: 'TuneCore', icon: 'iconoir-music-note' },
        { value: 'cdbaby', label: 'CD Baby', icon: 'iconoir-compact-disc' },
      ],
    }
  },
  computed: {
    isNew() {
      return !this.rowId
    },
    isValid() {
      return (
        this.formData.email_address &&
        this.formData.email_address.trim().length > 0 &&
        this.formData.platform
      )
    },
  },
  mounted() {
    document.body.appendChild(this.$el)
    window.addEventListener('keydown', this.handleEscape)
  },
  beforeDestroy() {
    window.removeEventListener('keydown', this.handleEscape)
    if (this.$el.parentNode === document.body) {
      document.body.removeChild(this.$el)
    }
  },
  methods: {
    getDefaultFormData() {
      return {
        email_address: '',
        platform: 'distrokid',
        phone_number: '',
        address: '',
        gologin_profile_id: '',
        gologin_api_token: '',
      }
    },
    handleEscape(e) {
      if (e.key === 'Escape' && this.open) this.cancel()
    },
    buildFieldMap() {
      this.fieldMap = {}
      const nameMap = {
        'email_address': ['email_address', 'email address', 'email'],
        'phone_number': ['phone_number', 'phone number', 'phone'],
        'address': ['address'],
        'gologin_profile_id': ['gologin profile id', 'gologin_profile_id', 'gologin profile'],
        'gologin_api_token': ['gologin api token', 'gologin_api_token'],
      }

      for (const field of this.allFieldsInTable) {
        const fn = field.name.toLowerCase().trim()
        for (const [formKey, aliases] of Object.entries(nameMap)) {
          if (aliases.includes(fn)) {
            this.fieldMap[formKey] = field
            break
          }
        }
      }
    },
    show(rowId, rowData) {
      this.buildFieldMap()
      this.rowId = rowId
      this.formData = this.getDefaultFormData()
      this.errors = {}

      if (rowData) {
        this.populateFromRow(rowData)
      }

      this.open = true
    },
    populateFromRow(row) {
      for (const [formKey, field] of Object.entries(this.fieldMap)) {
        const val = row[`field_${field.id}`]
        if (val === undefined || val === null) continue
        this.formData[formKey] = val
      }
    },
    validateField(fieldName) {
      if (fieldName === 'email_address') {
        if (!this.formData.email_address || !this.formData.email_address.trim()) {
          this.$set(this.errors, 'email_address', 'Email address is required')
        } else {
          this.$delete(this.errors, 'email_address')
        }
      }
    },
    async save() {
      this.validateField('email_address')
      if (Object.keys(this.errors).length) return

      this.saving = true
      try {
        const payload = {}

        for (const [formKey, field] of Object.entries(this.fieldMap)) {
          payload[`field_${field.id}`] = this.formData[formKey] || ''
        }

        const token = this.$store.getters['auth/token']
        const baseUrl = this.$config.PUBLIC_BACKEND_URL || ''

        if (this.rowId) {
          await this.$client.patch(
            `${baseUrl}/api/database/rows/table/${this.table.id}/${this.rowId}/`,
            payload,
            { headers: { Authorization: `JWT ${token}` } }
          )
        } else {
          await this.$client.post(
            `${baseUrl}/api/database/rows/table/${this.table.id}/`,
            payload,
            { headers: { Authorization: `JWT ${token}` } }
          )
        }

        this.$emit('saved')
        this.open = false
      } catch (err) {
        console.error('Failed to save account:', err)
        this.$set(this.errors, '_save', err.message || 'Failed to save. Please try again.')
      } finally {
        this.saving = false
      }
    },
    cancel() {
      this.open = false
      this.$emit('hidden')
    },
  },
}
</script>

<style lang="scss" scoped>
.account-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.account-modal {
  width: 540px;
  max-height: 80vh;
  background: var(--color-neutral-0, #fff);
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.account-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-neutral-200, #e5e7eb);
}

.account-modal__header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.account-modal__title {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  color: var(--color-neutral-900, #111);
}

.account-modal__header-actions {
  display: flex;
  gap: 8px;
}

.account-modal__btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.15s ease;

  &--ghost {
    background: transparent;
    color: var(--color-neutral-500, #6b7280);

    &:hover {
      background: var(--color-neutral-100, #f3f4f6);
    }
  }

  &--primary {
    background: #5190ef;
    color: #fff;

    &:hover {
      background: #4080df;
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}

.account-modal__spin {
  animation: account-spin 0.8s linear infinite;
}

@keyframes account-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.account-modal__body {
  padding: 24px;
  overflow-y: auto;
}

.account-modal__form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.account-modal__field {
  display: flex;
  flex-direction: column;
  gap: 6px;

  &--half {
    flex: 1;
    min-width: 0;
  }
}

.account-modal__row {
  display: flex;
  gap: 16px;
}

.account-modal__label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-neutral-600, #4b5563);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.account-modal__required {
  color: #ef4444;
}

.account-modal__input {
  width: 100%;
  padding: 10px 12px;
  font-size: 14px;
  border: 1px solid var(--color-neutral-200, #e5e7eb);
  border-radius: 8px;
  background: var(--color-neutral-0, #fff);
  color: var(--color-neutral-900, #111);
  transition: all 0.15s ease;
  box-sizing: border-box;

  &:focus {
    outline: none;
    border-color: #5190ef;
    box-shadow: 0 0 0 3px rgba(81, 144, 239, 0.15);
  }

  &--error {
    border-color: #ef4444;
    box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
  }
}

.account-modal__hint {
  font-size: 11px;
  color: var(--color-neutral-400, #9ca3af);
}

.account-modal__error {
  font-size: 11px;
  color: #ef4444;
}

.account-modal__platform-grid {
  display: flex;
  gap: 8px;
}

.account-modal__platform-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  border: 2px solid var(--color-neutral-200, #e5e7eb);
  border-radius: 10px;
  background: var(--color-neutral-0, #fff);
  color: var(--color-neutral-700, #374151);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    border-color: var(--color-neutral-300, #d1d5db);
    background: var(--color-neutral-50, #f9fafb);
  }

  &--selected {
    border-color: #5190ef;
    background: rgba(81, 144, 239, 0.08);
    color: #5190ef;
  }

  i {
    font-size: 16px;
  }
}

.account-modal__save-error {
  padding: 12px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 8px;
  color: #ef4444;
  font-size: 13px;
}
</style>