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
        <div class="btn-action d-flex align-items-center integration_add gap-2 my-1"
             data-toggle="modal"
             :data-target="modal_target"
        >
            <div><i class="icon__18x18 icon-create-element"></i></div>
            <div v-if="logo" v-html="logo"></div>
            <slot v-else></slot>
            <p class="font-h5 font-semibold text-gray-600">[[ display_name ]]</p>
        </div>
    `
}

const TestConnectionButton = {
    delimiters: ['[[', ']]'],
    props: ['error', 'apiPath', 'is_fetching', 'body_data'],
    emits: ['update:is_fetching', 'handleError', 'update:error'],
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
        show_error() {
            return (this.test_connection_class === 'btn-warning')
        }
    },
    template: `
        <button type="button" class="btn btn-sm mt-3"
                @click="test_connection"
                :class="[{disabled: is_fetching, updating: is_fetching, 'is-invalid': error}, test_connection_class]"
        >
            Test connection
        </button>
        <div class="invalid-feedback" v-if="show_error">[[ error ]]</div>
    `,
    watch: {
        is_fetching(newState, oldState) {
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
                this.$emit('update:is_fetching', false)
                this.status = response.status
                if (!response.ok) {
                    this.$emit('handleError', response)
                }
            })
        },
    }
}

const ModalDialog = {
    delimiters: ['[[', ']]'],
    props: ['display_name', 'id', 'name', 'is_default', 'is_shared', 'is_fetching'],
    emits: ['update', 'create', 'update:name', 'update:is_default', 'update:is_shared'],
    template: `
<div class="modal-dialog modal-dialog-aside" role="document">
    <div class="modal-content">
        <div class="modal-header">
            <div class="d-flex align-items-center w-100 justify-content-between">
                <div>
                    <p class="font-h3 font-bold">[[ display_name ]]</p>
                </div>
                <div class="d-flex">
                    <button type="button" class="btn btn-sm btn-secondary" data-dismiss="modal" aria-label="Close">
                        Cancel
                    </button>
                    <button type="button" class="btn btn-sm btn-secondary ml-2"
                            :class="{disabled: is_fetching, updating: is_fetching}"
                            @click.prevent="id ? $emit('update') : $emit('create')"
                    >
                        [[ id ? 'Update' : 'Save' ]]
                    </button>
                </div>
            </div>
        </div>

        <div class="modal-body">
            <div class="form-group">
                <div>
                    <label class="w-100">
                        <p class="font-h5 font-semibold">Name</p>
                        <p class="font-h6 font-weight-400 mb-2">Specify the name of integration to differ from similar ones</p>
                        <input type="text" class="form-control"
                            :value="name"
                            @input="$emit('update:name', $event.target.value)"
                        >
                    </label>
                </div>
            </div>
            <slot name="body"></slot>
            <div class="form-group">
                <div class="mt-3">
                    <label class="custom-checkbox d-flex align-items-center">
                        <input class="mr-2.5" type="checkbox"
                                :checked="Boolean(is_default)"
                                @input="$emit('update:is_default', $event.target.checked)"
                               >
                        <p class="font-h5 font-semibold">Set as default</p>
                    </label>
                </div>
                <div v-if="$root.mode === 'administration'" class="mt-3">
                    <label class="custom-checkbox d-flex align-items-center">
                        <input class="mr-2.5" type="checkbox"
                                :checked="Boolean(is_shared)"
                                @input="$emit('update:is_shared', $event.target.checked)"
                               >
                        <p class="font-h5 font-semibold">Share with projects</p>
                    </label>
                </div>
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
    mounted() {
        this.value = this.modelValue
    },
    template: `
    <div class="custom-input__tabs">
        <input :type="from_secrets ? 'text' : 'password'"
           class="form-control form-control-alternative" 
           :placeholder="placeholder"
           v-model="value"
           style="padding-left: 140px"
        >
        <ul class="input-tabs nav nav-pills" role="tablist" >
            <li class="nav-item" role="presentation">
                <a class="font-h6 font-semibold"
                 :class="{'active': from_secrets}"
                href=""
                data-toggle="pill" 
                role="tab" 
                @click="from_secrets = true"
                >Secret</a>
            </li>
            <li class="nav-item" role="presentation" >
                <a class="font-h6 font-semibold" 
                :class="{'active': !from_secrets}"
                href="" 
                data-toggle="pill" 
                role="tab" 
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
