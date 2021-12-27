$(document).ready(() => {
    new SectionDataProvider('integrations', {
        get: () => (
            $('.integration_section').toArray().reduce((accum, item) => {
                const sectionElement = $(item)
                const sectionName = sectionElement.find('.integration_section_name').text().toLowerCase().replace(' ', '_')

                const sectionData = sectionElement.find('.security_integration_item').toArray().reduce((acc, i) => {
                    const integrationName = i.dataset.name
                    const dataCallbackName = `${sectionName}_${integrationName}`
                    const integrationData = window[dataCallbackName]?.get_data()
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
        ),
        set: values => {
            if (values) {
                console.log('SET integrations', values)
                // {
                //     scanners: {
                //         qualys:
                //         {
                //             id: "44"
                //         }
                //     }
                // }
                Object.keys(values).forEach(section => {
                    Object.keys(values[section]).forEach(integrationItem => {
                        const dataCallbackName = `${section}_${integrationItem}`
                        window[dataCallbackName]?.set_data(values[section][integrationItem])
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
                    window[dataCallbackName]?.clear_data()
                })
            })
        ),
        default: {}
    }).register()
})
