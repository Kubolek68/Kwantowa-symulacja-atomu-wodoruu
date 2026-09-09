"""
interactive_viewer_3d.py
=========================
Profesjonalna aplikacja webowa (uruchamiana lokalnie) do interaktywnej
wizualizacji 3D gestosci prawdopodobienstwa elektronu w atomie wodoru.

WAZNE: to jest prawdziwa aplikacja z suwakami WEWNATRZ interfejsu -
nie trzeba niczego wpisywac w terminalu/IDE. Wszystko (suwaki n, l, m
i wykres 3D) dziala w jednym oknie przegladarki.

Uruchomienie:
    python interactive_viewer_3d.py

Nastepnie otworz w przegladarce:
    http://127.0.0.1:8050

Sterowanie:
    - Suwaki n, l, m (po lewej) - zmieniaja orbital, wykres przelicza sie
      automatycznie
    - Mysz na wykresie 3D - obracanie kamery (przeciagnij)
    - Scroll na wykresie - przyblizanie/oddalanie
    - Przycisk "Losowy orbital" - losuje dowolna dozwolona kombinacje
"""

import random

import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, ctx

from hydrogen_orbital import (
    radial_wavefunction,
    angular_probability,
    orbital_label,
    node_counts,
    ORBITAL_LETTERS,
    ORBITAL_FUN_FACTS,
)

NUM_POINTS = 40_000  # liczba punktow "chmury elektronowej"


def clamp_state(n: int, l: int, m: int) -> tuple[int, int, int]:
    n = max(1, min(3, n))
    l = max(0, min(n - 1, l))
    m = max(-l, min(l, m))
    return n, l, m


# ---------------------------------------------------------------------------
# Losowanie punktow metoda odwrotnej dystrybuanty (bez odrzucen) - dzieki
# temu KAZDY z NUM_POINTS "strzalow" trafia w prawdziwy punkt chmury (w
# przeciwienstwie do prostego accept/reject, ktore przy ostrych, spiczastych
# gestosciach (np. orbital 1s) odrzuca ~95% probek).
# -----------------------------------------------------------------------
def sample_radius(n: int, l: int, num_points: int, r_max: float, grid: int = 6000) -> np.ndarray:
    r_grid = np.linspace(1e-6, r_max, grid)
    pdf = radial_wavefunction(n, l, r_grid) ** 2 * r_grid ** 2
    cdf = np.cumsum(pdf)
    cdf /= cdf[-1]
    u = np.random.uniform(0, 1, num_points)
    return np.interp(u, cdf, r_grid)


def sample_theta(l: int, m: int, num_points: int, grid: int = 3000) -> np.ndarray:
    theta_grid = np.linspace(1e-6, np.pi - 1e-6, grid)
    # dOmega = sin(theta) dtheta dphi -> jakobian sin(theta) jest wymagany
    pdf = angular_probability(l, m, theta_grid) * np.sin(theta_grid)
    cdf = np.cumsum(pdf)
    cdf /= cdf[-1]
    u = np.random.uniform(0, 1, num_points)
    return np.interp(u, cdf, theta_grid)


def generate_cloud(n: int, l: int, m: int, num_points: int = NUM_POINTS):
    """Zwraca (x, y, z, kolor) - probki polozenia elektronu zgodne z |psi|^2."""
    r_max = 5.0 + 9.0 * n ** 2  # wystarczajaco szeroki zasieg probkowania

    r = sample_radius(n, l, num_points, r_max)
    theta = sample_theta(l, m, num_points)
    phi = np.random.uniform(0, 2 * np.pi, num_points)

    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)

    # gestosc w kazdym wylosowanym punkcie - uzywana tylko do koloru
    density = radial_wavefunction(n, l, r) ** 2 * angular_probability(l, m, theta)
    color = density / (density.max() + 1e-15)

    return x, y, z, color


def build_figure(n: int, l: int, m: int) -> go.Figure:
    x, y, z, color = generate_cloud(n, l, m)

    fig = go.Figure(data=[go.Scatter3d(
        x=x, y=y, z=z,
        mode="markers",
        marker=dict(
            size=1.8,
            color=color,
            colorscale="Plasma",
            opacity=0.55,
            showscale=True,
            colorbar=dict(title="gestosc", thickness=14, len=0.65),
            line=dict(width=0),
        ),
        hoverinfo="skip",  # bez dymkow z liczbami przy najezdzaniu na punkty
    )])

    fig.update_layout(
        scene=dict(
            xaxis=dict(showbackground=True, backgroundcolor="#14141f",
                       gridcolor="#2a2a3a", zerolinecolor="#3a3a4a", title=""),
            yaxis=dict(showbackground=True, backgroundcolor="#14141f",
                       gridcolor="#2a2a3a", zerolinecolor="#3a3a4a", title=""),
            zaxis=dict(showbackground=True, backgroundcolor="#14141f",
                       gridcolor="#2a2a3a", zerolinecolor="#3a3a4a", title=""),
            aspectmode="cube",
            camera=dict(eye=dict(x=1.4, y=1.4, z=1.1)),
        ),
        paper_bgcolor="#0f0f1a",
        plot_bgcolor="#0f0f1a",
        font=dict(color="#e8e8e8", family="Arial, sans-serif"),
        margin=dict(l=0, r=0, t=10, b=0),
        uirevision="keep-camera",  # nie resetuj obrotu kamery przy zmianie suwaka
    )
    return fig


