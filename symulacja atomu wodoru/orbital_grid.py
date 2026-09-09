"""
orbital_grid.py
================
Generuje siatke porownawcza gestosci prawdopodobienstwa dla n = 1,2,3
oraz l = 0,1,2 (s, p, d) - dokladnie tak, jak na klasycznym podrecznikowym
zestawieniu orbitali atomu wodoru. Dla kazdej pary (n, l) uzywany jest
przekroj z m = 0 (najbardziej "podrecznikowy" ksztalt, symetryczny wzgledem
osi z).

Uruchomienie:
    python orbital_grid.py

Wynik: plik orbital_grid.png w tym samym katalogu.
"""

import matplotlib
matplotlib.use("Agg")  # backend bez okna - zapisujemy od razu do pliku
import matplotlib.pyplot as plt
import numpy as np

from hydrogen_orbital import (
    density_slice,
    suggested_extent,
    orbital_label,
    node_counts,
)

N_VALUES = [1, 2, 3]
L_VALUES = [0, 1, 2]
CMAP = "afmhot"


def main(resolution: int = 350, save_path: str = "orbital_grid.png"):
    fig, axes = plt.subplots(
        len(N_VALUES), len(L_VALUES),
        figsize=(10, 10),
        facecolor="black",
    )

    for row, n in enumerate(N_VALUES):
        extent = suggested_extent(n)
        for col, l in enumerate(L_VALUES):
            ax = axes[row, col]
            ax.set_facecolor("black")

            if l > n - 1:
                # Kombinacja fizycznie niedozwolona (l musi byc < n) -
                # zostawiamy puste, czarne pole - dokladnie jak w oryginale.
                ax.axis("off")
                continue

            m = 0
            X, Z, density = density_slice(n, l, m, extent, resolution)
            # Skalowanie nieliniowe (pierwiastek) do wyswietlania: surowa gestosc
            # ma bardzo ostry pik blisko jadra, przez co slabsze, dalsze "pierscienie"
            # staja sie niewidoczne przy skali liniowej. To wplywa TYLKO na kolor,
            # nie na dane fizyczne.
            display_values = np.sqrt(density)
            ax.imshow(
                display_values,
                extent=[-extent, extent, -extent, extent],
                origin="lower",
                cmap=CMAP,
            )
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_visible(False)

            r_nodes, ang_nodes = node_counts(n, l)
            ax.set_title(
                orbital_label(n, l, m),
                color="white",
                fontsize=11,
                pad=6,
            )

        # etykieta n z boku wiersza
        axes[row, 0].text(
            -0.25, 0.5, f"n={n}",
            transform=axes[row, 0].transAxes,
            color="white", fontsize=13, fontweight="bold",
            ha="center", va="center", rotation=90,
        )

    # etykiety kolumn (s, p, d) u gory
    letters = {0: "s", 1: "p", 2: "d"}
    for col, l in enumerate(L_VALUES):
        axes[0, col].text(
            0.5, 1.18, letters[l],
            transform=axes[0, col].transAxes,
            color="white", fontsize=16, fontweight="bold",
            ha="center", va="center",
        )

    fig.suptitle(
        "Gestosc prawdopodobienstwa polozenia elektronu w atomie wodoru\n"
        "(przekroj plaszczyzna x-z, m = 0)",
        color="white", fontsize=12,
    )
    fig.tight_layout(rect=[0.03, 0, 1, 0.93])
    fig.savefig(save_path, dpi=150, facecolor="black")
    print(f"Zapisano: {save_path}")


if __name__ == "__main__":
    main()
