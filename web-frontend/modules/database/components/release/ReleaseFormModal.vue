<template>
  <div v-if="open" class="release-modal-overlay" @click.self="cancel">
    <div class="release-modal" @click.stop>
      <!-- Header -->
      <div class="release-modal__header">
        <div class="release-modal__header-left">
          <h1 class="release-modal__title">
            {{ isNew ? 'New Release' : (formData.release_title || 'Untitled Release') }}
          </h1>
          <span class="release-modal__status-badge" :class="'release-modal__status-badge--' + (formData.status || 'draft').toLowerCase()">
            {{ formData.status || 'Draft' }}
          </span>
        </div>
        <div class="release-modal__header-actions">
          <button class="release-modal__btn release-modal__btn--ghost" @click="cancel">
            Cancel
          </button>
          <button
            class="release-modal__btn release-modal__btn--primary"
            :disabled="saving || !isValid"
            @click="save"
          >
            <i v-if="saving" class="iconoir-refresh-double release-modal__spin"></i>
            {{ saving ? 'Saving...' : 'Save Release' }}
          </button>
        </div>
      </div>

      <!-- Body -->
      <div class="release-modal__body">
        <!-- Left Column: Form -->
        <div class="release-modal__form">
          <!-- RELEASE INFO -->
          <section class="release-modal__section">
            <div class="release-modal__section-header" @click="toggleSection('info')">
              <i class="iconoir-music-double-note"></i>
              <h2>Release Info</h2>
              <i :class="sections.info ? 'iconoir-nav-arrow-up' : 'iconoir-nav-arrow-down'" class="release-modal__chevron"></i>
            </div>
            <div v-show="sections.info" class="release-modal__section-body">
              <div class="release-modal__field">
                <label class="release-modal__label">
                  Release Title <span class="release-modal__required">*</span>
                </label>
                <input
                  v-model="formData.release_title"
                  type="text"
                  class="release-modal__input"
                  :class="{ 'release-modal__input--error': errors.release_title }"
                  placeholder="e.g. Midnight Dreams (Deluxe)"
                  @blur="validateField('release_title')"
                />
                <span v-if="errors.release_title" class="release-modal__error">{{ errors.release_title }}</span>
              </div>

              <div class="release-modal__row">
                <div class="release-modal__field release-modal__field--half">
                  <label class="release-modal__label">UPC</label>
                  <input
                    v-model="formData.upc"
                    type="text"
                    class="release-modal__input"
                    placeholder="e.g. 0123456789012"
                  />
                  <span class="release-modal__hint">13-digit barcode. Leave blank to auto-generate.</span>
                </div>
                <div class="release-modal__field release-modal__field--half">
                  <label class="release-modal__label">Release Date</label>
                  <input
                    v-model="formData.release_date"
                    type="date"
                    class="release-modal__input"
                  />
                </div>
              </div>

              <div class="release-modal__row">
                <div class="release-modal__field release-modal__field--half">
                  <label class="release-modal__label">Status</label>
                  <select v-model="formData.status" class="release-modal__select">
                    <option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
                  </select>
                </div>
                <div class="release-modal__field release-modal__field--quarter">
                  <label class="release-modal__label release-modal__label--checkbox">
                    <input v-model="formData.previously_released" type="checkbox" class="release-modal__checkbox" />
                    Previously Released
                  </label>
                </div>
                <div class="release-modal__field release-modal__field--quarter">
                  <label class="release-modal__label release-modal__label--checkbox">
                    <input v-model="formData.ready_for_upload" type="checkbox" class="release-modal__checkbox" />
                    Ready for Upload
                  </label>
                </div>
              </div>
            </div>
          </section>

          <!-- CREDITS -->
          <section class="release-modal__section">
            <div class="release-modal__section-header" @click="toggleSection('credits')">
              <i class="iconoir-user-circle"></i>
              <h2>Credits</h2>
              <i :class="sections.credits ? 'iconoir-nav-arrow-up' : 'iconoir-nav-arrow-down'" class="release-modal__chevron"></i>
            </div>
            <div v-show="sections.credits" class="release-modal__section-body">
              <!-- Default Songwriter -->
              <div class="release-modal__credit-group">
                <h3 class="release-modal__sub-label">Default Songwriter</h3>
                <div class="release-modal__row">
                  <div class="release-modal__field release-modal__field--third">
                    <input v-model="formData.songwriter_first" type="text" class="release-modal__input" placeholder="First name" />
                  </div>
                  <div class="release-modal__field release-modal__field--third">
                    <input v-model="formData.songwriter_middle" type="text" class="release-modal__input" placeholder="Middle name" />
                  </div>
                  <div class="release-modal__field release-modal__field--third">
                    <input v-model="formData.songwriter_last" type="text" class="release-modal__input" placeholder="Last name" />
                  </div>
                </div>
              </div>

              <!-- Default Performer -->
              <div class="release-modal__credit-group">
                <h3 class="release-modal__sub-label">Default Performer</h3>
                <div class="release-modal__row">
                  <div class="release-modal__field release-modal__field--half">
                    <input v-model="formData.performer_name" type="text" class="release-modal__input" placeholder="Performer name" />
                  </div>
                  <div class="release-modal__field release-modal__field--half">
                    <select v-model="formData.performer_role" class="release-modal__select">
                      <option value="">Select role...</option>
                      <option v-for="r in creditRoles" :key="r" :value="r">{{ r }}</option>
                    </select>
                  </div>
                </div>
              </div>

              <!-- Default Producer -->
              <div class="release-modal__credit-group">
                <h3 class="release-modal__sub-label">Default Producer</h3>
                <div class="release-modal__row">
                  <div class="release-modal__field release-modal__field--half">
                    <input v-model="formData.producer_name" type="text" class="release-modal__input" placeholder="Producer name" />
                  </div>
                  <div class="release-modal__field release-modal__field--half">
                    <select v-model="formData.producer_role" class="release-modal__select">
                      <option value="">Select role...</option>
                      <option v-for="r in producerRoles" :key="r" :value="r">{{ r }}</option>
                    </select>
                  </div>
                </div>
              </div>

              <!-- Artists Link -->
              <div class="release-modal__credit-group">
                <h3 class="release-modal__sub-label">Artists</h3>
                <div class="release-modal__artist-picker">
                  <input
                    v-model="artistSearch"
                    type="text"
                    class="release-modal__input"
                    placeholder="Search artists..."
                    @input="searchArtists"
                    @focus="showArtistDropdown = true"
                  />
                  <div v-if="showArtistDropdown && artistResults.length" class="release-modal__dropdown">
                    <div
                      v-for="artist in artistResults"
                      :key="artist.id"
                      class="release-modal__dropdown-item"
                      @click="addArtist(artist)"
                    >
                      {{ artist.value }}
                    </div>
                  </div>
                  <div class="release-modal__tags">
                    <span v-for="artist in formData.artists" :key="artist.id" class="release-modal__tag">
                      {{ artist.value }}
                      <i class="iconoir-xmark release-modal__tag-remove" @click="removeArtist(artist)"></i>
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- DISTRIBUTION SETTINGS -->
          <section class="release-modal__section">
            <div class="release-modal__section-header" @click="toggleSection('distribution')">
              <i class="iconoir-globe"></i>
              <h2>Distribution Settings</h2>
              <i :class="sections.distribution ? 'iconoir-nav-arrow-up' : 'iconoir-nav-arrow-down'" class="release-modal__chevron"></i>
            </div>
            <div v-show="sections.distribution" class="release-modal__section-body">
              <div class="release-modal__row">
                <div class="release-modal__field release-modal__field--half">
                  <label class="release-modal__label">Genre</label>
                  <select v-model="formData.genre" class="release-modal__select">
                    <option value="">Select genre...</option>
                    <option v-for="g in genreOptions" :key="g" :value="g">{{ g }}</option>
                  </select>
                </div>
                <div class="release-modal__field release-modal__field--half">
                  <label class="release-modal__label">Genre 2 <span class="release-modal__optional">(optional)</span></label>
                  <select v-model="formData.genre2" class="release-modal__select">
                    <option value="">None</option>
                    <option v-for="g in genreOptions" :key="g" :value="g">{{ g }}</option>
                  </select>
                </div>
              </div>

              <div class="release-modal__row">
                <div class="release-modal__field release-modal__field--third">
                  <label class="release-modal__label">Language</label>
                  <select v-model="formData.language" class="release-modal__select">
                    <option value="">Select...</option>
                    <option v-for="l in languageOptions" :key="l.code" :value="l.code">{{ l.name }}</option>
                  </select>
                </div>
                <div class="release-modal__field release-modal__field--third">
                  <label class="release-modal__label">Label Name</label>
                  <input v-model="formData.label_name" type="text" class="release-modal__input" placeholder="Label name" />
                </div>
                <div class="release-modal__field release-modal__field--third">
                  <label class="release-modal__label">Copyright Year</label>
                  <input v-model="formData.copyright_year" type="text" class="release-modal__input" placeholder="e.g. 2026" maxlength="4" />
                </div>
              </div>

              <div class="release-modal__row">
                <div class="release-modal__field release-modal__field--quarter">
                  <label class="release-modal__label release-modal__label--checkbox">
                    <input v-model="formData.explicit" type="checkbox" class="release-modal__checkbox" />
                    Explicit Content
                  </label>
                </div>
                <div class="release-modal__field release-modal__field--three-quarter">
                  <label class="release-modal__label">Territorial Rights</label>
                  <select v-model="formData.territorial_rights" class="release-modal__select">
                    <option value="worldwide">Worldwide</option>
                    <option value="us_only">US Only</option>
                    <option value="eu_only">EU Only</option>
                    <option value="uk_only">UK Only</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>
              </div>
            </div>
          </section>

          <!-- TRACKS -->
          <section class="release-modal__section">
            <div class="release-modal__section-header" @click="toggleSection('tracks')">
              <i class="iconoir-playlist"></i>
              <h2>Tracks</h2>
              <span class="release-modal__count">{{ formData.tracks.length }}</span>
              <i :class="sections.tracks ? 'iconoir-nav-arrow-up' : 'iconoir-nav-arrow-down'" class="release-modal__chevron"></i>
            </div>
            <div v-show="sections.tracks" class="release-modal__section-body">
              <!-- Track List -->
              <div v-if="formData.tracks.length" class="release-modal__track-list">
                <div class="release-modal__track-header">
                  <span class="release-modal__track-col release-modal__track-col--num">#</span>
                  <span class="release-modal__track-col release-modal__track-col--title">Title</span>
                  <span class="release-modal__track-col release-modal__track-col--isrc">ISRC</span>
                  <span class="release-modal__track-col release-modal__track-col--duration">Duration</span>
                  <span class="release-modal__track-col release-modal__track-col--actions"></span>
                </div>
                <div
                  v-for="(track, index) in formData.tracks"
                  :key="index"
                  class="release-modal__track-row"
                  :class="{ 'release-modal__track-row--editing': editingTrackIndex === index }"
                >
                  <template v-if="editingTrackIndex !== index">
                    <span class="release-modal__track-col release-modal__track-col--num">{{ track.track_number || index + 1 }}</span>
                    <span class="release-modal__track-col release-modal__track-col--title">{{ track.track_title || 'Untitled' }}</span>
                    <span class="release-modal__track-col release-modal__track-col--isrc">
                      <code v-if="track.isrc">{{ track.isrc }}</code>
                      <span v-else class="release-modal__muted">—</span>
                    </span>
                    <span class="release-modal__track-col release-modal__track-col--duration">{{ track.duration || '—' }}</span>
                    <span class="release-modal__track-col release-modal__track-col--actions">
                      <button class="release-modal__icon-btn" title="Edit track" @click="editTrack(index)">
                        <i class="iconoir-edit-pencil"></i>
                      </button>
                      <template v-if="confirmingDeleteTrackIndex !== index">
                        <button class="release-modal__icon-btn release-modal__icon-btn--danger" title="Remove track" @click="confirmingDeleteTrackIndex = index">
                          <i class="iconoir-bin"></i>
                        </button>
                      </template>
                      <span v-else class="release-modal__confirm-delete">
                        Delete?
                        <button class="release-modal__confirm-btn release-modal__confirm-btn--yes" @click="removeTrack(index)">Yes</button>
                        <button class="release-modal__confirm-btn release-modal__confirm-btn--no" @click="confirmingDeleteTrackIndex = -1">No</button>
                      </span>
                    </span>
                  </template>

                  <!-- Inline Track Edit Form -->
                  <template v-else>
                    <div class="release-modal__track-edit">
                      <div class="release-modal__row">
                        <div class="release-modal__field release-modal__field--small">
                          <label class="release-modal__label">Track #</label>
                          <input v-model.number="track.track_number" type="number" class="release-modal__input" min="1" />
                        </div>
                        <div class="release-modal__field" style="flex: 2">
                          <label class="release-modal__label">Title <span class="release-modal__required">*</span></label>
                          <input v-model="track.track_title" type="text" class="release-modal__input" placeholder="Track title" />
                        </div>
                        <div class="release-modal__field" style="flex: 1">
                          <label class="release-modal__label">ISRC</label>
                          <input v-model="track.isrc" type="text" class="release-modal__input" placeholder="ISRC code" />
                        </div>
                        <div class="release-modal__field" style="flex: 1">
                          <label class="release-modal__label">Duration</label>
                          <input v-model="track.duration" type="text" class="release-modal__input" placeholder="3:45" />
                        </div>
                      </div>

                      <div class="release-modal__row">
                        <div class="release-modal__field release-modal__field--quarter">
                          <label class="release-modal__label release-modal__label--checkbox">
                            <input v-model="track.explicit" type="checkbox" class="release-modal__checkbox" />
                            Explicit
                          </label>
                        </div>
                        <div class="release-modal__field release-modal__field--quarter">
                          <label class="release-modal__label release-modal__label--checkbox">
                            <input v-model="track.instrumental" type="checkbox" class="release-modal__checkbox" />
                            Instrumental
                          </label>
                        </div>
                      </div>

                      <!-- Track Credits (inherit from release) -->
                      <div class="release-modal__row">
                        <div class="release-modal__field release-modal__field--third">
                          <label class="release-modal__label">Songwriter</label>
                          <input v-model="track.songwriter" type="text" class="release-modal__input"
                            :placeholder="defaultSongwriter || 'Songwriter name'" />
                          <span class="release-modal__hint" v-if="defaultSongwriter">Inherited from release</span>
                        </div>
                        <div class="release-modal__field release-modal__field--third">
                          <label class="release-modal__label">Performer</label>
                          <input v-model="track.performer" type="text" class="release-modal__input"
                            :placeholder="formData.performer_name || 'Performer name'" />
                        </div>
                        <div class="release-modal__field release-modal__field--third">
                          <label class="release-modal__label">Producer</label>
                          <input v-model="track.producer" type="text" class="release-modal__input"
                            :placeholder="formData.producer_name || 'Producer name'" />
                        </div>
                      </div>

                      <!-- Audio Upload -->
                      <div class="release-modal__row">
                        <div class="release-modal__field">
                          <label class="release-modal__label">Audio File</label>
                          <div class="release-modal__file-upload">
                            <input type="file" accept="audio/*" @change="handleAudioUpload($event, index)" />
                            <span v-if="track.audio_filename" class="release-modal__file-name">
                              <i class="iconoir-check-circle"></i> {{ track.audio_filename }}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div class="release-modal__track-edit-actions">
                        <button class="release-modal__btn release-modal__btn--small release-modal__btn--primary" @click="editingTrackIndex = -1">
                          Done
                        </button>
                      </div>
                    </div>
                  </template>
                </div>
              </div>

              <div v-else class="release-modal__empty-tracks">
                <i class="iconoir-playlist"></i>
                <p>No tracks yet. Add your first track below.</p>
              </div>

              <button class="release-modal__btn release-modal__btn--outline" @click="addTrack">
                <i class="iconoir-plus"></i> Add Track
              </button>
            </div>
          </section>
        </div>

        <!-- Right Column: Cover Art & Quick Info -->
        <div class="release-modal__sidebar">
          <!-- Cover Art -->
          <div class="release-modal__artwork">
            <div v-if="coverArtPreview" class="release-modal__artwork-preview">
              <img :src="coverArtPreview" alt="Cover Art" />
              <button class="release-modal__artwork-remove" @click="removeCoverArt" title="Remove cover art">
                <i class="iconoir-xmark"></i>
              </button>
            </div>
            <div v-else class="release-modal__artwork-placeholder" @click="$refs.coverInput.click()">
              <i class="iconoir-media-image"></i>
              <span>Upload Cover Art</span>
              <span class="release-modal__hint">3000×3000px recommended</span>
            </div>
            <input
              ref="coverInput"
              type="file"
              accept="image/*"
              style="display: none"
              @change="handleCoverUpload"
            />
            <button v-if="!coverArtPreview" class="release-modal__btn release-modal__btn--outline release-modal__btn--full" @click="$refs.coverInput.click()">
              <i class="iconoir-upload"></i> Choose Image
            </button>
          </div>

          <!-- Quick Stats -->
          <div class="release-modal__quick-stats">
            <div class="release-modal__stat">
              <span class="release-modal__stat-label">Tracks</span>
              <span class="release-modal__stat-value">{{ formData.tracks.length }}</span>
            </div>
            <div class="release-modal__stat">
              <span class="release-modal__stat-label">Status</span>
              <span class="release-modal__stat-value">{{ formData.status || 'Draft' }}</span>
            </div>
            <div class="release-modal__stat" v-if="formData.release_date">
              <span class="release-modal__stat-label">Release</span>
              <span class="release-modal__stat-value">{{ formattedDate }}</span>
            </div>
            <div class="release-modal__stat" v-if="formData.upc">
              <span class="release-modal__stat-label">UPC</span>
              <span class="release-modal__stat-value release-modal__stat-value--mono">{{ formData.upc }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ReleaseFormModal',
  props: {
    database: { type: Object, required: true },
    table: { type: Object, required: true },
    allFieldsInTable: { type: Array, required: true },
    rows: { type: Array, default: () => [] },
  },
  data() {
    return {
      open: false,
      saving: false,
      rowId: null,
      editingTrackIndex: -1,
      confirmingDeleteTrackIndex: -1,
      artistSearch: '',
      artistResults: [],
      showArtistDropdown: false,
      coverArtFile: null,
      coverArtPreview: null,
      sections: {
        info: true,
        credits: true,
        distribution: false,
        tracks: true,
      },
      errors: {},
      formData: this.getDefaultFormData(),
      statusOptions: ['Draft', 'Submitted', 'Pending', 'Approved', 'Rejected', 'Taken Down'],
      creditRoles: ['Primary Artist', 'Featured Artist', 'Performer', 'Vocalist', 'Instrumentalist'],
      producerRoles: ['Producer', 'Executive Producer', 'Co-Producer', 'Mix Engineer', 'Mastering Engineer'],
      genreOptions: [
        'Pop', 'Rock', 'Hip-Hop/Rap', 'R&B/Soul', 'Electronic', 'Dance',
        'Country', 'Jazz', 'Classical', 'Latin', 'Reggae', 'Blues',
        'Folk', 'Indie', 'Alternative', 'Metal', 'Punk', 'Gospel',
        'World', 'Ambient', 'Soundtrack', 'Children\'s', 'Comedy', 'Spoken Word',
      ],
      languageOptions: [
        { code: 'en', name: 'English' },
        { code: 'es', name: 'Spanish' },
        { code: 'fr', name: 'French' },
        { code: 'de', name: 'German' },
        { code: 'it', name: 'Italian' },
        { code: 'pt', name: 'Portuguese' },
        { code: 'ja', name: 'Japanese' },
        { code: 'ko', name: 'Korean' },
        { code: 'zh', name: 'Chinese' },
        { code: 'ar', name: 'Arabic' },
        { code: 'hi', name: 'Hindi' },
        { code: 'ru', name: 'Russian' },
      ],
      // Field mapping: Baserow field name → formData key
      fieldMap: {},
    }
  },
  computed: {
    isNew() {
      return !this.rowId
    },
    isValid() {
      return !!(this.formData.release_title && this.formData.release_title.trim())
    },
    defaultSongwriter() {
      const parts = [this.formData.songwriter_first, this.formData.songwriter_middle, this.formData.songwriter_last].filter(Boolean)
      return parts.join(' ')
    },
    formattedDate() {
      if (!this.formData.release_date) return ''
      try {
        return new Date(this.formData.release_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
      } catch {
        return this.formData.release_date
      }
    },
  },
  mounted() {
    document.addEventListener('keydown', this.handleEscape)
    // Move modal to document.body to render as a portal (escape grid overflow)
    this.$el.parentNode.removeChild(this.$el)
    document.body.appendChild(this.$el)
  },
  beforeDestroy() {
    document.removeEventListener('keydown', this.handleEscape)
    // Clean up portal
    if (this.$el.parentNode === document.body) {
      document.body.removeChild(this.$el)
    }
  },
  methods: {
    getDefaultFormData() {
      return {
        release_title: '',
        upc: '',
        release_date: '',
        previously_released: false,
        status: 'Draft',
        ready_for_upload: false,
        songwriter_first: '',
        songwriter_middle: '',
        songwriter_last: '',
        performer_name: '',
        performer_role: '',
        producer_name: '',
        producer_role: '',
        artists: [],
        genre: '',
        genre2: '',
        language: '',
        explicit: false,
        label_name: '',
        copyright_year: '',
        territorial_rights: 'worldwide',
        tracks: [],
      }
    },
    handleEscape(e) {
      if (e.key === 'Escape' && this.open) this.cancel()
    },
    toggleSection(name) {
      this.sections[name] = !this.sections[name]
    },
    /**
     * Build field mapping from Baserow fields to our form keys.
     * Uses fuzzy name matching to handle variations.
     */
    buildFieldMap() {
      this.fieldMap = {}
      const nameMap = {
        'release_title': ['release_title', 'release title', 'title', 'name'],
        'upc': ['upc', 'barcode'],
        'release_date': ['release_date', 'release date', 'date'],
        'previously_released': ['previously_released', 'previously released'],
        'status': ['status'],
        'ready_for_upload': ['ready_for_upload', 'ready for upload', 'ready'],
        'genre': ['genre'],
        'genre2': ['genre 2', 'genre2', 'secondary genre'],
        'language': ['language'],
        'explicit': ['explicit', 'explicit content'],
        'label_name': ['label_name', 'label name', 'label'],
        'copyright_year': ['copyright_year', 'copyright year', 'copyright'],
        'territorial_rights': ['territorial_rights', 'territorial rights', 'territory'],
        'songwriter_first': ['songwriter_first', 'songwriter first', 'default songwriter first'],
        'songwriter_middle': ['songwriter_middle', 'songwriter middle', 'default songwriter middle'],
        'songwriter_last': ['songwriter_last', 'songwriter last', 'default songwriter last'],
        'performer_name': ['performer_name', 'performer name', 'default performer'],
        'producer_name': ['producer_name', 'producer name', 'default producer'],
        'cover_art': ['cover_art', 'cover art', 'artwork', 'cover'],
        'artists': ['artists', 'artist'],
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
    /**
     * Open the modal for an existing row or a new release.
     */
    show(rowId, rowData) {
      this.buildFieldMap()
      this.rowId = rowId
      this.formData = this.getDefaultFormData()
      this.errors = {}
      this.editingTrackIndex = -1
      this.coverArtPreview = null

      if (rowData) {
        this.populateFromRow(rowData)
      }

      this.open = true
    },
    /**
     * Map Baserow row data to our form.
     */
    populateFromRow(row) {
      for (const [formKey, field] of Object.entries(this.fieldMap)) {
        const val = row[`field_${field.id}`]
        if (val === undefined || val === null) continue

        if (formKey === 'artists' && Array.isArray(val)) {
          this.formData.artists = val.map(v => ({ id: v.id, value: v.value }))
        } else if (formKey === 'cover_art' && Array.isArray(val) && val.length) {
          this.coverArtPreview = val[0].thumbnails?.card_cover?.url || val[0].url
        } else if (field.type === 'boolean') {
          this.formData[formKey] = !!val
        } else if (field.type === 'date') {
          this.formData[formKey] = val ? val.split('T')[0] : ''
        } else if (field.type === 'single_select' && val) {
          this.formData[formKey] = typeof val === 'object' ? val.value : val
        } else {
          this.formData[formKey] = val
        }
      }

      // Load tracks from linked rows if available
      const tracksField = this.allFieldsInTable.find(f =>
        f.type === 'link_row' && f.name.toLowerCase().includes('track')
      )
      if (tracksField && row[`field_${tracksField.id}`]) {
        // Tracks are link_row references — we'll load them as stubs for now
        const linkedTracks = row[`field_${tracksField.id}`]
        if (Array.isArray(linkedTracks)) {
          this.formData.tracks = linkedTracks.map((t, i) => ({
            id: t.id,
            track_number: i + 1,
            track_title: t.value || `Track ${i + 1}`,
            isrc: '',
            duration: '',
            explicit: false,
            instrumental: false,
            songwriter: '',
            performer: '',
            producer: '',
            audio_filename: '',
          }))
        }
      }
    },
    /**
     * Validate a single field.
     */
    validateField(fieldName) {
      if (fieldName === 'release_title') {
        if (!this.formData.release_title || !this.formData.release_title.trim()) {
          this.$set(this.errors, 'release_title', 'Release title is required')
        } else {
          this.$delete(this.errors, 'release_title')
        }
      }
    },
    /**
     * Save the release back to Baserow via API.
     */
    async save() {
      this.validateField('release_title')
      if (Object.keys(this.errors).length) return

      this.saving = true
      try {
        const payload = {}

        for (const [formKey, field] of Object.entries(this.fieldMap)) {
          if (formKey === 'artists') {
            payload[`field_${field.id}`] = this.formData.artists.map(a => a.id)
          } else if (formKey === 'cover_art') {
            // File uploads handled separately
            continue
          } else if (field.type === 'single_select') {
            // For single_select, send the option value
            payload[`field_${field.id}`] = this.formData[formKey] || null
          } else if (field.type === 'boolean') {
            payload[`field_${field.id}`] = !!this.formData[formKey]
          } else if (field.type === 'date') {
            payload[`field_${field.id}`] = this.formData[formKey] || null
          } else {
            payload[`field_${field.id}`] = this.formData[formKey]
          }
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
        this.$store.dispatch('toast/success', {
          title: this.rowId ? 'Release Updated' : 'Release Created',
          message: `"${this.formData.release_title}" has been saved successfully.`,
        })
        this.open = false
      } catch (err) {
        console.error('Failed to save release:', err)
        this.$set(this.errors, '_save', err.message || 'Failed to save. Please try again.')
      } finally {
        this.saving = false
      }
    },
    cancel() {
      this.open = false
      this.$emit('hidden')
    },
    // Track methods
    addTrack() {
      const num = this.formData.tracks.length + 1
      this.formData.tracks.push({
        track_number: num,
        track_title: '',
        isrc: '',
        duration: '',
        explicit: false,
        instrumental: false,
        songwriter: this.defaultSongwriter,
        performer: this.formData.performer_name,
        producer: this.formData.producer_name,
        audio_filename: '',
      })
      this.editingTrackIndex = this.formData.tracks.length - 1
    },
    editTrack(index) {
      this.editingTrackIndex = index
    },
    removeTrack(index) {
      this.formData.tracks.splice(index, 1)
      if (this.editingTrackIndex === index) this.editingTrackIndex = -1
      this.confirmingDeleteTrackIndex = -1
      // Renumber
      this.formData.tracks.forEach((t, i) => { t.track_number = i + 1 })
    },
    handleAudioUpload(event, trackIndex) {
      const file = event.target.files[0]
      if (file) {
        this.formData.tracks[trackIndex].audio_filename = file.name
      }
    },
    // Cover art methods
    handleCoverUpload(event) {
      const file = event.target.files[0]
      if (file) {
        this.coverArtFile = file
        this.coverArtPreview = URL.createObjectURL(file)
      }
    },
    removeCoverArt() {
      this.coverArtFile = null
      this.coverArtPreview = null
    },
    // Artist search
    async searchArtists() {
      if (!this.artistSearch || this.artistSearch.length < 2) {
        this.artistResults = []
        return
      }
      // Find the artists link_row field to get the linked table
      const artistField = this.fieldMap.artists
      if (!artistField) {
        this.artistResults = []
        return
      }
      try {
        const token = this.$store.getters['auth/token']
        const baseUrl = this.$config.PUBLIC_BACKEND_URL || ''
        const linkedTableId = artistField.link_row_table_id
        const response = await this.$client.get(
          `${baseUrl}/api/database/rows/table/${linkedTableId}/`,
          {
            params: { search: this.artistSearch, size: 10 },
            headers: { Authorization: `JWT ${token}` },
          }
        )
        this.artistResults = (response.data.results || []).map(r => ({
          id: r.id,
          value: r[Object.keys(r).find(k => k.startsWith('field_'))] || `Row ${r.id}`,
        }))
      } catch {
        this.artistResults = []
      }
    },
    addArtist(artist) {
      if (!this.formData.artists.find(a => a.id === artist.id)) {
        this.formData.artists.push(artist)
      }
      this.artistSearch = ''
      this.artistResults = []
      this.showArtistDropdown = false
    },
    removeArtist(artist) {
      this.formData.artists = this.formData.artists.filter(a => a.id !== artist.id)
    },
  },
}
</script>

<style lang="scss" scoped>
// ── Variables ──
$primary: #3b82f6;
$primary-hover: #2563eb;
$danger: #e74c3c;
$success: #00b894;
$warning: #fdcb6e;
$radius: 12px;
$radius-sm: 8px;
$shadow: 0 20px 60px rgba(0, 0, 0, 0.15);

// ── Overlay ──
.release-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 99999;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.2s ease;
  overflow: hidden;
  color: var(--text-primary);
}

// ── Modal Container ──
.release-modal {
  background: var(--bg-elevated);
  border-radius: $radius;
  box-shadow: $shadow;
  width: 95vw;
  max-width: 1400px;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s ease;

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 28px;
    border-bottom: 1px solid var(--border-color);
    flex-shrink: 0;

    &-left {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }
    &-actions {
      display: flex;
      gap: 8px;
      flex-shrink: 0;
    }
  }

  &__title {
    font-size: 20px;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__status-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    white-space: nowrap;

    &--draft { background: #edf2f7; color: #718096; }
    &--submitted { background: #ebf8ff; color: #3182ce; }
    &--pending { background: #fefcbf; color: #d69e2e; }
    &--approved { background: #f0fff4; color: #38a169; }
    &--rejected { background: #fed7d7; color: #e53e3e; }
    &--taken\ down { background: #feebc8; color: #dd6b20; }
  }

  // ── Body ──
  &__body {
    display: flex;
    gap: 24px;
    padding: 24px 28px;
    overflow-y: auto;
    flex: 1;
    min-height: 0;
  }

  &__form {
    flex: 1;
    min-width: 0;
  }

  &__sidebar {
    width: 320px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  // ── Sections ──
  &__section {
    margin-bottom: 16px;
    border: 1px solid var(--border-color);
    border-radius: $radius-sm;
    overflow: hidden;

    &-header {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 14px 18px;
      background: var(--bg-tertiary);
      cursor: pointer;
      user-select: none;
      transition: background 0.15s;

      &:hover { background: var(--bg-hover); }

      h2 {
        margin: 0;
        font-size: 14px;
        font-weight: 600;
        color: var(--text-primary);
        flex: 1;
      }

      i { color: var(--text-muted); font-size: 16px; }
    }

    &-body {
      padding: 18px;
    }
  }

  &__chevron {
    margin-left: auto;
  }

  &__count {
    background: $primary;
    color: white;
    padding: 1px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
  }

  // ── Form Elements ──
  &__field {
    margin-bottom: 14px;
    flex: 1;

    &--half { flex: 0 0 calc(50% - 6px); }
    &--third { flex: 0 0 calc(33.33% - 8px); }
    &--quarter { flex: 0 0 calc(25% - 9px); }
    &--three-quarter { flex: 0 0 calc(75% - 3px); }
    &--small { flex: 0 0 70px; }
  }

  &__row {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }

  &__label {
    display: block;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 5px;
    letter-spacing: 0.3px;

    &--checkbox {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      font-weight: 500;
      margin-top: 24px;
    }
  }

  &__required { color: $danger; }
  &__optional { color: var(--text-muted); font-weight: 400; }

  &__input, &__select {
    width: 100%;
    padding: 9px 12px;
    border: 1.5px solid var(--border-color);
    border-radius: 6px;
    font-size: 13px;
    color: var(--text-primary);
    background: var(--bg-elevated);
    transition: border-color 0.15s, box-shadow 0.15s;
    outline: none;
    box-sizing: border-box;

    &:focus {
      border-color: $primary;
      box-shadow: 0 0 0 3px rgba($primary, 0.1);
    }

    &--error {
      border-color: $danger;
      &:focus { box-shadow: 0 0 0 3px rgba($danger, 0.1); }
    }

    &::placeholder { color: var(--text-muted); }
  }

  &__select {
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg width='10' height='6' viewBox='0 0 10 6' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1L5 5L9 1' stroke='%23A0AEC0' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 12px center;
    padding-right: 32px;
  }

  &__checkbox {
    width: 16px;
    height: 16px;
    accent-color: $primary;
  }

  &__hint {
    display: block;
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 4px;
  }

  &__error {
    display: block;
    font-size: 11px;
    color: $danger;
    margin-top: 4px;
  }

  &__sub-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 0 0 10px;
  }

  &__credit-group {
    margin-bottom: 18px;
    padding-bottom: 18px;
    border-bottom: 1px solid var(--border-color);

    &:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
  }

  // ── Artist Picker ──
  &__artist-picker {
    position: relative;
  }

  &__dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: var(--bg-elevated);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    z-index: 10;
    max-height: 200px;
    overflow-y: auto;
  }

  &__dropdown-item {
    padding: 8px 12px;
    font-size: 13px;
    cursor: pointer;
    transition: background 0.1s;

    &:hover { background: var(--bg-tertiary); }
  }

  &__tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 8px;
  }

  &__tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    background: lighten($primary, 32%);
    color: $primary;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
  }

  &__tag-remove {
    cursor: pointer;
    font-size: 10px;
    opacity: 0.7;
    &:hover { opacity: 1; }
  }

  // ── Tracks ──
  &__track-list {
    margin-bottom: 12px;
  }

  &__track-header {
    display: flex;
    padding: 8px 12px;
    font-size: 11px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid var(--border-color);
  }

  &__track-row {
    display: flex;
    align-items: center;
    padding: 10px 12px;
    border-bottom: 1px solid var(--border-color);
    font-size: 13px;
    transition: background 0.1s;

    &:hover { background: var(--bg-tertiary); }

    &--editing {
      display: block;
      background: var(--bg-tertiary);
      padding: 16px;
    }
  }

  &__track-col {
    &--num { width: 40px; color: var(--text-muted); font-weight: 600; }
    &--title { flex: 2; font-weight: 500; }
    &--isrc { flex: 1; code { font-size: 11px; background: var(--bg-tertiary); padding: 2px 6px; border-radius: 3px; } }
    &--duration { width: 60px; text-align: right; color: var(--text-muted); }
    &--actions { min-width: 60px; text-align: right; display: flex; gap: 4px; justify-content: flex-end; flex-shrink: 0; }
  }

  &__muted { color: var(--text-muted); }

  &__track-edit {
    width: 100%;

    &-actions {
      margin-top: 12px;
      display: flex;
      justify-content: flex-end;
    }
  }

  &__empty-tracks {
    text-align: center;
    padding: 32px 16px;
    color: var(--text-muted);

    i { font-size: 32px; display: block; margin-bottom: 8px; }
    p { margin: 0; font-size: 13px; }
  }

  // ── Artwork ──
  &__artwork {
    &-preview {
      position: relative;
      border-radius: $radius-sm;
      overflow: hidden;
      border: 1px solid var(--border-color);

      img {
        width: 100%;
        display: block;
        aspect-ratio: 1;
        object-fit: cover;
      }
    }

    &-remove {
      position: absolute;
      top: 8px;
      right: 8px;
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: rgba(0, 0, 0, 0.6);
      color: white;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      transition: background 0.15s;

      &:hover { background: rgba(0, 0, 0, 0.8); }
    }

    &-placeholder {
      border: 2px dashed var(--border-color);
      border-radius: $radius-sm;
      padding: 36px 20px;
      text-align: center;
      cursor: pointer;
      transition: border-color 0.15s, background 0.15s;

      &:hover {
        border-color: $primary;
        background: rgba($primary, 0.02);
      }

      i {
        display: block;
        font-size: 40px;
        color: var(--text-muted);
        margin-bottom: 8px;
      }

      span {
        display: block;
        font-size: 13px;
        color: var(--text-muted);
        font-weight: 500;
      }
    }
  }

  // ── Quick Stats ──
  &__quick-stats {
    background: var(--bg-tertiary);
    border-radius: $radius-sm;
    padding: 16px;
  }

  &__stat {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;

    &:not(:last-child) { border-bottom: 1px solid var(--border-color); }

    &-label { font-size: 12px; color: var(--text-muted); }
    &-value {
      font-size: 13px;
      font-weight: 600;
      color: var(--text-primary);

      &--mono { font-family: monospace; font-size: 11px; }
    }
  }

  // ── Buttons ──
  &__btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 9px 18px;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;

    &--primary {
      background: $primary;
      color: white;
      &:hover:not(:disabled) { background: $primary-hover; }
      &:disabled { opacity: 0.5; cursor: not-allowed; }
    }

    &--ghost {
      background: transparent;
      color: var(--text-muted);
      &:hover { color: var(--text-primary); background: var(--bg-tertiary); }
    }

    &--outline {
      background: transparent;
      border: 1.5px solid var(--border-color);
      color: var(--text-primary);
      &:hover { border-color: $primary; color: $primary; }
    }

    &--full { width: 100%; justify-content: center; margin-top: 8px; }

    &--small { padding: 6px 14px; font-size: 12px; }
  }

  &__icon-btn {
    width: 28px;
    height: 28px;
    border: none;
    background: transparent;
    border-radius: 4px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
    transition: all 0.1s;

    &:hover { background: var(--bg-tertiary); color: var(--text-primary); }
    &--danger:hover { color: $danger; background: rgba($danger, 0.08); }
  }

  &__file-upload {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  &__file-name {
    font-size: 12px;
    color: $success;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  &__spin {
    animation: spin 1s linear infinite;
  }

  &__confirm-delete {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    font-weight: 600;
    color: $danger;
    white-space: nowrap;
  }

  &__confirm-btn {
    padding: 2px 8px;
    border: none;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.1s;

    &--yes {
      background: rgba($danger, 0.1);
      color: $danger;
      &:hover { background: rgba($danger, 0.2); }
    }

    &--no {
      background: var(--bg-tertiary);
      color: var(--text-muted);
      &:hover { background: var(--bg-hover); }
    }
  }
}

// ── Animations ──
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// ── Responsive ──
@media (max-width: 768px) {
  .release-modal {
    width: 100vw;
    max-width: 100vw;
    max-height: 100vh;
    border-radius: 0;

    &__body {
      flex-direction: column-reverse;
    }

    &__sidebar {
      width: 100%;
      flex-direction: row;
      gap: 16px;
    }

    &__artwork {
      width: 120px;
      flex-shrink: 0;
    }

    &__quick-stats {
      flex: 1;
    }
  }
}
</style>
