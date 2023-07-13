$(() => {
    new SectionDataProvider('integrations', {
        get: () => {
            let all_data = $('.integration_section').toArray().reduce((accum, item) => {
                const sectionElement = $(item)
                const sectionName = sectionElement.find('.integration_section_name').text().trim().toLowerCase().replace(' ', '_')
                let sectionData = sectionElement.find('.security_integration_item').toArray().reduce((acc, i) => {
                    const integrationName = i.dataset.name
                    const dataCallbackName = `${sectionName}_${integrationName}`
                    let integrationData
                    if (window[dataCallbackName]) {
                        integrationData = window[dataCallbackName].get_data()
                    } else {
                        // integrationData = vueVm.registered_components[integrationName]?.get_data()
                    }

                    if (integrationData) {
                        acc[integrationName] = integrationData
                    }
                    return acc
                }, {})

                if (Object.entries(sectionData).length) {
                    accum[sectionName] = sectionData
                }
                return accum;
            }, {})
            Object.entries(vueVm.registered_components).reduce((acc, [name, i]) => {
                const tmp_data = i.get_data && i.get_data()
                if (tmp_data && Object.entries(tmp_data).length) {
                    acc[i.section] = acc[i.section] || {}
                    acc[i.section][name] = tmp_data
                }
                return acc
            }, all_data)
            return all_data
        },
        set: values => {
            if (values) {
                console.debug('SET integrations', values)
                Object.keys(values).forEach(section => {
                    Object.keys(values[section]).forEach(integrationItem => {
                        const dataCallbackName = `${section}_${integrationItem}`         
                        if (window[dataCallbackName]) {
                            window[dataCallbackName].set_data(values[section][integrationItem])
                        } else {
                            vueVm.registered_components[integrationItem]?.set_data(values[section][integrationItem])
                        }
                    })
                })
            }

        },
        clear: () => (
            $('.integration_section').toArray().forEach(item => {
                const sectionElement = $(item)
                const sectionName = sectionElement.find('.integration_section_name').text().toLowerCase().replace(' ', '_')
                sectionElement.find('.security_integration_item').toArray().forEach(i => {
                    const integrationName = $(i).attr('data-name')
                    const dataCallbackName = `${sectionName}_${integrationName}`

                    if (window[dataCallbackName]) {
                        window[dataCallbackName].clear_data()
                    } else {
                        // vueVm.registered_components[integrationName]?.clear_data()
                    }
                })
                Object.values(vueVm.registered_components).forEach(i => {
                    if (i.section) {
                        i.clear_data()
                    }
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
        /*
        clearErrors: () => {
            $('.integration_section').toArray().forEach(item => {
                const sectionElement = $(item)
                const sectionName = sectionElement.find('.integration_section_name').text().toLowerCase().replace(' ', '_')
                sectionElement.find('.security_integration_item').toArray().forEach(i => {
                    const integrationName = $(i).attr('data-name')
                    const dataCallbackName = `${sectionName}_${integrationName}`
                    if (window[dataCallbackName]) {
                        window[dataCallbackName].clear_errors && window[dataCallbackName].clear_errors()
                    } else {
                        vueVm.registered_components[integrationName]?.clear_errors && vueVm.registered_components[integrationName]?.clear_errors()
                    }
                })
            })
        },
        */
        default: {}
    }).register()
})

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
        this.selected_integration = this.default_integration?.id
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
            return this.project_integrations.find(item => item.id === this.selected_integration)
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
            integrationName = integration.hasOwnProperty('config')? integration.config.name : integration.description 
            return integration.is_default ? `${integrationName} - default` : integrationName
        },
        clear_data() {
            this.is_selected = false
            this.selected_integration = this.default_integration?.id
            $(`#${this.selector_id}`).collapse('hide')
            $(`#${this.settings_id}`).collapse('hide')
            this.clear_errors()
        },
        set_data({id}) {
            console.debug('TestIntegrationItem receiving set_data', {id, selected_integration: this.selected_integration})
            !this.project_integrations.find(item => item.id === id) && this.handle_id_error()
            this.selected_integration = id
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
        }
    },
    template: `
<div class="col-6">
    <div class="card card-row-1">
        <div class="card-header">
            <div class="d-flex align-items-center">
                <h9 class="flex-grow-1" style="line-height: 24px">[[ display_name ]]</h9>
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
        <div class="row">
            <div class="collapse col-12 mb-3 pl-0" :id="selector_id">
                <div class="select-validation" 
                    :class="{'invalid-select': this.errors.id}">
                    <select class="selectpicker bootstrap-select__b" data-style="btn"
                        v-model="selected_integration">
                        <option
                            v-for="integration in project_integrations"
                            :value="integration.id"
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
                    :selected_integration="selected_integration"
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
                    :selected_integration="selected_integration"
                    :integration_data="integration_data"
                    :is_selected="is_selected"
                ></slot>
            </div>
        </div>
    </div>
</div>
    `,
}


register_component('TestIntegrationItem', TestIntegrationItem)
