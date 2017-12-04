$(function() {
    $('.inline-group').on('click', '.add-row a', function() {
        replaceJetSelectWithAutocompleteLight($(this).closest('.inline-group'));
    });

    // Remove jet select2 if autocomplete-light is used
    function replaceJetSelectWithAutocompleteLight(parent) {
        var autocomplete_light_selects;
        if ('undefined' != typeof(parent)) {
            autocomplete_light_selects = parent.find('select[data-is_custom_autocomplete_light="true"]');
        }
        else {
            autocomplete_light_selects = $('select[data-is_custom_autocomplete_light="true"]');
        }

        if (0 < autocomplete_light_selects.length) {
            $.each(autocomplete_light_selects, function(index, item) {
                var parent = $(item).parent();

                parent.find('.select2-container--jet').not('.custom').remove();
                var autocomplete_light = parent.find('.select2-container--default');

                autocomplete_light.removeClass('select2-container--default').addClass('select2-container--jet custom');

                $(item).on("select2:open", function() {
                    $('.select2-container--default').removeClass('select2-container--default').addClass('select2-container--jet');
                });

                var prefix = $(item).getFormPrefix();
                var full_field_name = $(item).prop('name');
                var field_name = full_field_name.replace(prefix, '');

                $.each($(item).data('forward'), function(index, name) {
                    $('[name$="' + name + '"]').on('change', function() {
                        var prefix = $(this).getFormPrefix();
                        $('[name=' + prefix + field_name + ']').val(null).trigger('change');
                    });
                });
            });
        }
    }

    replaceJetSelectWithAutocompleteLight();
});