/*
 * Zamboni loader percentage readout.
 *
 * Dash does not expose real load progress, so while the shell loading
 * indicator (the only dcc.Loading in the app) is visible this animates
 * an eased estimate from 0% toward 99% (fast start, slowing climb -
 * never 100% while still loading) as percentage text over a horizontal
 * progress bar. When the spinner hides, it snaps to
 * 100%, holds briefly, fades out, and resets for the next load.
 * The readout element is appended inside the spinner element itself,
 * so it stays glued under the machine wherever Dash centers it
 * (anchoring it to the loading wrapper put it at the page's bottom
 * edge on tall pages).
 *
 * Detection note: the spinner element itself is the loading signal.
 * Dash renders it (inside the shell Loading component, #main-loading)
 * only while a load is active and unmounts it when the load ends. An
 * earlier version hunted for a `._dash-loading` element containing
 * the spinner, but in this Dash version that class is never an
 * ancestor of the spinner, so the readout never fired on the live
 * site even though the script loaded fine.
 *
 * Vanilla JS, no dependencies. Everything is guarded: if the expected
 * DOM is not found it silently does nothing - it must never break
 * the app.
 */
(function () {
    'use strict';

    var PCT_CLASS = 'zamboni-pct';
    var TEXT_CLASS = 'zamboni-pct-text';
    var TRACK_CLASS = 'zamboni-pct-track';
    var FILL_CLASS = 'zamboni-pct-fill';
    var SPINNER_SEL = '.dash-default-spinner, .dash-sk-circle, .dash-dot-spinner';
    var TICK_MS = 120;
    var state = null; // {host, el, pct, timer, gen}
    var gen = 0;

    function findSpinner() {
        try {
            // The spinner element is rendered inside the shell Loading
            // component (#main-loading) only while a load is active,
            // so a connected spinner in the document IS the signal.
            var shell = document.getElementById('main-loading');
            if (shell) {
                var spinner = shell.querySelector(SPINNER_SEL);
                if (spinner && spinner.isConnected) {
                    return spinner;
                }
            }
            var any = document.querySelector(SPINNER_SEL);
            if (any && any.isConnected) {
                return any;
            }
        } catch (e) { /* ignore */ }
        return null;
    }

    // The readout is a small stack inside the .zamboni-pct container:
    // percentage text on top, a horizontal progress bar under it.
    // Only the container is a direct child of the spinner - Dash's own
    // stylesheet paints every direct-child div of the spinner as one
    // of its animated equalizer bars, so the container's CSS carries
    // hard resets against that, and the text/bar live one level
    // deeper where Dash's child selector cannot reach them.
    function ensureEl(host) {
        var el = null;
        try { el = host.querySelector(':scope > .' + PCT_CLASS); } catch (e) { /* ignore */ }
        if (el && el.querySelector('.' + TEXT_CLASS) && el.querySelector('.' + FILL_CLASS)) {
            return el;
        }
        if (!el) {
            el = document.createElement('div');
            el.className = PCT_CLASS;
            el.setAttribute('aria-hidden', 'true');
            try { host.appendChild(el); } catch (e) { /* ignore */ }
        } else {
            try { el.innerHTML = ''; } catch (e) { /* ignore */ }
        }
        try {
            var text = document.createElement('span');
            text.className = TEXT_CLASS;
            var track = document.createElement('div');
            track.className = TRACK_CLASS;
            var fill = document.createElement('div');
            fill.className = FILL_CLASS;
            track.appendChild(fill);
            el.appendChild(text);
            el.appendChild(track);
        } catch (e) { /* ignore */ }
        return el;
    }

    function setDisplay(el, pct) {
        try {
            var text = el.querySelector('.' + TEXT_CLASS);
            if (text) { text.textContent = Math.floor(pct) + '%'; }
            var fill = el.querySelector('.' + FILL_CLASS);
            if (fill) { fill.style.width = pct + '%'; }
        } catch (e) { /* ignore */ }
    }

    function tick() {
        if (!state) { return; }
        try {
            if (state.pct < 99) {
                // Eased climb: quick off the line, slowing as it nears
                // the cap, with a little randomness so it feels alive.
                var step = Math.max(0.4, (99 - state.pct) * 0.045) + Math.random() * 1.1;
                state.pct = Math.min(99, state.pct + step);
                setDisplay(state.el, state.pct);
            }
        } catch (e) { /* never break the app */ }
    }

    function start(host) {
        gen += 1;
        if (state && state.timer) {
            try { clearInterval(state.timer); } catch (e) { /* ignore */ }
        }
        var el = ensureEl(host);
        try { el.setAttribute('data-gen', String(gen)); } catch (e) { /* ignore */ }
        state = { host: host, el: el, pct: 0, timer: null, gen: gen };
        try {
            el.style.opacity = '1';
            setDisplay(el, 0);
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
            setDisplay(s.el, 100);
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
            var host = findSpinner();
            if (host) {
                if (!state || state.host !== host) {
                    start(host);
                } else if (state.el && !state.el.isConnected) {
                    // Spinner re-rendered mid-load; re-attach the readout.
                    state.el = ensureEl(host);
                    setDisplay(state.el, state.pct);
                    try { state.el.style.opacity = '1'; } catch (e) { /* ignore */ }
                }
            } else if (state) {
                if (state.host && !state.host.isConnected) {
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
