#!/usr/bin/env python3
"""Static "as-is" illustration of the LaGuardia March 22, 2026 accident geometry, drawn from viz/klga.geojson (OSM) with
the NTSB preliminary report's names and times. Two PNGs: the ground view and a zoom on the D × runway 4 crossing.

  python3 viz/lga/asis_diagram.py --out-main docs/lga_asis_diagram.png --out-inset docs/lga_asis_crossing.png
"""
import argparse, json, math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon

PAPER, INK, MUTED = "#f4f2ec", "#1b1f27", "#5d6470"
RWY, RWY_EDGE, TWY = "#3a3f47", "#2a2e35", "#e3c24a"
BLUE, ORANGE, RED = "#1f6fe0", "#ef8a1d", "#d7263d"
LAT0 = 40.7755


def xy(lon, lat):  # metres, equirectangular about the crossing
    return (lon + 73.878884) * 111320 * math.cos(math.radians(LAT0)), (lat - 40.775525) * 110574


def load():
    g = json.load(open("viz/klga.geojson")); s = json.load(open("viz/scenario_lga_04.json"))
    rw = {f["properties"]["ref"]: [xy(*c) for c in f["geometry"]["coordinates"]] for f in g["features"] if f["properties"].get("kind") == "runway"}
    tw = [( f["properties"].get("ref"), [xy(*c) for c in f["geometry"]["coordinates"]]) for f in g["features"]
          if f["geometry"]["type"] == "LineString" and f["properties"].get("kind") != "runway"]
    return rw, tw, s


def runway(ax, pts, lw, numbers=True, label_ends=None, fs=11):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=RWY_EDGE, lw=lw + 2, solid_capstyle="butt", zorder=3)
    ax.plot(xs, ys, color=RWY, lw=lw, solid_capstyle="butt", zorder=4)
    ax.plot(xs, ys, color="#ffffff", lw=1.1, ls=(0, (6, 6)), zorder=5, alpha=0.9)
    if label_ends:
        for (x, y), t, dx, dy in label_ends:
            ax.text(x + dx, y + dy, t, color="#ffffff", fontsize=fs, fontweight="bold", ha="center", va="center", zorder=7,
                    bbox=dict(boxstyle="round,pad=0.25", fc=INK, ec="none"))


def aircraft(ax, x, y, heading_deg, size, color=BLUE, z=9):
    # simple top-down airliner silhouette, nose along heading (0 = +x)
    body = [(1.0, 0), (0.75, 0.12), (-0.55, 0.12), (-0.8, 0.08), (-0.8, -0.08), (-0.55, -0.12), (0.75, -0.12)]
    wing = [(0.25, 0.1), (-0.25, 0.1), (-0.5, 0.95), (-0.35, 0.95), (0.25, 0.1)]
    wing2 = [(x_, -y_) for x_, y_ in wing]
    tail = [(-0.6, 0.08), (-0.85, 0.08), (-0.95, 0.42), (-0.85, 0.42), (-0.6, 0.08)]
    tail2 = [(x_, -y_) for x_, y_ in tail]
    th = math.radians(heading_deg); c, s_ = math.cos(th), math.sin(th)
    for poly in (wing, wing2, tail, tail2, body):
        pts = [(x + size * (px * c - py * s_), y + size * (px * s_ + py * c)) for px, py in poly]
        ax.add_patch(Polygon(pts, closed=True, fc=color, ec="#ffffff", lw=0.8, zorder=z))


def truck(ax, x, y, heading_deg, size, color=ORANGE, z=9):
    th = math.radians(heading_deg); c, s_ = math.cos(th), math.sin(th)
    box = [(1, 0.45), (-1, 0.45), (-1, -0.45), (1, -0.45)]
    cab = [(1, 0.45), (0.45, 0.45), (0.45, -0.45), (1, -0.45)]
    for poly, col in ((box, color), (cab, "#ffd27a")):
        pts = [(x + size * (px * c - py * s_), y + size * (px * s_ + py * c)) for px, py in poly]
        ax.add_patch(Polygon(pts, closed=True, fc=col, ec=INK, lw=0.8, zorder=z))


