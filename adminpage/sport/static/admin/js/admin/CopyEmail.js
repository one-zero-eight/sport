(function($) {
    $(document).ready(function() {
        const $wrapper = $('.field-user .related-widget-wrapper');

        if ($wrapper.length) {
            const $copyBtn = $('<a class="related-widget-wrapper-link" style="cursor:pointer; margin-left:5px; opacity: 1 !important; filter: brightness(1.2);" title="Скопировать email">📋</a>');

            $copyBtn.on('click', function(e) {
                e.preventDefault();
                const email = $('#id_user').next('.select2-container').find('.select2-selection__rendered').text().trim();

                if (email) {
                    navigator.clipboard.writeText(email).then(() => {
                        const $this = $(this);
                        $this.text('✅');
                        setTimeout(() => $this.text('📋'), 1500);
                    });
                }
            });

            $wrapper.append($copyBtn);
        }
    });
})(django.jQuery);
