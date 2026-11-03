"""Load check of the lift base plate MEC-019 on the centre-frame arch (owner decision of 2 Nov 2026, B3).

Load path: everything above the plate (column, carriage, arms, chest equipment) -> 4 x DIN 7500 M8 column screws ->
10 mm 6082-T6 plate -> 4 x ISO 4762 M8 8.8 bolts into the M8 blind rivet nuts of the 2 mm S235JR arch top, and plate
bearing on the arch top, whose stiff support line is the arch front / rear wall (x +/-0.117).

Model (planar, x-z, per robot; both bolt rows and both column screw rows act as pairs):
  plate  : Euler-Bernoulli beam from the plate rear edge to its front edge, E 70 GPa, b 0.140 m, t 0.010 m;
  column : the column base is stiff between its two screw rows (rigid segment);
  arch   : compression-only bearing where the plate sits on the arch top (x -0.080 to 0.117), the walls at x +/-0.117
           rigid; tension-only bolt springs at x +/-0.060 (bolt EA/L in series with the arch top sheet stiffness at
           the rivet nut, from a Navier series of the simply supported 2 mm panel between the walls and the ribs,
           0.234 x 0.154 m, the bolt load spread over the 11.3 mm rivet-nut flange);
  loads  : weight W at the COM of the mass above the plate, horizontal inertia m a at the COM height, as a vertical
           force and a moment on the column axis.
Load cases: static at L1350; braking from 1.5 m/s at the deceleration the analysis allows (the tip-over limit at
L1350) at L1350; the arms at full forward reach with the rated payload (OpenArm 2.0: 4.1 kg nominal, 5.5 kg arm,
0.606 m reach, robot page data) plus braking at L1350. Column at bp050 (largest overhang) and bp000.
Material and part sources: 6082-T6 plate Rp0.2 255 MPa (EN 485-2, 6 < t <= 12.5 mm); S235JR sheet fy 235 MPa, fu 360 MPa
(EN 10025-2); M8 class 8.8 As 36.6 mm2, fub 800 MPa: Ft,Rd 21.1 kN, Fv,Rd 14.1 kN (EN 1993-1-8 Table 3.4, gamma_M2 1.25);
punching (pull-through) of the rivet-nut flange through the 2 mm sheet Bp,Rd = 0.6 pi dm tp fu / gamma_M2 (EN 1993-1-8
Table 3.4) with dm 11.3 mm (CAD rivet-nut flange); the rivet nut's own rated pull-out is the supplier's figure (not in
the repositories) and is listed as a question.
"""
import math

import numpy as np

E_AL, E_ST, NU = 70e9, 210e9, 0.3
PLATE_B, PLATE_T = 0.140, 0.010
RP02_6082, FY_S235, FU_S235 = 255e6, 235e6, 360e6
AS_M8, FUB_88, GM2 = 36.6e-6, 800e6, 1.25
FT_RD = 0.9 * FUB_88 * AS_M8 / GM2
FV_RD = 0.6 * FUB_88 * AS_M8 / GM2
BP_RD = 0.6 * math.pi * 0.0113 * 0.002 * FU_S235 / GM2
SHEET = {"a": 0.234, "b": 0.154, "x0": -0.117, "y0": -0.077, "t": 0.002, "patch": 0.0113}
G = 9.81


def navier(loads, pts, n=61):
    """Simply supported rectangular plate, patch loads [(x, y, P)] (upward positive); returns deflection and the largest
    bending stress at pts [(x, y)] (stress from Mx, My at the point)."""
    a, b, t, u = SHEET["a"], SHEET["b"], SHEET["t"], SHEET["patch"]
    D = E_ST * t ** 3 / (12 * (1 - NU ** 2))
    m = np.arange(1, n + 1)[:, None]
    k = np.arange(1, n + 1)[None, :]
    out = []
    for (px, py) in pts:
        X, Y = px - SHEET["x0"], py - SHEET["y0"]
        w = mx = my = 0.0
        for (lx, ly, P) in loads:
            x0, y0 = lx - SHEET["x0"], ly - SHEET["y0"]
            q0 = P / (u * u)
            qmn = 16 * q0 / (math.pi ** 2 * m * k) * np.sin(m * math.pi * x0 / a) * np.sin(k * math.pi * y0 / b) * np.sin(m * math.pi * u / (2 * a)) * np.sin(k * math.pi * u / (2 * b))
            den = D * math.pi ** 4 * ((m / a) ** 2 + (k / b) ** 2) ** 2
            wmn = qmn / den
            s = np.sin(m * math.pi * X / a) * np.sin(k * math.pi * Y / b)
            w += float((wmn * s).sum())
            mx += float((D * wmn * ((m * math.pi / a) ** 2 + NU * (k * math.pi / b) ** 2) * s).sum())
            my += float((D * wmn * ((k * math.pi / b) ** 2 + NU * (m * math.pi / a) ** 2) * s).sum())
        out.append((w, 6 * max(abs(mx), abs(my)) / t ** 2))
    return out


