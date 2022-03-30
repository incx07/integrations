const AddIntegrationButton = {
    delimiters: ['[[', ']]'],
    props: ['integration_name', 'logo', 'display_name'],
    computed: {
        modal_target() {
            return `#${this.integration_name}_integration`
        }
    },
    template: `
        <div class="btn btn-action btn-lg d-flex align-items-center integration_add"
             data-toggle="modal"
             :data-target="modal_target"
        >
            <div style="font-size: 20px"><i class="fa fa-plus"></i></div>
            <div class="col-2" v-html="logo"></div>
            <div class="col">[[ display_name ]]</div>
        </div>
    `
}
vueApp.component('add-integration-button', AddIntegrationButton)

const TestConnectionButton = {
    delimiters: ['[[', ']]'],
    props: ['error', 'apiPath', 'is_fetching', 'body_data'],
    emits: ['update:is_fetching', 'handleError'],
    data() {
        return {
            status: 0,
        }
    },
    computed: {
        test_connection_class() {
            if (200 <= this.status && this.status < 300) {
                return 'btn-success'
            } else if (this.status > 0) {
                return 'btn-warning'
            } else {
                return 'btn-secondary'
            }
        },
    },
    template: `
        <button type="button" class="btn btn-sm mt-3"
                @click="test_connection"
                :class="[{disabled: is_fetching, updating: is_fetching, 'is-invalid': error}, test_connection_class]"
        >
            Test connection
        </button>
        <div class="invalid-feedback">[[ error ]]</div>
    `,
    watch: {
        is_fetching(newState, oldState) {
            console.log('watch is_fetching', newState)
            if (newState) {
                this.status = 0
            }
        }
    },
    methods: {
        test_connection() {
            this.$emit('update:is_fetching', true)
            fetch(this.apiPath, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(this.body_data)
            }).then(response => {
                console.log(response)
                // this.is_fetching = false
                this.$emit('update:is_fetching', false)
                this.status = response.status
                if (!response.ok) {
                    this.$emit('handleError', response)
                }
            })
        },
    }
}
vueApp.component('TestConnectionButton', TestConnectionButton)

const ModalDialog = {
    delimiters: ['[[', ']]'],
    props: ['display_name', 'id', 'description', 'is_default', 'is_fetching'],
    emits: ['update', 'create', 'update:description', 'update:is_default'],
    template: `
<div class="modal-dialog modal-dialog-aside" role="document">
    <div class="modal-content">
        <div class="modal-header">
            <div class="row w-100">
                <div class="col">
                    <h2>[[ display_name ]] integration</h2>
                    <p v-if="id">
                        <h13>id: [[ id ]]</h13>
                    </p>
                </div>
                <div class="col-xs">
                    <button type="button" class="btn btn-sm btn-secondary" data-dismiss="modal" aria-label="Close">
                        Cancel
                    </button>
                    <button type="button" class="btn btn-sm btn-secondary"
                            :class="{disabled: is_fetching, updating: is_fetching}"
                            @click.prevent="id ? $emit('update') : $emit('create')"
                    >
                        [[ id ? 'Update' : 'Save' ]]
                    </button>
                </div>
            </div>
        </div>

        <div class="modal-body">
            <slot name="body"></slot>
            
            <div class="form-group">
                <label class="w-100">
                    <h9>Description</h9>
                    <textarea class="form-control" rows="1" placeholder="Optional"
                    :value="description"
                              @input="$emit('update:description', $event.target.value)">
                        </textarea>

                </label>
            </div>
            <div class="form-check">
                <label>
                    <input class="form-check-input" type="checkbox"
                            :value="Boolean(is_default)"
                           @input="$emit('update:is_default', $event.target.checked)"
                           >
                    <h9>
                        Set as default
                    </h9>
                </label>
            </div>
            
            <slot name="footer"></slot>
            
        </div>
    </div>
</div>
    `
}
vueApp.component('ModalDialog', ModalDialog)
