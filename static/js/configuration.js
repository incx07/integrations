const AddIntegrationButton = {
    template: `
        <div class="btn btn-action btn-lg d-flex align-items-center integration_add"
             data-toggle="modal"
             data-target="#{{ integration_name }}_integration"
             id="create_integration_{{ integration_name }}"
        >
            <div style="font-size: 20px"><i class="fa fa-plus"></i></div>
            <div class="col-2">[[ logo ]]</div>
            <div class="col">[[ display_name ]]</div>
        </div>
    `
}