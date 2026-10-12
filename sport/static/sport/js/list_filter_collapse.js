(function ($) {
    $(document).ready(function () {
        $('#changelist-filter').children('h3').each(function () {
            const $filterEl = $(this).css('cursor', 'pointer');
            const $filterList = $filterEl.next('ul').hide();
            $filterEl.click($filterList.slideToggle.bind($filterList));
        });
        $('#changelist-filter li:not(:first-child).selected').parent().show();
        $($('#changelist-filter li select option[selected]').parents()[2]).show();
    });
})(django.jQuery);
