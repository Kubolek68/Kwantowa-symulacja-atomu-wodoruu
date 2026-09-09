"""
hydrogen_orbital.py
====================
Rdzen fizyczny projektu: analityczne rozwiazanie rownania Schroedingera
dla atomu wodoru (elektron w potencjale kulombowskim jadra).

Pelna funkcja falowa rozdziela sie na czesc radialna i katowa:

    psi_nlm(r, theta, phi) = R_nl(r) * Y_lm(theta, phi)

gdzie:
    n - glowna liczba kwantowa      (n = 1, 2, 3, ...)      -> rozmiar/energia orbitalu
    l - poboczna (orbitalna) l.k.   (0 <= l <= n-1)          -> ksztalt orbitalu (s,p,d,...)
    m - magnetyczna liczba kwant.   (-l <= m <= l)           -> orientacja orbitalu

Gestosc prawdopodobienstwa znalezienia elektronu w danym punkcie przestrzeni
to kwadrat modulu funkcji falowej:

    rho(r, theta, phi) = |psi_nlm(r, theta, phi)|^2

Kluczowy fakt upraszczajacy wizualizacje: |Y_lm|^2 NIE zalezy od kata phi
(bo Y_lm ~ e^(i*m*phi), a |e^(i*m*phi)|^2 = 1). Dzieki temu gestosc jest
symetryczna wzgledem obrotu wokol osi z i mozna ja w pelni pokazac na
jednym przekroju plaszczyzna (np. plaszczyzna x-z) - dokladnie tak, jak na
klasycznych podrecznikowych rysunkach orbitali atomowych.
"""

from __future__ import annotations

import numpy as np
from scipy.special import genlaguerre, lpmv, factorial

# Promien Bohra - w jednostkach atomowych przyjmujemy a0 = 1.
# Wszystkie odleglosci (r, zasieg wykresu) sa wtedy wyrazone w "promieniach Bohra".
A0 = 1.0


def validate_quantum_numbers(n: int, l: int, m: int) -> None:
    """Sprawdza, czy trojka (n, l, m) jest fizycznie dozwolona."""
    if n < 1:
        raise ValueError("n musi byc >= 1")
    if not (0 <= l <= n - 1):
        raise ValueError(f"l musi spelniac 0 <= l <= n-1 (dla n={n}: l <= {n - 1})")
    if not (-l <= m <= l):
        raise ValueError(f"m musi spelniac -l <= m <= l (dla l={l}: |m| <= {l})")


def radial_wavefunction(n: int, l: int, r: np.ndarray) -> np.ndarray:
    """
    Znormalizowana czesc radialna R_nl(r), zbudowana ze stowarzyszonych
    wielomianow Laguerre'a. Znormalizowana tak, ze:

        integral_0^inf  R_nl(r)^2 * r^2 dr = 1
    """
    rho = 2.0 * r / (n * A0)
    norm = np.sqrt(
        (2.0 / (n * A0)) ** 3
        * factorial(n - l - 1)
        / (2.0 * n * factorial(n + l))
    )
    laguerre_poly = genlaguerre(n - l - 1, 2 * l + 1)
    return norm * np.exp(-rho / 2.0) * rho ** l * laguerre_poly(rho)


def angular_probability(l: int, m: int, theta: np.ndarray) -> np.ndarray:
    """
    |Y_lm(theta, phi)|^2 - gestosc katowa, niezalezna od phi (patrz docstring
    modulu). Zbudowana ze stowarzyszonych wielomianow Legendre'a.
    """
    m_abs = abs(m)
    norm = (2 * l + 1) / (4 * np.pi) * factorial(l - m_abs) / factorial(l + m_abs)
    legendre = lpmv(m_abs, l, np.cos(theta))
    return norm * legendre ** 2


def probability_density(n: int, l: int, m: int, r: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """Pelna gestosc prawdopodobienstwa |psi_nlm(r, theta)|^2 (bez zaleznosci od phi)."""
    validate_quantum_numbers(n, l, m)
    R = radial_wavefunction(n, l, r)
    Theta = angular_probability(l, m, theta)
    return (R ** 2) * Theta


def density_slice(n: int, l: int, m: int, extent: float, resolution: int = 400):
    """
    Buduje siatke 2D (przekroj w plaszczyznie x-z, czyli phi=0) z gestoscia
    prawdopodobienstwa. Zwraca (X, Z, gestosc) gotowe do narysowania np.
    funkcja pcolormesh/imshow.
    """
    x = np.linspace(-extent, extent, resolution)
    z = np.linspace(-extent, extent, resolution)
    X, Z = np.meshgrid(x, z)

    R = np.sqrt(X ** 2 + Z ** 2)
    R_safe = np.where(R == 0, 1e-12, R)
    Theta = np.arccos(np.clip(Z / R_safe, -1.0, 1.0))

    density = probability_density(n, l, m, R, Theta)
    return X, Z, density


def suggested_extent(n: int, margin: float = 1.2) -> float:
    """
    Wyznacza sensowny zasieg wykresu (w promieniach Bohra) dla danego n:
    promien, w ktorym (dla najbardziej "rozlaglego" l przy tym n) miesci
    sie 99% radialnego prawdopodobienstwa, plus margines.
    """
    r = np.linspace(1e-6, 60.0 * n ** 2, 200_000)
    max_r99 = 0.0
    for l in range(n):
        density = radial_wavefunction(n, l, r) ** 2 * r ** 2
        cumulative = np.cumsum(density)
        cumulative /= cumulative[-1]
        idx = int(np.searchsorted(cumulative, 0.99))
        max_r99 = max(max_r99, r[idx])
    return max_r99 * margin


ORBITAL_LETTERS = {0: "s", 1: "p", 2: "d", 3: "f"}

ORBITAL_FUN_FACTS = {
    "s": "Ksztalt: kula. Elektron 's' nie ma ulubionego kierunku - "
         "prawdopodobienstwo jego znalezienia jest takie samo we wszystkich stronach.",
    "p": "Ksztalt: hantle / dwa platki. Pojawia sie plaszczyzna wezlowa "
         "(gdzie gestosc spada do zera) przechodzaca przez jadro.",
    "d": "Ksztalt: koniczynka lub torus z 'pierscieniem'. Orbitale d maja "
         "wiecej plaszczyzn/powierzchni wezlowych niz p.",
}


def orbital_label(n: int, l: int, m: int) -> str:
    """Zwraca podrecznikowa etykiete typu '3d', 'm=+1'."""
    letter = ORBITAL_LETTERS.get(l, str(l))
    m_str = f"+{m}" if m > 0 else str(m)
    return f"{n}{letter} (m={m_str})"


def node_counts(n: int, l: int) -> tuple[int, int]:
    """
    Liczba wezlow radialnych i katowych (fakt, ktory dobrze widac na
    wykresie - to liczba 'pierscieni' i 'plaszczyzn', gdzie gestosc = 0).
    """
    radial_nodes = n - l - 1
    angular_nodes = l
    return radial_nodes, angular_nodes
