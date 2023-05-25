const InheritedIntegrationCard = {
    props: ['id', 'name', 'section', 'settings', 'is_default', 'config', 'task_id', 'status'],
    delimiters: ['[[', ']]'],
    computed: {
        reflected_component() {
            const obj = this.$root.registered_components[this.name]
            !obj && console.warn('No reflected component found for', this.name)
            obj && !obj.handleEdit && console.warn('.handleEdit method not implemented for for', this.name)
            obj && !obj.handleDelete && console.warn('.handleDelete method not implemented for for', this.name)
            obj && !obj.handleSetDefault && console.warn('.handleSetDefault method not implemented for for', this.name)
            return obj
        },
        display_name() {
            return this.reflected_component?.display_name || this.name
        },
        logo() {
            return this.reflected_component?.logo_src
        },
        circle_class() {
            switch (this.status) {
                case window.integration_status.success:
                    return 'integration_icon_success'
                case window.integration_status.pending:
                    return 'integration_icon_undetermined'
                default:
                    return 'integration_icon_error'
            }
        }
    },
    methods: {
        handle_set_default() {
            this.reflected_component.handleSetDefault(this.id, local=false)
        },
    },
    watch: {
        status() {
            this.$nextTick(() => $('[data-toggle="infotip"]').tooltip('update'))
        }
    },
    template: `
<div class="card card-row-1 integration_card p-4 flex-row mb-3">
    <img class="integration_icon h-12 w-12 object-contain mr-3" :class="circle_class" :src="logo">
    <div class="d-flex flex-column flex-grow-1 justify-content-between">
        <p class="font-h4 font-bold">[[ display_name ]]</p>
        <p class="font-h6 font-weight-400 integration_description">[[ config.name ]]</p>
    </div>
    <div class="d-flex flex-column justify-content-between align-items-end">
        <div class="d-flex justify-content-end align-items-center">
            <div class="badge-grey mr-2" v-if="is_default">
                <p class="font-h6 font-weight-400">Default</p>
            </div>
            <button class="btn btn-icon" 
                data-toggle="infotip" 
                data-placement="top" 
                title="" 
                :data-original-title="status"
                v-else-if="status !== window.integration_status.success"
            >
                <i class="far fa-exclamation-triangle" style="color: var(--text-orange)"></i>
            </button>
            <div class="dropdown dropleft dropdown_action text-right">
                <button class="btn btn-default btn-xs btn-table btn-icon__xs"
                        data-toggle="dropdown"
                        aria-expanded="false">
                    <i class="icon__18x18 icon-menu-dots"></i>
                </button>
    
                <ul class="dropdown-menu">
                    <li class="dropdown-item d-flex align-items-center" @click="handle_set_default">
                        <span>Set as default</span>
                    </li>
                </ul>
            </div>
        </div>
        <i class="preview-loader mr-1" v-if="status === window.integration_status.pending"></i>
    </div>
</div>
`
}
register_component('InheritedIntegrationCard', InheritedIntegrationCard)
