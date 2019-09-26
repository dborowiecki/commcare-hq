hqDefine("succeed/js/patient_submissions", function () {
    var initialPageData = hqImport("hqwebapp/js/initial_page_data");
    $(document).on("ajaxComplete", function (e, xhr, options) {
        var fragment = "async/",
            pageUrl = window.location.href.split('?')[0],
            ajaxUrl = options.url.split('?')[0];
        if (ajaxUrl.indexOf(fragment) === -1 || !pageUrl.endsWith(ajaxUrl.replace(fragment, ''))) {
            return;
        }
        var $paramSelectorForm = $('#paramSelectorForm');
        if ($paramSelectorForm.length && ! $paramSelectorForm.find('#patient_id_field').length) {
            $('<input>').attr({id: 'patient_id_field', type: 'hidden', name: 'patient_id', value: initialPageData.get('patient_id') }).appendTo('#paramSelectorForm');
        }

        var tableOptions = initialPageData.get('report_table_js_options');
        if (tableOptions && tableOptions.datatables) {
            var id = '#report_table_' + initialPageData.get('slug');
            var table = $(id).dataTable();
            table.fnSettings().aaSorting = [[2, 'desc']];
            table.fnDraw();
        }
    });
});
