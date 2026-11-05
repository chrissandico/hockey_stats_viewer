"""Last N games filter — shared control, session store, and callbacks.

One session-scoped store (`last-n-games-store`) holds the selected window:
an int N (1-30) or None for "All games". The control (preset select +
custom number input) is rendered on the Dashboard, Players/Goalies and
Parent pages; setting it on any page is honoured on all of them because
every in-scope callback reads the same store and passes `last_n` down to
the data service. The store is storage_type='session', so a new browser
session always starts at All games — the window is never sticky across
logins.
"""
from dash import html, dcc, Input, Output, State, no_update

LAST_N_STORE_ID = 'last-n-games-store'
LAST_N_PRESET_ID = 'last-n-preset-select'
LAST_N_CUSTOM_ID = 'last-n-custom-input'
LAST_N_CUSTOM_WRAP_ID = 'last-n-custom-wrap'

LAST_N_PRESETS = (2, 3, 5, 10)
LAST_N_MIN = 1
LAST_N_MAX = 30

PRESET_OPTIONS = (
    [{'label': 'All Games', 'value': 'all'}]
    + [{'label': f'Last {n} Games', 'value': str(n)} for n in LAST_N_PRESETS]
    + [{'label': 'Custom…', 'value': 'custom'}]
)


def create_last_n_store():
    """The shared session store. Place once in the app layout root so it
    survives page swaps; data is the resolved window (int) or None."""
    return dcc.Store(id=LAST_N_STORE_ID, storage_type='session', data=None)


def normalize_last_n_choice(preset, custom):
    """Resolve a preset/custom control state to a window value.

    Returns None for All, else an int clamped to 1-30. A Custom preset
    with an empty or invalid number resolves to None (All) rather than
    an error — the same rule the data service applies.
    """
    if preset is None or preset == 'all':
        return None
    if preset == 'custom':
        try:
            n = int(custom)
        except (TypeError, ValueError):
            return None
        return max(LAST_N_MIN, min(LAST_N_MAX, n))
    try:
        n = int(preset)
    except (TypeError, ValueError):
        return None
    return max(LAST_N_MIN, min(LAST_N_MAX, n))


def last_n_window_label(last_n, actual=None):
    """Reader-facing label for an active window ('' when All).

    When fewer completed games exist than were requested, the actual
    count is named — the same requested-vs-actual honesty the Recent
    Games page uses.
    """
    if last_n is None:
        return ''
    if actual is not None and actual < last_n:
        return f'Last {last_n} Games (only {actual} played)'
    return f'Last {last_n} Games'


def create_last_n_filter_component():
    """Render the Last N control (styled like the game type filter)."""
    return html.Div([
        html.Label(
            'Games window:',
            style={'fontWeight': 'bold', 'marginRight': '10px', 'color': '#2c3e50'},
        ),
        dcc.Dropdown(
            id=LAST_N_PRESET_ID,
            options=PRESET_OPTIONS,
            value='all',
            clearable=False,
            style={'width': '220px', 'display': 'inline-block', 'verticalAlign': 'middle'},
        ),
        html.Span(
            dcc.Input(
                id=LAST_N_CUSTOM_ID,
                type='number',
                min=LAST_N_MIN,
                max=LAST_N_MAX,
                step=1,
                placeholder='1–30',
                style={'width': '90px', 'marginLeft': '10px'},
            ),
            id=LAST_N_CUSTOM_WRAP_ID,
            style={'display': 'none'},
        ),
        html.Span(
            'Stats below cover only the most recent completed games when a window is chosen.',
            style={'marginLeft': '12px', 'color': '#6c757d', 'fontSize': '0.85em'},
        ),
    ], style={
        'margin': '10px 0 20px 0',
        'padding': '12px 15px',
        'backgroundColor': '#f8f9fa',
        'border': '1px solid #dee2e6',
        'borderRadius': '5px',
    })


def register_last_n_callbacks(app):
    """Register the store write + control sync callbacks (call once).

    Both callbacks are equality-guarded: the write callback returns
    no_update when the resolved window already equals the store, and the
    sync callback returns no_update when the rendered control already
    agrees with the store. That pair prevents callback loops and stops a
    freshly mounted control (which defaults to 'all') from clobbering a
    window the user set on another page.
    """

    @app.callback(
        Output(LAST_N_STORE_ID, 'data'),
        [Input(LAST_N_PRESET_ID, 'value'),
         Input(LAST_N_CUSTOM_ID, 'value')],
        [State(LAST_N_STORE_ID, 'data')],
        prevent_initial_call=True,
    )
    def _write_last_n_store(preset, custom, current):
        resolved = normalize_last_n_choice(preset, custom)
        if resolved == current:
            return no_update
        return resolved

    @app.callback(
        [Output(LAST_N_PRESET_ID, 'value'),
         Output(LAST_N_CUSTOM_ID, 'value'),
         Output(LAST_N_CUSTOM_WRAP_ID, 'style')],
        [Input(LAST_N_STORE_ID, 'data')],
        [State(LAST_N_PRESET_ID, 'value'),
         State(LAST_N_CUSTOM_ID, 'value')],
    )
    def _sync_last_n_control(stored, current_preset, current_custom):
        if stored is None:
            target_preset, target_custom = 'all', current_custom
            wrap_style = {'display': 'none'}
        elif stored in LAST_N_PRESETS:
            target_preset, target_custom = str(stored), current_custom
            wrap_style = {'display': 'none'}
        else:
            target_preset, target_custom = 'custom', stored
            wrap_style = {'display': 'inline'}
        if target_preset == current_preset and target_custom == current_custom:
            return no_update, no_update, no_update
        return target_preset, target_custom, wrap_style

    return app
