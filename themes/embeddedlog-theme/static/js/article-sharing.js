/*
 * Site-specific Shariff setup: classic Twitter, service names and Copy link.
 * Keep custom behaviour here so the vendored library stays unchanged.
 */
(function () {
    'use strict';

    var serviceNames = {
        twitter: 'Twitter',
        facebook: 'Facebook',
        linkedin: 'LinkedIn',
        reddit: 'Reddit',
        whatsapp: 'WhatsApp'
    };
    var canonical = document.querySelector('link[rel="canonical"]');
    var url = canonical ? canonical.href : window.location.href;

    document.querySelectorAll('.article-sharing').forEach(function (sharing) {
        var shariff = sharing.querySelector('.shariff');
        // Pass an absolute URL: Shariff misresolves relative dev canonicals.
        // Mark the instance so its automatic setup does not build it again.
        shariff.shariff = new window.Shariff(shariff, {url: url});
        Object.keys(serviceNames).forEach(function (service) {
            var text = shariff.querySelector('.' + service + ' .share_text');
            if (text) text.textContent = serviceNames[service];
        });
        var twitter = shariff.querySelector('.twitter');
        if (twitter) {
            var icon = twitter.querySelector('.fa-x-twitter');
            if (icon) icon.classList.replace('fa-x-twitter', 'fa-twitter');
            var link = twitter.querySelector('a');
            link.title = 'Share on Twitter';
            link.setAttribute('aria-label', 'Share on Twitter');
        }

        var copyButton = sharing.querySelector('.article-copy-link');
        if (!navigator.clipboard || !navigator.clipboard.writeText) return;

        var copyLabel = copyButton.querySelector('span');
        var status = sharing.querySelector('.article-copy-status');
        var resetTimer;
        function resetCopyButton() {
            copyLabel.textContent = 'Copy link';
            copyButton.classList.remove('is-copied');
        }
        copyButton.hidden = false;
        copyButton.addEventListener('click', async function () {
            clearTimeout(resetTimer);
            resetCopyButton();
            try {
                await navigator.clipboard.writeText(url);
                copyLabel.textContent = 'Copied!';
                copyButton.classList.add('is-copied');
                status.classList.add('sr-only');
                status.textContent = 'Article link copied to clipboard.';
                resetTimer = setTimeout(resetCopyButton, 2000);
            } catch (error) {
                status.classList.remove('sr-only');
                status.textContent = 'Could not copy the link. Copy the address from your browser.';
            }
        });
    });
})();
