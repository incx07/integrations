const IntegrationSections = {
    delimiters: ['[[', ']]'],
    props: ['initial_sections'],
    data() {
        return {
            sections: []
        }
    },
    mounted() {
        this.sections = this.initial_sections
        this.$root.custom_data.handle_integrations_update = this.handle_integration_update
        window.socket.on('task_creation', async payload => {
            console.log('payload', payload)
            payload.msg && showNotify(payload.ok ? 'SUCCESS' : 'ERROR', payload.msg)
                // integrationName = payload['name']
                // integrationId = payload['id']
                // imgSrc = payload['img_src']
                // $(`#${integrationName}-${integrationId}-img`).attr('src', imgSrc)
                // return


            const integration_section_index = this.sections.findIndex(section => section.name === payload.section)
            if (integration_section_index !== -1) {
                const integration = this.sections[integration_section_index].integrations.find(i => i.id === payload.id)
                if (integration) {
                    Object.assign(integration, payload)
                } else {
                    await this.handle_integration_update({section_name: payload.section})
                    const integration = this.sections[integration_section_index].integrations.find(i => i.id === payload.id)
                    Object.assign(integration, payload)
                }
            }
        })
    },
    methods: {
        async handle_integration_update({section_name, ...rest}) {
            console.log('section updated', section_name, rest)

            const updated_section_data = await this.fetch_section(section_name)
            if (updated_section_data !== undefined) {
                const integration_section_index = this.sections.findIndex(section => section.name === section_name)
                if (integration_section_index) {
                    this.sections[integration_section_index].integrations = updated_section_data
                }
            }
            showNotify('INFO', 'Updated')
        },
        async fetch_integrations(integration_name) {
            const resp = await fetch(`/api/v1/integrations/integrations/${this.$root.project_id}?name=${integration_name}`)
            if (resp.ok) {
                return await resp.json()
            }
            showNotify('ERROR', 'Failed fetching updates')
        },
        async fetch_section(section_name) {
            const resp = await fetch(`/api/v1/integrations/integrations/${this.$root.project_id}?section=${section_name}`)
            if (resp.ok) {
                return await resp.json()
            }
            showNotify('ERROR', 'Failed fetching updates')
        }
    },
    template: `
        <div class="row section_row" v-for="section in sections">
            <div class="card card-x shadow-none">
                <div class="card-header">
                    <h3 class="section-name">[[ section.name ]]</h3>
                    <h9>[[ section.integration_description ]]</h9>
                </div>
                <div class="card-body">
                    <div class="row d-flex section_cards">
                        <Integration-Card
                            v-for="integration in section.integrations"
                            v-bind="integration"
                        ></Integration-Card>
                    </div>
                    <div class="row d-flex mt-3 section_create">
                        <slot :name="'section_create_' + section.name"></slot>
                    </div>
                </div>
            </div>
        </div>
    `
}
register_component('IntegrationSections', IntegrationSections)