def sheet_stiffness(xb):
    """Stiffness of the arch top sheet at one rivet nut (a pair at y +/-0.050 loaded together), N/m per bolt."""
    w = navier([(xb, 0.050, 1.0), (xb, -0.050, 1.0)], [(xb, 0.050)])[0][0]
    return 1.0 / w


def beam_solve(x_nodes, ei, loads, springs, bearing, rigid):
    """Planar beam: nodes x, element EI list, nodal loads {i: (Fz, My)} (upward positive), tension-only springs {i: k}
    (active when the node lifts), compression-only bearing nodes (active when the node is pushed down), rigid [(i, j)]
    stiff segments. Contact by active-set iteration. Returns w, theta, active springs, active bearing nodes."""
    n = len(x_nodes)
    bear_on, spr_on = set(bearing), set()
    big = 1e12
    for _ in range(60):
        K = np.zeros((2 * n, 2 * n))
        f = np.zeros(2 * n)
        for e in range(n - 1):
            L = x_nodes[e + 1] - x_nodes[e]
            EI = ei[e] * (1e4 if any(i <= e and e + 1 <= j for i, j in rigid) else 1.0)
            ke = EI / L ** 3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L], [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]])
            ix = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
            K[np.ix_(ix, ix)] += ke
        for i, (Fz, My) in loads.items():
            f[2 * i] += Fz
            f[2 * i + 1] += My
        for i in spr_on:
            K[2 * i, 2 * i] += springs[i]
        for i in bear_on:
            K[2 * i, 2 * i] += big
        u = np.linalg.solve(K, f)
        w = u[0::2]
        nb = {i for i in bearing if (i in bear_on and w[i] <= 0) or (i not in bear_on and w[i] < -1e-9)}
        ns = {i for i in springs if i not in nb and w[i] > 0}
        if nb == bear_on and ns == spr_on:
            break
        bear_on, spr_on = nb, ns
    return w, u[1::2], spr_on, bear_on


