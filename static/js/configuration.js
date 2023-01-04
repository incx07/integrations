window.integration_status = {
    success: 'success',
    pending: 'pending'
}

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
            <div><i class="fa fa-plus"></i></div>
            <div v-if="logo" v-html="logo"></div>
            <slot v-else></slot>
            <div>[[ display_name ]]</div>
        </div>
    `
}

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
            if (newState) {
                this.status = 0
            }
        }
    },
    methods: {
        async test_connection() {
            this.$emit('update:is_fetching', true)
            try {
                const resp = await fetch(this.apiPath, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(this.body_data)
                })
                this.status = resp.status
                if (!resp.ok) {
                    this.$emit('handleError', await resp.json())
                }
            } catch (e) {
                console.error(e)
                showNotify('WARNING', 'Test not successful')
            } finally {
                this.$emit('update:is_fetching', false)
            }
        },
    }
}

const ModalDialog = {
    delimiters: ['[[', ']]'],
    props: ['display_name', 'id', 'description', 'is_default', 'is_fetching'],
    emits: ['update', 'create', 'update:description', 'update:is_default'],
    template: `
<div class="modal-dialog modal-dialog-aside" role="document">
    <div class="modal-content">
        <div class="modal-header">
            <div class="d-flex align-items-center w-100 justify-content-between">
                <div>
                    <h2>[[ display_name ]]</h2>
                    <p v-if="id">
                        <h13>id: [[ id ]]</h13>
                    </p>
                </div>
                <div class="d-flex">
                    <button type="button" class="btn btn-sm btn-secondary" data-dismiss="modal" aria-label="Close">
                        Cancel
                    </button>
                    <button type="button" class="btn btn-sm btn-secondary ml-1"
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
            
            <div>
                <label class="w-100">
                    <p class="font-h5 font-semibold">Description</p>
                    <textarea class="form-control" rows="1" placeholder="Optional"
                        :value="description"
                        @input="$emit('update:description', $event.target.value)">
                    </textarea>

                </label>
            </div>
            <div class="mt-2">
                <label class="custom-checkbox d-flex align-items-center">
                    <input class="mr-1" type="checkbox"
                            :checked="Boolean(is_default)"
                            @input="$emit('update:is_default', $event.target.checked)"
                           >
                    <p class="font-h5 font-semibold">Set as default</p>
                </label>
            </div>
            
            <slot name="footer"></slot>
            
        </div>
    </div>
</div>
    `
}

const SecretFieldInput = {
    props: ["modelValue", "placeholder"],
    emits: ['update:modelValue'],
    computed: {
        value: {
            get() {
                if (this.modelValue.hasOwnProperty("value")) {
                    return this.modelValue.value
                }
                return this.modelValue
            },
            set(value) {
                this.$emit('update:modelValue', {
                    value: value,
                    from_secrets: this.from_secrets
                })
            }
        }
    },
    template: `
    <div class="custom-input__tabs">
        <input :type="from_secrets ? 'text' : 'password'"
           class="form-control form-control-alternative" 
           :placeholder="placeholder"
           v-model="value"
           style="padding-left: 140px"
        >
        <ul class="input-tabs nav nav-pills" role="tablist">
            <li class="nav-item" role="presentation">
                <a class="font-h6 font-semibold active" 
                href=""
                data-toggle="pill" 
                role="tab" 
                :aria-selected="from_secrets"
                @click="from_secrets = true"
                >Secret</a>
            </li>
            <li class="nav-item" role="presentation" >
                <a class="font-h6 font-semibold" 
                href="" 
                data-toggle="pill" 
                role="tab" 
                :aria-selected="from_secrets"
                @click="from_secrets = false"
                >Plain</a>
            </li>
        </ul>
    </div>
    `,
    data() {
        return {
            from_secrets: true,
        }
    }
}

vueApp.component('SecretFieldInput', SecretFieldInput)
vueApp.component('AddIntegrationButton', AddIntegrationButton)
vueApp.component('TestConnectionButton', TestConnectionButton)
vueApp.component('ModalDialog', ModalDialog)
