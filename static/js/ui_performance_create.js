var IntegrationSection = {
    Manager: instance_prefix => {
        instance_prefix = instance_prefix || ''
        return {
            get: () => {
                return Object.entries(vueVm.registered_components).reduce((acc, [name, i]) => {
                    const tmp_data = i.section && i.get_data && i.get_data()
                    if (tmp_data && Object.entries(tmp_data).length) {
                        acc[i.section] = acc[i.section] || {}
                        acc[i.section][name.substring(instance_prefix.length)] = tmp_data
                    }
                    return acc
                }, {})
            },
            set: values => {
                if (values) {
                    console.debug('SET integrations', values)
                    Object.keys(values).forEach(section => {
                        Object.keys(values[section]).forEach(integrationItem => {
                            vueVm.registered_components[`${instance_prefix}${integrationItem}`]?.set_data(values[section][integrationItem])
                        })
                    })
                }

            },
            clear: () => (
                $('.integration_section').toArray().forEach(item => {
                    Object.values(vueVm.registered_components).forEach(i => {
                        i.section && i.clear_data()
                    })

                })
            ),
            setError: data => {
                console.debug('SET error', data)
                const process_error = error_data => {
                    const [dataCallbackName, ...rest] = error_data.loc
                    const integrationName = dataCallbackName.split('_').splice(1).join('_')
                    error_data.loc = rest
                    if (window[integrationName]) {
                        window[integrationName].set_error(error_data)
                    } else {
                        vueVm.registered_components[integrationName]?.set_error(error_data)
                        // console.warn('SET ERROR FAIL', dataCallbackName, error_data.loc)
                    }
                }
                if (Array.isArray(data)) {
                    data.forEach(i => process_error(i))
                } else {
                    process_error(data)
                }
            },
            clearErrors: () => {
                Object.values(vueVm.registered_components).forEach(i => {
                 i.clear_errors && i.clear_errors()
                })
            },
        }
    }
}


const TestIntegrationItem = {
    delimiters: ['[[', ']]'],
    props: ['integration_name', 'display_name', 'project_integrations'],
    data() {
        return {
            selected_integration: undefined,
            is_selected: false,
            errors: {}
        }
    },
    mounted() {
        this.selected_integration = this.get_integration_value(this.default_integration)
    },
    computed: {
        selector_id() {
            return `selector_${this.integration_name}`
        },
        settings_id() {
            return `settings_${this.integration_name}`
        },
        default_integration() {
            return this.project_integrations.find(item => item.is_default)
        },
        integration_data() {
            return this.project_integrations.find(item => this.get_integration_value(item) === this.selected_integration)
        },
        selected_integration_id() {
            const integration_id = this.selected_integration?.split('#')[0] 
            return integration_id && parseInt(integration_id)
        }
    },
    watch: {
        is_selected(newState, oldState) {
            !newState && $(`#${this.selector_id}`).collapse('hide')
            !newState && $(`#${this.settings_id}`).collapse('hide')
        }
    },
    methods: {
        getIntegrationTitle(integration) {
            return integration.is_default ? `${integration.config?.name} - default` : integration.config?.name
        },
        clear_data() {
            this.is_selected = false
            this.selected_integration = this.get_integration_value(this.default_integration)
            $(`#${this.selector_id}`).collapse('hide')
            $(`#${this.settings_id}`).collapse('hide')
            this.clear_errors()
        },
        set_data({id, is_local}) {
            console.debug('TestIntegrationItem receiving set_data', {
                id,
                is_local,
                selected_integration: this.selected_integration
            })
            const integration_obj = this.project_integrations.find(
                item => {
                    if (item.id === id) {
                        if (is_local !== undefined) {
                            return !!(item.project_id) === is_local
                            }
                        return true
                        }
                    }
                )
            !integration_obj && this.handle_id_error()
            this.selected_integration = this.get_integration_value(integration_obj)
            this.is_selected = true
            $(`#${this.selector_id}`).collapse('show')
        },
        handle_id_error() {
            this.errors.id = `This integration no longer exists. 
                ${this.project_integrations.length === 0 ? 'Create' : 'Select'} a new one, 
                otherwise the integration won\'t be applied
            `
            alertCreateTest?.add(`
                Please fix errors in <a href="#" onclick="$('#${this.selector_id}')[0].scrollIntoView()">this integration section</a>
            `, 'warning-overlay', true,)
        },
        clear_errors() {
            this.errors = {}
        },
        get_integration_value(integration) {
            return `${integration?.id}#${integration?.project_id}`
        }
    },
    template: `
    <div class="card card-row-1 card-x mx-auto">
        <div class="card-header">
            <div class="d-flex align-items-center">
                <p class="flex-grow-1 font-h5 font-semibold" style="line-height: 24px">[[ display_name ]]</p>
                <button aria-expanded="false" 
                        type="button"
                        class="btn btn-24 btn-action"
                        data-toggle="collapse" 
                        :data-target="is_selected && '#' + settings_id" 
                        v-if="!!this.$slots.settings"
                        :class="!is_selected && 'disabled'"
                        
                        >
                    <i class="fas fa-cog"></i>
                </button>
                <label class="custom-toggle"
                    :data-toggle="project_integrations.length === 0 && 'tooltip'" 
                    data-placement="top" 
                    title="No integrations found"
                >
                    <input aria-expanded="false" type="checkbox"
                           :data-target="'#' + selector_id" data-toggle="collapse"
                           v-model="is_selected"
                           :disabled="project_integrations.length === 0 && !errors.id"
                           />
<!--                    <span class="custom-toggle-slider rounded-circle"></span>-->
                    <span class="custom-toggle_slider round"></span>
                </label>
            </div>
        </div>
        <div>
            <div class="collapse" style="padding-bottom: 20px" :id="selector_id">
                <div v-if="this.selected_integration !== 'quality_gate#undefined'" class="select-validation"
                    :class="{'invalid-select': this.errors.id}">
                    <select class="selectpicker bootstrap-select__b" data-style="btn"
                        v-model="selected_integration">
                        <option
                            v-for="integration in project_integrations"
                            :value="get_integration_value(integration)"
                            :title="getIntegrationTitle(integration)"
                        >
                            [[ getIntegrationTitle(integration) ]]
                        </option>
                    </select>
                    <span class="select_error-msg">[[ errors.id ]]</span>
                </div>
                
                <slot 
                    name="selector"
                    :on_set_data="set_data" 
                    :on_clear_data="clear_data"
                    :selected_integration="selected_integration_id"
                    :integration_data="integration_data"
                    :is_selected="is_selected"
                ></slot>
            </div>
        </div>
        <div class="row">
            <div class="collapse col-12 mb-3 pl-0" :id="settings_id">
                <slot 
                    name="settings"
                    :on_set_data="set_data" 
                    :on_clear_data="clear_data" 
                    :selected_integration="selected_integration_id"
                    :integration_data="integration_data"
                    :is_selected="is_selected"
                ></slot>
            </div>
        </div>
    </div>
    `,
}

vueApp.component('TestIntegrationItem', TestIntegrationItem)
