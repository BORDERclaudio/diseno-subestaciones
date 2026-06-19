import math
import numpy as np

MU0 = 4 * math.pi * 1e-7
g = 9.81

def solve_psi(phi, zeta):
    a = phi**2
    b = phi * (2 + zeta)
    c = 1 + 2 * zeta
    d = -zeta * (2 + phi)
    roots = np.roots([a, b, c, d])
    real = roots[np.isreal(roots)].real
    psi_vals = real[(real > 0) & (real <= 1)]
    return float(psi_vals[0]) if len(psi_vals) > 0 else 1.0

def solve_psi_iec(phi, zeta):
    a = phi + zeta
    b = 2 * phi + 1
    c = zeta - 2
    d = -2 * phi
    roots = np.roots([a, b, c, d])
    real = roots[np.isreal(roots)].real
    psi_vals = real[(real > 0) & (real <= 1)]
    return float(psi_vals[0]) if len(psi_vals) > 0 else 1.0

def calcular(p):
    n_c = p["n"]
    d = p["d_mm"] / 1000
    m_s = p["m_s"]
    As = p["As_mm2"] * 1e-6
    l = p["l"]
    a = p["a"]
    li = p["li"]
    fes = p["fes"]
    h = p["h"]
    V = p["V"]
    Cz = p["Cz"]
    Gf = p["Gf"]
    Cf = p["Cf"]
    t_ice = p["t_ice"]
    w_ice = p["w_ice"]
    Ik3 = p["Ik3_kA"] * 1000
    Tk1 = p["Tk1"]
    S_sup = p["S_sup"]
    E_eff = p["E_eff_GPa"] * 1e9
    cth = p["cth_e18"] * 1e-18

    lc = l - 2 * li

    Fc = g * m_s
    FI = w_ice * (t_ice / 1000) * math.pi * (d + t_ice / 1000) if t_ice > 0 else 0
    w_tot = Fc + FI
    Q = 0.613
    FW = Q * V**2 * d * Cf * Cz * Gf
    w_res = math.sqrt(w_tot**2 + FW**2)
    Fst = n_c * m_s * g * l**2 / (8 * fes)

    d_viento = math.degrees(math.atan2(FW, w_tot))
    bh_viento = fes * math.sin(math.radians(d_viento))

    Fp = (MU0 / (2 * math.pi)) * 0.75 * (Ik3**2 / a) * (lc / l)
    r = Fp / (n_c * m_s * g) if (n_c * m_s * g) > 0 else 0
    d1 = math.degrees(math.atan(r))

    T = 2 * math.pi * math.sqrt(0.8 * fes / g)
    factor = 1 + r**2 * (1 - (math.pi**2 / 64) * (d1 / 90)**2)
    Tres = T / factor**0.25 if factor > 0 else T

    ratio = Tk1 / Tres
    if ratio <= 0.5:
        d_end_iec = d1 * (1 - math.cos(2 * math.pi * ratio)) / 2
        dk_ieee = d1 * (1 - math.cos(2 * math.pi * ratio))
    else:
        d_end_iec = d1
        dk_ieee = 2 * d1

    chi_iec = 1 / (1 + r)
    if d_end_iec <= 90:
        val = chi_iec * math.sin(math.radians(d_end_iec)) - chi_iec
        val = max(-1, min(1, val))
        d_max_iec = d_end_iec + math.degrees(math.asin(val))
    else:
        d_max_iec = d_end_iec + 180 * (1 - chi_iec)

    if dk_ieee <= 90:
        chi_ieee = 1 - r * math.sin(math.radians(dk_ieee))
    else:
        chi_ieee = 1 - r
    chi_ieee = max(-1, min(1, chi_ieee))
    if chi_ieee >= 0.766:
        dm_ieee = 1.25 * math.degrees(math.acos(chi_ieee))
    elif chi_ieee >= -0.985:
        dm_ieee = 10 + math.degrees(math.acos(chi_ieee))
    else:
        dm_ieee = 180

    N_val = 1 / (S_sup * l) + 1 / (l * n_c * E_eff * As)
    zeta_ieee = (n_c * g * m_s * l)**2 / (24 * Fst**3 * N_val) if Fst > 0 else 0
    zeta_iec = (n_c * m_s * g * l)**2 / (24 * Fst**2 * N_val) if Fst > 0 else 0

    if Tk1 >= Tres / 4:
        phi_ieee = 3 * (math.sqrt(1 + r**2) - 1)
        phi_iec = (1 + r/3) * (1 + (d_end_iec + d1)/180 * ratio * r) - 1
    else:
        phi_ieee = 3 * (r * math.sin(math.radians(dk_ieee)) + math.cos(math.radians(dk_ieee)) - 1)
        phi_iec = (r/3) * (math.cos(math.radians(d_end_iec)) + (d1/90) * ratio * r)

    psi_ieee = solve_psi(phi_ieee, zeta_ieee)
    psi_iec = solve_psi_iec(phi_iec, zeta_iec)

    Ft_ieee = Fst * (1 + phi_ieee * psi_ieee)
    if n_c >= 2:
        Ft_ieee *= 1.1
    Ft_iec = Fst * (1 + phi_iec * psi_iec)

    Ff_ieee = 1.2 * Fst * math.sqrt(1 + 8 * zeta_ieee * dm_ieee / 180)
    Ff_iec = Fst * (1.2 + zeta_iec * (1 + 8 * d_max_iec / 180))

    e_ela = N_val * (Ft_ieee - Fst)
    if Tk1 >= Tres / 4:
        e_th = cth * (Ik3 / (n_c * As))**2 * Tres / 4
        e_th_iec = cth * (Ik3 / (n_c * As))**2 * Tres * (Tk1 / Tres - 0.25)
    else:
        e_th = cth * (Ik3 / (n_c * As))**2 * Tk1
        e_th_iec = cth * (Ik3 / (n_c * As))**2 * Tk1**2 / (4 * Tres)

    CD_ieee = 1 + (3/8) * (l / fes)**2 * (e_ela + e_th)
    CD_iec = math.sqrt(1 + (3/8) * (l / fes)**2 * (e_ela + e_th_iec))

    if r <= 0.8:
        CF = 1.05
    elif r < 1.8:
        CF = 0.97 + 0.1 * r
    else:
        CF = 1.15

    fed = CF * CD_ieee * fes

    if dm_ieee >= d1:
        bh_ieee = CF * CD_ieee * fes * math.sin(math.radians(d1))
    else:
        bh_ieee = CF * CD_ieee * fes * math.sin(math.radians(dm_ieee))

    if d_max_iec >= d1:
        bh_iec = (fed - li) * math.sin(math.radians(d_max_iec)) + li * math.sin(math.radians(d1))
    else:
        bh_iec = fed * math.sin(math.radians(d_max_iec))

    a_min_ieee = a - 2 * bh_ieee
    a_min_iec = a - 2 * bh_iec

    return dict(
        Fc=round(Fc,2), FI=round(FI,2), w_tot=round(w_tot,2),
        FW=round(FW,2), w_res=round(w_res,2),
        Fst=round(Fst,0), d_viento=round(d_viento,2), bh_viento=round(bh_viento,3),
        Fp=round(Fp,1), r=round(r,3), d1=round(d1,2),
        T=round(T,3), Tres=round(Tres,3),
        d_end_iec=round(d_end_iec,2), dk_ieee=round(dk_ieee,2),
        d_max_iec=round(d_max_iec,2), dm_ieee=round(dm_ieee,2),
        zeta_iec=round(zeta_iec,4), zeta_ieee=round(zeta_ieee,4),
        phi_iec=round(phi_iec,4), phi_ieee=round(phi_ieee,4),
        psi_iec=round(psi_iec,4), psi_ieee=round(psi_ieee,4),
        Ft_iec=round(Ft_iec,0), Ft_ieee=round(Ft_ieee,0),
        Ff_iec=round(Ff_iec,0), Ff_ieee=round(Ff_ieee,0),
        CD_iec=round(CD_iec,4), CD_ieee=round(CD_ieee,4),
        CF=round(CF,4), fed=round(fed,3),
        bh_iec=round(bh_iec,3), bh_ieee=round(bh_ieee,3),
        a_min_iec=round(a_min_iec,3), a_min_ieee=round(a_min_ieee,3),
    )
