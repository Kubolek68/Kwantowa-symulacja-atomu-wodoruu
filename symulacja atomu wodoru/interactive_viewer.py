"""
interactive_viewer.py
=======================
Interaktywny eksplorator gestosci prawdopodobienstwa elektronu w atomie
wodoru. Suwakami wybierasz liczby kwantowe n, l, m i na biezaco widzisz,
jak zmienia sie ksztalt "chmury elektronowej".

Uruchomienie:
    python interactive_viewer.py

Sterowanie:
    - suwak n: glowna liczba kwantowa (1, 2, 3)
    - suwak l: poboczna liczba kwantowa (0=s, 1=p, 2=d) - automatycznie
      ograniczana do l <= n-1
    - suwak m: magnetyczna liczba kwantowa - automatycznie ograniczana
      do -l <= m <= l
    - przycisk "Zapisz PNG": zapisuje aktualny widok do pliku
    - przycisk "Losowy orbital": wybiera losowa, dozwolona kombinacje n,l,m
"""

import random

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import numpy as np

from hydrogen_orbital import (
    density_slice,
    suggested_extent,
    orbital_label,
    node_counts,
    ORBITAL_LETTERS,
    ORBITAL_FUN_FACTS,
)

CMAP = "afmhot"
RESOLUTION = 300

# ---------------------------------------------------------------------------
# Stan aplikacji
# ---------------------------------------------------------------------------
state = {"n": 1, "l": 0, "m": 0}
_guard = False  # zabezpieczenie przed rekurencyjnym wywolywaniem callbackow


def clamp_state(n: int, l: int, m: int) -> tuple[int, int, int]:
    n = max(1, min(3, n))
    l = max(0, min(n - 1, l))
    m = max(-l, min(l, m))
    return n, l, m


# ---------------------------------------------------------------------------
# Budowa figury
# ---------------------------------------------------------------------------
fig = plt.figure(figsize=(9, 8.5), facecolor="black")
ax_plot = fig.add_axes([0.08, 0.30, 0.84, 0.62])
ax_plot.set_facecolor("black")

im = ax_plot.imshow(
    np.zeros((RESOLUTION, RESOLUTION)),
    cmap=CMAP,
    origin="lower",
)
ax_plot.set_xticks([])
ax_plot.set_yticks([])

title_text = fig.text(
    0.5, 0.955, "", color="white", fontsize=16, fontweight="bold", ha="center"
)
info_text = fig.text(
    0.5, 0.925, "", color="#dddddd", fontsize=10, ha="center"
)
fact_text = fig.text(
    0.5, 0.235, "", color="#ffcc88", fontsize=9.5, ha="center", wrap=True
)
hint_text = fig.text(
    0.5, 0.205,
    "Przeciagnij LPM, aby przesunac widok - scroll, aby przyblizyc/oddalic",
    color="#888888", fontsize=8.5, ha="center",
)

# --- suwaki -----------------------------------------------------------------
slider_color = "#552200"
ax_n = fig.add_axes([0.25, 0.15, 0.55, 0.03])
ax_l = fig.add_axes([0.25, 0.10, 0.55, 0.03])
ax_m = fig.add_axes([0.25, 0.05, 0.55, 0.03])

slider_n = Slider(ax_n, "n", 1, 3, valinit=1, valstep=1, color=slider_color)
slider_l = Slider(ax_l, "l", 0, 2, valinit=0, valstep=1, color=slider_color)
slider_m = Slider(ax_m, "m", -2, 2, valinit=0, valstep=1, color=slider_color)

for s in (slider_n, slider_l, slider_m):
    s.label.set_color("white")
    s.valtext.set_color("white")

# --- przyciski ----------------------------------------------------------
ax_save = fig.add_axes([0.05, 0.005, 0.22, 0.035])
btn_save = Button(ax_save, "Zapisz PNG", color="#333333", hovercolor="#555555")
btn_save.label.set_color("white")

ax_random = fig.add_axes([0.30, 0.005, 0.27, 0.035])
btn_random = Button(ax_random, "Losowy orbital", color="#333333", hovercolor="#555555")
btn_random.label.set_color("white")

ax_reset_view = fig.add_axes([0.60, 0.005, 0.27, 0.035])
btn_reset_view = Button(ax_reset_view, "Resetuj widok", color="#333333", hovercolor="#555555")
btn_reset_view.label.set_color("white")