def main_view(rw, tw, s, out):
    fig, ax = plt.subplots(figsize=(14, 10), dpi=140); fig.patch.set_facecolor(PAPER); ax.set_facecolor("#ece9e1")
    for ref, pts in tw:
        xs, ys = zip(*pts); ax.plot(xs, ys, color=TWY, lw=3.2, solid_capstyle="round", zorder=2, alpha=0.95)
    r4 = rw["04/22"]; r13 = rw["13/31"]
    runway(ax, r13, 16, label_ends=[(r13[0], "13", -60, 40), (r13[-1], "31", -50, -70)])
    runway(ax, r4, 16, label_ends=[(r4[-1], "04", -70, -40), (r4[0], "22", 80, 5)])
    # runway names
    mid = r4[len(r4) // 2]; ax.text(mid[0] + 260, mid[1] - 230, "Runway 04/22", color=MUTED, fontsize=11, rotation=50, ha="center")
    mid = r13[len(r13) // 2]; ax.text(mid[0] + 100, mid[1] + 160, "Runway 13/31", color=MUTED, fontsize=11, rotation=-25, ha="center")
    # taxiway labels near the crossing
    for ref, pts in tw:
        if ref in ("D", "AA", "BB"):
            x, y = pts[len(pts) // 2]
            if ref == "D": x, y = -470, 110
            if ref == "AA": x, y = -116, -75
            if ref == "BB": x, y = -215, -75
            ax.text(x, y, ref, fontsize=10, fontweight="bold", color=INK, ha="center", va="center", zorder=8,
                    bbox=dict(boxstyle="square,pad=0.25", fc=TWY, ec=INK, lw=0.8))
    # JAZZ 646: along runway 4 from before the threshold to the D crossing
    thr = r4[-1]; cross = xy(*s["intersection"])
    dx, dy = cross[0] - thr[0], cross[1] - thr[1]; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L
    start = (thr[0] - ux * 650, thr[1] - uy * 650)
    ax.add_patch(FancyArrowPatch(start, (cross[0] + ux * 40, cross[1] + uy * 40), arrowstyle="-|>", mutation_scale=28, lw=5, color=BLUE, zorder=8))
    hdg = math.degrees(math.atan2(uy, ux)); aircraft(ax, thr[0] - ux * 210, thr[1] - uy * 210, hdg, 90)
    ax.text(thr[0] + 560, thr[1] - 170, "AIR CANADA EXPRESS 8646 · JAZZ 646\nCRJ-900 · cleared to land RWY 4 at 23:35:07", fontsize=10.5,
            fontweight="bold", color="#ffffff", ha="center", va="center", zorder=10, bbox=dict(boxstyle="round,pad=0.45", fc=BLUE, ec="none"))
    # TRUCK 1: along D from the BB gathering point across runway 4
    cp = [xy(*c) for c in s["crossing_path"]]
    xs, ys = zip(*cp); ax.plot(xs, ys, color=ORANGE, lw=5, solid_capstyle="round", zorder=8)
    ax.add_patch(FancyArrowPatch(cp[-2], cp[-1], arrowstyle="-|>", mutation_scale=28, lw=5, color=ORANGE, zorder=8))
    hp = xy(*s["hold_point"]); tx, ty = cp[0]
    truck(ax, tx - 40, ty, 0, 55)
    ax.text(tx - 250, ty + 160, "TRUCK 1 · RESCUE 35\nARFF · cleared to cross RWY 4 at D, 23:37:04", fontsize=10.5, fontweight="bold",
            color=INK, ha="center", va="center", zorder=10, bbox=dict(boxstyle="round,pad=0.45", fc=ORANGE, ec="none"))
    ax.plot([hp[0]], [hp[1]], marker="|", ms=22, mew=4, color=RED, zorder=9); ax.text(hp[0] - 60, hp[1] + 62, "hold-short line", fontsize=9, color=RED, ha="center", fontweight="bold")
    # collision point
    ax.add_patch(Circle(cross, 110, fc=RED, ec="none", alpha=0.25, zorder=6)); ax.add_patch(Circle(cross, 14, fc=RED, ec="#ffffff", lw=1.5, zorder=11))
    ax.annotate("COLLISION ≈ 23:37:24\nrunway 4 × taxiway D", xy=cross, xytext=(cross[0] + 330, cross[1] + 420), fontsize=12, fontweight="bold", color="#ffffff",
                ha="center", va="center", zorder=12, bbox=dict(boxstyle="round,pad=0.5", fc=RED, ec="none"),
                arrowprops=dict(arrowstyle="-", color=RED, lw=2))
    # legend + title + north
    ax.text(-1210, 1110, "LaGuardia Airport (LGA)", fontsize=26, fontweight="bold", color=INK, va="top")
    ax.text(-1210, 985, "Ground view from OpenStreetMap — illustration, not for navigation", fontsize=11, color=MUTED, va="top")
    lx, ly = 900, 1040
    ax.add_patch(FancyBboxPatch((lx - 40, ly - 220), 820, 300, boxstyle="round,pad=12", fc="#ffffff", ec="#cfcac0", lw=1, zorder=12))
    ax.add_patch(FancyArrowPatch((lx, ly), (lx + 130, ly), arrowstyle="-|>", mutation_scale=22, lw=4, color=BLUE, zorder=13)); ax.text(lx + 160, ly, "Aircraft path (JAZZ 646, CRJ-900)", fontsize=10.5, va="center", zorder=13)
    ax.add_patch(FancyArrowPatch((lx, ly - 80), (lx + 130, ly - 80), arrowstyle="-|>", mutation_scale=22, lw=4, color=ORANGE, zorder=13)); ax.text(lx + 160, ly - 80, "Vehicle path (TRUCK 1, Rescue 35)", fontsize=10.5, va="center", zorder=13)
    ax.add_patch(Circle((lx + 65, ly - 160), 22, fc=RED, alpha=0.35, ec="none", zorder=13)); ax.text(lx + 160, ly - 160, "Collision point, NTSB estimate", fontsize=10.5, va="center", zorder=13)
    ax.annotate("", xy=(1790, 1110), xytext=(1790, 950), arrowprops=dict(arrowstyle="-|>", lw=2, color=INK)); ax.text(1790, 1125, "N", ha="center", fontsize=12, fontweight="bold", color=INK)
    ax.text(-1210, -1040, "Names, times and the collision point: NTSB preliminary report DCA26MA161 (investigation ongoing). Geometry © OpenStreetMap contributors.", fontsize=9, color=MUTED)
    ax.set_xlim(-1250, 1850); ax.set_ylim(-1070, 1144); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_color("#cfcac0")
    fig.subplots_adjust(0.01, 0.01, 0.99, 0.99); fig.savefig(out, facecolor=PAPER); print("wrote", out)


def inset_view(rw, tw, s, out):
    fig, ax = plt.subplots(figsize=(12.54, 12.54), dpi=100); fig.patch.set_facecolor(PAPER); ax.set_facecolor("#ece9e1")
    for ref, pts in tw:
        xs, ys = zip(*pts); ax.plot(xs, ys, color=TWY, lw=14, solid_capstyle="round", zorder=2, alpha=0.95)
    r4 = rw["04/22"]; runway(ax, r4, 95, label_ends=[(r4[-1], "04", 0, 0)], fs=14)
    cross = xy(*s["intersection"]); thr = r4[-1]
    dx, dy = cross[0] - thr[0], cross[1] - thr[1]; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L; hdg = math.degrees(math.atan2(uy, ux))
    ax.plot([cross[0] - ux * 900, cross[0]], [cross[1] - uy * 900, cross[1]], color=BLUE, lw=9, zorder=8, solid_capstyle="round")
    aircraft(ax, cross[0] - ux * 70, cross[1] - uy * 70, hdg, 48, z=10)
    cp = [xy(*c) for c in s["crossing_path"]]; xs, ys = zip(*cp); ax.plot(xs, ys, color=ORANGE, lw=9, zorder=8, solid_capstyle="round")
    # truck heading along the last crossing segment
    (ax0, ay0), (ax1, ay1) = cp[-3], cp[-1]; th = math.degrees(math.atan2(ay1 - ay0, ax1 - ax0))
    truck(ax, cross[0] + 2, cross[1] + 2, th, 20, z=11)
    hp = xy(*s["hold_point"]); ax.plot([hp[0]], [hp[1]], marker="|", ms=46, mew=6, color=RED, zorder=9)
    ax.text(hp[0], hp[1] + 42, "hold-short line", fontsize=14, color=RED, ha="center", fontweight="bold", zorder=12)
    ax.add_patch(Circle(cross, 60, fc=RED, ec=RED, lw=2, alpha=0.22, zorder=7, ls="--"))
    for i in range(10):  # burst
        a = math.radians(i * 36 + 18); ax.plot([cross[0] + 24 * math.cos(a), cross[0] + 44 * math.cos(a)], [cross[1] + 24 * math.sin(a), cross[1] + 44 * math.sin(a)], color=RED, lw=3, zorder=12)
    ax.text(cross[0] - 230, cross[1] - 60, "D", fontsize=15, fontweight="bold", color=INK, ha="center", va="center", zorder=8, bbox=dict(boxstyle="square,pad=0.3", fc=TWY, ec=INK))
    ax.annotate("", xy=(cross[0] + 40, cross[1] + 40), xytext=(cross[0] + 120, cross[1] + 225), arrowprops=dict(arrowstyle="-", lw=3, color=RED), zorder=13)
    ax.text(cross[0] + 120, cross[1] + 230, "⚠ Runway collision\n", fontsize=30, fontweight="bold", color="#ffffff", ha="center", va="bottom", zorder=14,
            bbox=dict(boxstyle="round,pad=0.55", fc=RED, ec="none"))
    ax.text(cross[0] + 120, cross[1] + 232, "JAZZ 646 on landing rollout and TRUCK 1 (Rescue 35)\ncollided at D ≈ 23:37:24 — NTSB preliminary", fontsize=13.5, color="#ffffff", ha="center", va="bottom", zorder=15)
    ax.set_xlim(cross[0] - 330, cross[1] + 330 + cross[0]); ax.set_ylim(cross[1] - 330, cross[1] + 330); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_color("#cfcac0")
    fig.subplots_adjust(0.005, 0.005, 0.995, 0.995); fig.savefig(out, facecolor=PAPER); print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out-main", default="docs/lga_asis_diagram.png"); ap.add_argument("--out-inset", default="docs/lga_asis_crossing.png")
    a = ap.parse_args(); rw, tw, s = load(); main_view(rw, tw, s, a.out_main); inset_view(rw, tw, s, a.out_inset)