# ---------------------------------------------------------------------------
# Aplikacja Dash
# ---------------------------------------------------------------------------
app = Dash(__name__)
app.title = "Gestosc prawdopodobienstwa elektronu - atom wodoru"

PANEL_STYLE = {
    "minWidth": "260px",
    "maxWidth": "300px",
    "padding": "24px",
    "backgroundColor": "#161622",
    "borderRadius": "12px",
}
LABEL_STYLE = {"fontSize": "13px", "color": "#9a9aad", "marginTop": "18px", "marginBottom": "6px"}

app.layout = html.Div(
    style={
        "backgroundColor": "#0a0a12",
        "minHeight": "100vh",
        "fontFamily": "Arial, sans-serif",
        "color": "#e8e8e8",
        "padding": "24px",
    },
    children=[
        html.H2("Gęstość prawdopodobieństwa elektronu w atomie wodoru",
                style={"fontWeight": 600, "fontSize": "20px", "marginBottom": "4px"}),
        html.P("Model 3D — n, l, m wybierasz suwakami poniżej.",
               style={"color": "#9a9aad", "marginTop": 0, "marginBottom": "24px", "fontSize": "13px"}),

        html.Div(style={"display": "flex", "gap": "24px", "flexWrap": "wrap"}, children=[

            html.Div(style=PANEL_STYLE, children=[
                html.Label("n — główna liczba kwantowa", style=LABEL_STYLE),
                dcc.Slider(id="slider-n", min=1, max=3, step=1, value=1,
                           marks={i: str(i) for i in (1, 2, 3)}),

                html.Label("l — poboczna liczba kwantowa", style=LABEL_STYLE),
                dcc.Slider(id="slider-l", min=0, max=2, step=1, value=0,
                           marks={i: str(i) for i in (0, 1, 2)}),

                html.Label("m — magnetyczna liczba kwantowa", style=LABEL_STYLE),
                dcc.Slider(id="slider-m", min=-2, max=2, step=1, value=0,
                           marks={i: str(i) for i in (-2, -1, 0, 1, 2)}),

                html.Button("Losowy orbital", id="btn-random", n_clicks=0,
                            style={
                                "marginTop": "22px", "width": "100%", "padding": "10px",
                                "backgroundColor": "#2a2a3f", "color": "#e8e8e8",
                                "border": "1px solid #3a3a52", "borderRadius": "8px",
                                "cursor": "pointer", "fontSize": "13px",
                            }),

                html.Div(id="orbital-label", style={
                    "marginTop": "24px", "fontSize": "17px", "fontWeight": 600,
                }),
                html.Div(id="orbital-nodes", style={
                    "marginTop": "4px", "fontSize": "12px", "color": "#9a9aad",
                }),
                html.Div(id="orbital-fact", style={
                    "marginTop": "14px", "fontSize": "12.5px", "color": "#ffb877",
                    "lineHeight": "1.5",
                }),
            ]),

            dcc.Graph(id="orbital-graph", style={"flex": "1", "minWidth": "520px", "height": "720px"},
                      config={"displaylogo": False}),
        ]),
    ],
)


# --- ograniczanie zakresow suwakow (l <= n-1, |m| <= l) ---------------------
@app.callback(
    Output("slider-l", "max"),
    Input("slider-n", "value"),
)
def restrict_l(n):
    return n - 1


@app.callback(
    Output("slider-m", "min"),
    Output("slider-m", "max"),
    Input("slider-l", "value"),
)
def restrict_m(l):
    return -l, l


# --- losowy orbital -----------------------------------------------------
@app.callback(
    Output("slider-n", "value"),
    Output("slider-l", "value"),
    Output("slider-m", "value"),
    Input("btn-random", "n_clicks"),
    prevent_initial_call=True,
)
def random_orbital(_n_clicks):
    n = random.randint(1, 3)
    l = random.randint(0, n - 1)
    m = random.randint(-l, l)
    return n, l, m


# --- glowny callback: przelicza wykres + opisy ------------------------------
@app.callback(
    Output("orbital-graph", "figure"),
    Output("orbital-label", "children"),
    Output("orbital-nodes", "children"),
    Output("orbital-fact", "children"),
    Input("slider-n", "value"),
    Input("slider-l", "value"),
    Input("slider-m", "value"),
)
def update_figure(n, l, m):
    n, l, m = clamp_state(n, l, m)
    letter = ORBITAL_LETTERS.get(l, str(l))
    r_nodes, ang_nodes = node_counts(n, l)

    fig = build_figure(n, l, m)
    label = f"Orbital {orbital_label(n, l, m)}"
    nodes = f"węzły radialne: {r_nodes}   ·   węzły kątowe: {ang_nodes}"
    fact = f"[{letter}] {ORBITAL_FUN_FACTS.get(letter, '')}"

    return fig, label, nodes, fact


if __name__ == "__main__":
    print("Uruchamiam aplikacje...")
    print("Otworz w przegladarce: http://127.0.0.1:8050")
    app.run(debug=False, port=8050)