# ---------------------------------------------------------------------------
# Logika odswiezania
# ---------------------------------------------------------------------------
def redraw():
    n, l, m = state["n"], state["l"], state["m"]
    extent = suggested_extent(n)
    _, _, density = density_slice(n, l, m, extent, RESOLUTION)
    display_values = np.sqrt(density)  # skalowanie tylko do wyswietlania

    im.set_data(display_values)
    im.set_extent([-extent, extent, -extent, extent])
    im.set_clim(vmin=0, vmax=display_values.max())
    # UWAGA: celowo NIE resetujemy tu xlim/ylim - inaczej kazda zmiana
    # suwaka (nawet samego l lub m przy tym samym n) kasowalaby
    # przesuniecie/przyblizenie zrobione mysza. Widok resetuje sie tylko
    # przy zmianie n (patrz reset_view) lub przyciskiem "Resetuj widok".

    letter = ORBITAL_LETTERS.get(l, str(l))
    r_nodes, ang_nodes = node_counts(n, l)
    title_text.set_text(f"Orbital {orbital_label(n, l, m)}")
    info_text.set_text(
        f"n={n}, l={l}, m={m}   |   wezly radialne: {r_nodes}   "
        f"wezly katowe: {ang_nodes}   |   zasieg: ±{extent:.1f} a0"
    )
    fact_text.set_text(f"[{letter}] " + ORBITAL_FUN_FACTS.get(letter, ""))

    fig.canvas.draw_idle()


def on_slider_change(_val=None):
    global _guard
    if _guard:
        return
    _guard = True

    n, l, m = clamp_state(
        int(round(slider_n.val)), int(round(slider_l.val)), int(round(slider_m.val))
    )

    if int(round(slider_l.val)) != l:
        slider_l.set_val(l)
    if int(round(slider_m.val)) != m:
        slider_m.set_val(m)

    n_changed = n != state["n"]
    state.update(n=n, l=l, m=m)
    if n_changed:
        reset_view()
    redraw()
    _guard = False


def reset_view():
    """Przywraca domyslne przybliznie/wysrodkowanie dla aktualnego n."""
    extent = suggested_extent(state["n"])
    ax_plot.set_xlim(-extent, extent)
    ax_plot.set_ylim(-extent, extent)


def on_save(_event):
    n, l, m = state["n"], state["l"], state["m"]
    filename = f"orbital_n{n}_l{l}_m{m}.png"
    fig.savefig(filename, dpi=150, facecolor="black")
    print(f"Zapisano: {filename}")


def on_random(_event):
    n = random.randint(1, 3)
    l = random.randint(0, n - 1)
    m = random.randint(-l, l)
    slider_n.set_val(n)  # to wywola on_slider_change i ustawi reszte
    slider_l.set_val(l)
    slider_m.set_val(m)


def on_reset_view(_event):
    reset_view()
    fig.canvas.draw_idle()


# --- przesuwanie (pan) lewym przyciskiem myszy + zoom kolkiem scrolla -------
_pan = {"active": False, "x0": None, "y0": None, "xlim0": None, "ylim0": None}


def on_press(event):
    if event.inaxes != ax_plot or event.button != 1:
        return
    _pan.update(
        active=True,
        x0=event.xdata,
        y0=event.ydata,
        xlim0=ax_plot.get_xlim(),
        ylim0=ax_plot.get_ylim(),
    )


def on_motion(event):
    if not _pan["active"] or event.inaxes != ax_plot or event.xdata is None:
        return
    dx = event.xdata - _pan["x0"]
    dy = event.ydata - _pan["y0"]
    xlim0, ylim0 = _pan["xlim0"], _pan["ylim0"]
    ax_plot.set_xlim(xlim0[0] - dx, xlim0[1] - dx)
    ax_plot.set_ylim(ylim0[0] - dy, ylim0[1] - dy)
    fig.canvas.draw_idle()


def on_release(_event):
    _pan["active"] = False


def on_scroll(event):
    if event.inaxes != ax_plot or event.xdata is None:
        return
    factor = 1.2 if event.button == "down" else 1 / 1.2
    xlim, ylim = ax_plot.get_xlim(), ax_plot.get_ylim()
    xdata, ydata = event.xdata, event.ydata

    new_w = (xlim[1] - xlim[0]) * factor
    new_h = (ylim[1] - ylim[0]) * factor
    relx = (xlim[1] - xdata) / (xlim[1] - xlim[0])
    rely = (ylim[1] - ydata) / (ylim[1] - ylim[0])

    ax_plot.set_xlim(xdata - new_w * (1 - relx), xdata + new_w * relx)
    ax_plot.set_ylim(ydata - new_h * (1 - rely), ydata + new_h * rely)
    fig.canvas.draw_idle()


slider_n.on_changed(on_slider_change)
slider_l.on_changed(on_slider_change)
slider_m.on_changed(on_slider_change)
btn_save.on_clicked(on_save)
btn_random.on_clicked(on_random)
btn_reset_view.on_clicked(on_reset_view)

fig.canvas.mpl_connect("button_press_event", on_press)
fig.canvas.mpl_connect("motion_notify_event", on_motion)
fig.canvas.mpl_connect("button_release_event", on_release)
fig.canvas.mpl_connect("scroll_event", on_scroll)

reset_view()
redraw()

if __name__ == "__main__":
    plt.show()
