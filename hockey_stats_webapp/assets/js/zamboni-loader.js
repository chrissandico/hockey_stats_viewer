/*
 * Zamboni loader percentage readout.
 *
 * Dash does not expose real load progress, so while the shell loading
 * indicator (the only dcc.Loading in the app) is visible this animates
 * an eased estimate from 0% toward 99% (fast start, slowing climb -
 * never 100% while still loading). When the spinner hides, it snaps to
 * 100%, holds briefly, fades out, and resets for the next load.
 *
 * Vanilla JS, no dependencies. Everything is guarded: if the expected
 * DOM is not found it silently does nothing - it must never break
 * the app.
 */
(function () {
    'use strict';

    var PCT_CLASS = 'zamboni-pct';
    var SPINNER_SEL = '.dash-default-spinner, .dash-sk-circle, .dash-dot-spinner';
    var TICK_MS = 120;
    var state = null; // {wrapper, el, pct, timer, gen}
    var gen = 0;

    function findLoadingWrapper() {
        try {
            var wrappers = document.querySelectorAll('._dash-loading');
            for (var i = 0; i < wrappers.length; i++) {
                if (wrappers[i].querySelector(SPINNER_SEL)) {
                    return wrappers[i];
                }
            }
        } catch (e) { /* ignore */ }
        return null;
    }

    function ensureEl(wrapper) {
        var el = null;
        try { el = wrapper.querySelector(':scope > .' + PCT_CLASS); } catch (e) { /* ignore */ }
        if (!el) {
            el = document.createElement('div');
            el.className = PCT_CLASS;
            el.setAttribute('aria-hidden', 'true');
            try { wrapper.appendChild(el); } catch (e) { /* ignore */ }
        }
        return el;
    }

    function tick() {
        if (!state) { return; }
        try {
            if (state.pct < 99) {
                // Eased climb: quick off the line, slowing as it nears
                // the cap, with a little randomness so it feels alive.
                var step = Math.max(0.4, (99 - state.pct) * 0.045) + Math.random() * 1.1;
                state.pct = Math.min(99, state.pct + step);
                state.el.textContent = Math.floor(state.pct) + '%';
            }
        } catch (e) { /* never break the app */ }
    }

    function start(wrapper) {
        gen += 1;
        if (state && state.timer) {
            try { clearInterval(state.timer); } catch (e) { /* ignore */ }
        }
        var el = ensureEl(wrapper);
        try { el.setAttribute('data-gen', String(gen)); } catch (e) { /* ignore */ }
        state = { wrapper: wrapper, el: el, pct: 0, timer: null, gen: gen };
        try {
            el.style.opacity = '1';
            el.textContent = '0%';
        } catch (e) { /* ignore */ }
        state.timer = setInterval(tick, TICK_MS);
    }

    function hardReset() {
        if (state && state.timer) {
            try { clearInterval(state.timer); } catch (e) { /* ignore */ }
        }
        state = null;
    }

    function finish() {
        if (!state) { return; }
        var s = state;
        state = null;
        if (s.timer) {
            try { clearInterval(s.timer); } catch (e) { /* ignore */ }
        }
        try {
            s.el.textContent = '100%';
            s.el.style.opacity = '1';
            setTimeout(function () {
                try {
                    // Superseded by a newer load reusing this element?
                    if (s.el.getAttribute('data-gen') !== String(s.gen)) { return; }
                    s.el.style.opacity = '0';
                    setTimeout(function () {
                        try {
                            if (s.el.getAttribute('data-gen') === String(s.gen) && s.el.parentNode) {
                                s.el.parentNode.removeChild(s.el);
                            }
                        } catch (e) { /* ignore */ }
                    }, 450);
                } catch (e) { /* ignore */ }
            }, 300);
        } catch (e) { /* ignore */ }
    }

    function sync() {
        try {
            var wrapper = findLoadingWrapper();
            if (wrapper) {
                if (!state || state.wrapper !== wrapper) {
                    start(wrapper);
                } else if (state.el && !state.el.isConnected) {
                    // Wrapper re-rendered mid-load; re-attach the readout.
                    state.el = ensureEl(wrapper);
                    try { state.el.style.opacity = '1'; } catch (e) { /* ignore */ }
                }
            } else if (state) {
                if (state.wrapper && !state.wrapper.isConnected) {
                    hardReset(); // whole loader was replaced; drop silently
                } else {
                    finish();
                }
            }
        } catch (e) { /* never break the app */ }
    }

    function init() {
        try {
            var observer = new MutationObserver(sync);
            observer.observe(document.documentElement, {
                subtree: true,
                childList: true,
                attributes: true,
                attributeFilter: ['class']
            });
        } catch (e) { /* ignore */ }
        sync();
    }

    try {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
        } else {
            init();
        }
    } catch (e) { /* never break the app */ }
})();