def case(name, m, com, a_h, bp, lp):
    """One load case: mass m (kg) at com (x, z, base_footprint), horizontal deceleration a_h (m/s2, inertia forward)."""
    ax = lp["col_axis_x"][bp]
    xr, xf = ax - lp["col_screws"][0] / 2, ax + lp["col_screws"][0] / 2
    bolts = lp["arch_bolts"]["x"]
    x_wall = 0.117
    xs = sorted(set([lp["x"][0], bolts[0], xr, bolts[1], x_wall, ax, xf, lp["x"][1]] + list(np.linspace(lp["x"][0], lp["x"][1], 34))))
    xs = [round(x, 5) for x in xs]
    xs = sorted(set(xs))
    idx = lambda x: int(np.argmin(np.abs(np.array(xs) - x)))
    EI = E_AL * PLATE_B * PLATE_T ** 3 / 12
    W = m * G
    Fh = m * a_h
    z_top = lp["top"]
    Mc = W * (com[0] - ax) + Fh * (com[1] - z_top)        # forward-tipping moment about the column axis at the plate top
    a = (xf - xr) / 2
    F_f, F_r = -W / 2 - Mc / (2 * a), -W / 2 + Mc / (2 * a)  # column screw rows, upward positive
    loads = {idx(xf): (F_f, 0.0), idx(xr): (F_r, 0.0)}
    k_sheet = {b_: sheet_stiffness(b_) for b_ in bolts}
    k_bolt = E_ST * AS_M8 / 0.020
    springs = {idx(b_): 2 * 1.0 / (1.0 / k_sheet[b_] + 1.0 / k_bolt) for b_ in bolts}   # a pair of bolts
    bearing = [i for i, x in enumerate(xs) if lp["x"][0] - 1e-9 <= x <= x_wall + 1e-9]
    w, th, s_on, b_on = beam_solve(xs, [EI] * (len(xs) - 1), loads, springs, bearing, [(idx(xr), idx(xf))])
    T = {b_: (springs[idx(b_)] * w[idx(b_)] / 2 if idx(b_) in s_on else 0.0) for b_ in bolts}   # per bolt
    # plate bending moment along the beam (from the element end rotations): M = EI * curvature
    M = []
    for e in range(len(xs) - 1):
        if any(idx(xr) <= e < idx(xf) for _ in [0]):
            continue
        L = xs[e + 1] - xs[e]
        c0 = (6 * (w[e + 1] - w[e]) / L ** 2 - (4 * th[e] + 2 * th[e + 1]) / L)
        c1 = (-6 * (w[e + 1] - w[e]) / L ** 2 + (2 * th[e] + 4 * th[e + 1]) / L)
        M += [abs(EI * c0), abs(EI * c1)]
    Mmax = max(M) if M else 0.0
    sigma_plate = Mmax / (PLATE_B * PLATE_T ** 2 / 6)
    t_rear = max(T.values())
    sheet = navier([(bolts[0], 0.050, T[bolts[0]]), (bolts[0], -0.050, T[bolts[0]]), (bolts[1], 0.050, T[bolts[1]]), (bolts[1], -0.050, T[bolts[1]])],
                   [(bolts[0], 0.050), (bolts[1], 0.050), (bolts[0] - 0.006, 0.050), (bolts[0] + 0.006, 0.050)])
    sig_sheet = max(s for _, s in sheet)
    v_bolt = Fh / 4
    tilt = abs(th[idx(ax)])
    inter = v_bolt / FV_RD + t_rear / (1.4 * FT_RD)
    return {"case": name, "bp": bp, "mass_kg": round(m, 2), "com_m": [round(com[0], 4), round(com[1], 4)], "decel_m_s2": round(a_h, 2),
            "moment_at_column_axis_Nm": round(Mc, 1), "column_screw_rows_N": {"rear": round(F_r, 1), "front": round(F_f, 1)},
            "bolt_tension_per_bolt_N": {("x %+.3f" % b_): round(v, 1) for b_, v in T.items()}, "bolt_shear_per_bolt_N": round(v_bolt, 1),
            "bolt_utilisation": round(inter, 3), "bolt_Ft_Rd_kN": round(FT_RD / 1000, 1), "bolt_Fv_Rd_kN": round(FV_RD / 1000, 1),
            "rivet_nut_pull_through_utilisation": round(t_rear / BP_RD, 3), "Bp_Rd_kN": round(BP_RD / 1000, 1),
            "plate_max_moment_Nm": round(Mmax, 1), "plate_stress_MPa": round(sigma_plate / 1e6, 1), "plate_utilisation": round(sigma_plate / RP02_6082, 3),
            "arch_sheet_stress_MPa": round(sig_sheet / 1e6, 1), "arch_sheet_utilisation": round(sig_sheet / FY_S235, 3),
            "arch_sheet_uplift_mm": round(max(d for d, _ in sheet) * 1000, 3),
            "plate_deflection_at_column_front_mm": round(w[idx(xf)] * 1000, 3), "column_tilt_deg": round(math.degrees(tilt), 3)}


def run(lp, above, decel, arms_forward):
    """above: {stop: (mass, com xyz)} of the mass above the plate (bp000); decel: allowed deceleration (m/s2);
    arms_forward: (mass, com xyz) of the same set with both arms at full forward reach and the rated payload (L1350)."""
    out = []
    for bp in ("bp050", "bp000"):
        dx = lp["col_axis_x"][bp] - lp["col_axis_x"]["bp000"]
        m, c = above["L1350"]
        out.append(case("static, L1350", m, (c[0] + dx, c[2]), 0.0, bp, lp))
        out.append(case("braking from 1.5 m/s at %.2f m/s2, L1350" % decel, m, (c[0] + dx, c[2]), decel, bp, lp))
        m2, c2 = arms_forward
        out.append(case("arms at full forward reach, 2 x 4.1 kg payload, braking at %.2f m/s2, L1350" % decel, m2, (c2[0] + dx, c2[2]), decel, bp, lp))
    worst = max(out, key=lambda r: max(r["bolt_utilisation"], r["rivet_nut_pull_through_utilisation"], r["plate_utilisation"], r["arch_sheet_utilisation"]))
    shoulder_h = above["L1350"][1][2]
    return {"cases": out, "worst": worst["case"] + " (" + worst["bp"] + ")",
            "max_utilisation": {k: max(r[k] for r in out) for k in ("bolt_utilisation", "rivet_nut_pull_through_utilisation", "plate_utilisation", "arch_sheet_utilisation")},
            "max_column_tilt_deg": max(r["column_tilt_deg"] for r in out), "shoulder_height_ref_m": shoulder_h,
            "overhang": {bp: {"column_axis_ahead_of_front_arch_bolts_m": round(lp["col_axis_x"][bp] - lp["arch_bolts"]["x"][1], 3),
                              "column_front_ahead_of_arch_front_wall_m": round(lp["col_axis_x"][bp] + 0.120 - 0.117, 3),
                              "column_front_ahead_of_rear_arch_bolts_m": round(lp["col_axis_x"][bp] + 0.120 - lp["arch_bolts"]["x"][0], 3)} for bp in ("bp000", "bp050")}}
