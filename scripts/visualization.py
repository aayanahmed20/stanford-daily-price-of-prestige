# ==============================================================================
# The Price of Prestige
# Step 5 - publication-quality figures
# ==============================================================================

"""Render every figure used by the article.

House style: Okabe-Ito color-blind-safe palette, DejaVu Sans typography,
300 dpi output, gridlines behind data, and a consistent source note under
each chart (see ``scripts.helpers.save_figure``).

Figures produced
----------------
* ``fig_sticker_cost.png``   -- sticker price, Stanford vs peers
* ``fig_aid_curve.png``      -- net price by family income (the "aid curve")
* ``fig_pell_share.png``     -- share of Pell recipients
* ``fig_debt_by_income.png`` -- median debt by family income group
* ``fig_earnings.png``       -- earnings percentiles 10 years after entry
* ``fig_roi_scatter.png``    -- net price vs median earnings (with OLS line)
* ``fig_cost_trend.png``     -- inflation-adjusted tuition, 2000-2025
* ``interactive_aid_curve.html`` -- hoverable aid curve (Plotly)
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

from scripts import config
from scripts.helpers import (
    PALETTE,
    apply_style,
    ensure_dir,
    get_logger,
    save_figure,
)

log = get_logger("visualization")

SOURCE_NOTE = (
    "Source: U.S. Department of Education, College Scorecard "
    "(Most Recent Cohorts, June 2026). Net prices and debts are averages/medians "
    "reported by institutions; see methodology."
)


# ---------------------------------------------------------------------------
# Small plotting helpers
# ---------------------------------------------------------------------------


def _fig(figsize: tuple[float, float] = (10, 6.5)):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=figsize)
    return fig, ax


def _label_axis(ax, title, xlabel=None, ylabel=None):
    ax.set_title(title, loc="left", pad=14)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(PALETTE["faint"])
    ax.spines["bottom"].set_color(PALETTE["faint"])


def _money_ticks(ax, axis="y"):
    from matplotlib.ticker import FuncFormatter

    fmt = FuncFormatter(lambda x, _: f"${x:,.0f}")
    if axis == "y":
        ax.yaxis.set_major_formatter(fmt)
    else:
        ax.xaxis.set_major_formatter(fmt)


def _pct_ticks(ax, axis="y"):
    from matplotlib.ticker import FuncFormatter

    fmt = FuncFormatter(lambda x, _: f"{x * 100:.0f}%")
    if axis == "y":
        ax.yaxis.set_major_formatter(fmt)
    else:
        ax.xaxis.set_major_formatter(fmt)


# ---------------------------------------------------------------------------
# Figure 1 - sticker price
# ---------------------------------------------------------------------------


def fig_sticker_cost(peers: pd.DataFrame, national_median_cost: float) -> str:
    from matplotlib.lines import Line2D

    d = peers.dropna(subset=["COSTT4_A"]).sort_values("COSTT4_A").copy()
    fig, ax = _fig()
    colors = np.where(d["is_stanford"], PALETTE["stanford"], PALETTE["peer"])
    ax.hlines(range(len(d)), 0, d["COSTT4_A"], color=colors, linewidth=4, alpha=0.85)
    ax.scatter(d["COSTT4_A"], range(len(d)), color=colors, s=80, zorder=3)
    ax.scatter(
        d["COSTT4_A"],
        range(len(d)),
        facecolors="white",
        edgecolors=colors,
        s=80,
        zorder=4,
        linewidths=1.2,
    )
    for i, v in enumerate(d["COSTT4_A"]):
        ax.text(v + 900, i, f"${v:,.0f}", va="center", fontsize=9, color=PALETTE["ink"])
    ax.axvline(national_median_cost, color=PALETTE["national"], linestyle="--", linewidth=1.2)
    ax.text(
        national_median_cost + 900,
        len(d) - 0.7,
        f"U.S. four-year non-profit median: ${national_median_cost:,.0f}",
        fontsize=9,
        color=PALETTE["slate"],
    )
    ax.set_yticks(range(len(d)))
    ax.set_yticklabels([("Stanford University" if s else s) for s in d["INSTNM"]], fontsize=10)
    ax.set_xlim(0, d["COSTT4_A"].max() * 1.18)
    _money_ticks(ax)
    _label_axis(
        ax,
        "The sticker price of an elite education",
        "Total cost of attendance, 2024-25 (tuition + fees + room/board)",
        None,
    )
    legend = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=PALETTE["stanford"],
            markersize=9,
            label="Stanford University",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=PALETTE["peer"],
            markersize=9,
            label="Peer institution",
        ),
    ]
    ax.legend(handles=legend, loc="lower right")
    return str(save_figure(fig, "fig_sticker_cost", SOURCE_NOTE))


# ---------------------------------------------------------------------------
# Figure 2 - the aid curve
# ---------------------------------------------------------------------------


def fig_aid_curve(aid: pd.DataFrame) -> str:

    buckets = list(config.INCOME_BUCKETS.values())
    x = np.arange(len(buckets))
    peer = aid[~aid["is_stanford"]]
    stan = aid[aid["is_stanford"]].set_index("income_bucket")["net_price"]

    q25 = peer.groupby("income_bucket")["net_price"].quantile(0.25)
    q75 = peer.groupby("income_bucket")["net_price"].quantile(0.75)
    med = peer.groupby("income_bucket")["net_price"].median()

    fig, ax = _fig()
    ax.fill_between(
        x,
        q25.reindex(buckets).values,
        q75.reindex(buckets).values,
        color=PALETTE["peer_fill"],
        alpha=0.5,
        linewidth=0,
        label="Middle 50% of peer schools",
    )
    ax.plot(
        x,
        med.reindex(buckets).values,
        color=PALETTE["peer"],
        linewidth=2.2,
        marker="o",
        markersize=6,
        label="Peer median",
    )
    stan_vals = [stan.get(b) for b in buckets]
    ax.plot(
        x,
        stan_vals,
        color=PALETTE["stanford"],
        linewidth=3.2,
        marker="o",
        markersize=8,
        label="Stanford University",
    )
    for xi, v in zip(x, stan_vals, strict=False):
        if v is not None and not np.isnan(v):
            ax.annotate(
                f"${v:,.0f}",
                (xi, v),
                textcoords="offset points",
                xytext=(0, 9),
                ha="center",
                fontsize=9,
                color=PALETTE["stanford"],
            )
    ax.axhline(0, color=PALETTE["faint"], linewidth=1, linestyle=":")
    ax.set_xticks(x)
    ax.set_xticklabels([b.replace("\u2013", "-") for b in buckets], fontsize=9)
    ax.set_ylim(-6000, 60000)
    _money_ticks(ax)
    _label_axis(
        ax,
        "What Stanford families actually pay, by income",
        "Family income (dependent students)",
        "Average net price per year, 2024-25",
    )
    ax.legend(loc="upper left")
    ax.text(
        0.0,
        -0.32,
        "Negative values mean grants and scholarships exceeded the full cost of attendance.",
        transform=ax.transAxes,
        fontsize=8.5,
        color=PALETTE["slate"],
    )
    return str(save_figure(fig, "fig_aid_curve", SOURCE_NOTE))


# ---------------------------------------------------------------------------
# Figure 3 - Pell share
# ---------------------------------------------------------------------------


def fig_pell_share(peers: pd.DataFrame, national_median_pell: float) -> str:
    from matplotlib.lines import Line2D

    d = peers.dropna(subset=["PCTPELL"]).sort_values("PCTPELL").copy()
    fig, ax = _fig()
    colors = np.where(d["is_stanford"], PALETTE["stanford"], PALETTE["peer"])
    ax.barh(range(len(d)), d["PCTPELL"], color=colors, alpha=0.9, height=0.62)
    for i, v in enumerate(d["PCTPELL"]):
        ax.text(v + 0.004, i, f"{v:.1%}", va="center", fontsize=9, color=PALETTE["ink"])
    ax.axvline(national_median_pell, color=PALETTE["national"], linestyle="--")
    ax.text(
        national_median_pell + 0.004,
        len(d) - 0.8,
        f"National median: {national_median_pell:.1%}",
        fontsize=9,
        color=PALETTE["slate"],
    )
    ax.set_yticks(range(len(d)))
    ax.set_yticklabels([("Stanford University" if s else s) for s in d["INSTNM"]], fontsize=10)
    ax.set_xlim(0, 0.32)
    _pct_ticks(ax)
    _label_axis(
        ax,
        "How many students receive Pell Grants?",
        "Share of undergraduate students with Pell Grants",
        None,
    )
    legend = [
        Line2D([0], [0], color=PALETTE["stanford"], lw=5, label="Stanford University"),
        Line2D([0], [0], color=PALETTE["peer"], lw=5, label="Peer"),
    ]
    ax.legend(handles=legend, loc="lower right")
    return str(save_figure(fig, "fig_pell_share", SOURCE_NOTE))


# ---------------------------------------------------------------------------
# Figure 4 - debt by income
# ---------------------------------------------------------------------------


def fig_debt_by_income(peers: pd.DataFrame, national_median_debt: float) -> str:
    from matplotlib.lines import Line2D

    d = peers.dropna(subset=["GRAD_DEBT_MDN"]).sort_values("GRAD_DEBT_MDN").copy()
    metrics = [
        ("GRAD_DEBT_MDN", "All graduates"),
        ("LO_INC_DEBT_MDN", "Graduates from low-income families"),
        ("FIRSTGEN_DEBT_MDN", "First-generation graduates"),
        ("HI_INC_DEBT_MDN", "Graduates from high-income families"),
    ]
    fig, ax = _fig()
    y = np.arange(len(d))
    for i, (col, _label) in enumerate(metrics):
        off = (i - 1.5) * 0.16
        vals = d[col]
        colors = np.where(d["is_stanford"], PALETTE["stanford"], PALETTE["peer"])
        ax.barh(y + off, vals.fillna(0), height=0.11, color=colors, alpha=0.85)
    stan = d[d["is_stanford"]].iloc[0]
    for i, (col, _label) in enumerate(metrics):
        if not np.isnan(stan[col]):
            off = (i - 1.5) * 0.16
            ax.text(
                stan[col] + 300,
                d.index.tolist().index(stan.name) + off,
                f"${stan[col]:,.0f}",
                va="center",
                fontsize=8,
                color=PALETTE["stanford"],
            )
    ax.axvline(national_median_debt, color=PALETTE["national"], linestyle="--")
    ax.text(
        national_median_debt + 300,
        len(d) - 0.8,
        f"National median: ${national_median_debt:,.0f}",
        fontsize=9,
        color=PALETTE["slate"],
    )
    ax.set_yticks(y)
    ax.set_yticklabels([("Stanford University" if s else s) for s in d["INSTNM"]], fontsize=10)
    xmax = max(d[["GRAD_DEBT_MDN", "LO_INC_DEBT_MDN", "HI_INC_DEBT_MDN"]].max().max() * 1.15, 10000)
    ax.set_xlim(0, xmax)
    _money_ticks(ax)
    _label_axis(
        ax,
        "The debt that graduates carry",
        "Median cumulative federal debt, by group (most recent cohort)",
        None,
    )
    legend = [
        Line2D([0], [0], color=PALETTE["stanford"], lw=3, label="Stanford"),
        Line2D([0], [0], color=PALETTE["peer"], lw=3, label="Peer"),
        Line2D(
            [0],
            [0],
            color=PALETTE["slate"],
            lw=0,
            marker="|",
            markersize=12,
            label="National median",
        ),
    ]
    ax.legend(handles=legend, loc="lower right", fontsize=9)
    return str(save_figure(fig, "fig_debt_by_income", SOURCE_NOTE))


# ---------------------------------------------------------------------------
# Figure 5 - earnings percentiles
# ---------------------------------------------------------------------------


def fig_earnings(peers: pd.DataFrame, national_median_earn: float) -> str:

    d = peers.dropna(subset=["MD_EARN_WNE_P10"]).sort_values("MD_EARN_WNE_P10").copy()
    fig, ax = _fig()
    y = np.arange(len(d))
    p25 = d["PCT25_EARN_WNE_P10"]
    p75 = d["PCT75_EARN_WNE_P10"]
    med = d["MD_EARN_WNE_P10"]
    p90 = d["PCT90_EARN_WNE_P10"]
    colors = np.where(d["is_stanford"], PALETTE["stanford"], PALETTE["peer"])

    ax.hlines(y, p25, p75, color=colors, linewidth=5, alpha=0.75, label="25th-75th percentile")
    ax.scatter(med, y, color=colors, s=70, zorder=4, label="Median")
    ax.scatter(p90, y, marker="D", color=colors, s=45, zorder=4, label="90th percentile")
    for i, sname in enumerate(d["INSTNM"]):
        if sname == config.FOCAL_SCHOOL:
            ax.annotate(
                f"median ${med.iloc[i]:,.0f}",
                (med.iloc[i], i),
                textcoords="offset points",
                xytext=(-6, 8),
                ha="right",
                fontsize=9,
                color=PALETTE["stanford"],
            )
    ax.axvline(national_median_earn, color=PALETTE["national"], linestyle="--")
    ax.text(
        national_median_earn + 1200,
        len(d) - 0.7,
        f"National median: ${national_median_earn:,.0f}",
        fontsize=9,
        color=PALETTE["slate"],
    )
    ax.set_yticks(y)
    ax.set_yticklabels([("Stanford University" if s else s) for s in d["INSTNM"]], fontsize=10)
    ax.set_xlim(0, d["PCT90_EARN_WNE_P10"].max() * 1.1)
    _money_ticks(ax)
    _label_axis(
        ax,
        "What graduates earn a decade after entering",
        "Annual earnings (median, interquartile range, 90th pctile)",
        None,
    )
    ax.legend(loc="lower right", fontsize=9)
    return str(save_figure(fig, "fig_earnings", SOURCE_NOTE))


# ---------------------------------------------------------------------------
# Figure 6 - ROI scatter
# ---------------------------------------------------------------------------


def fig_roi_scatter(roi: pd.DataFrame, peers: pd.DataFrame) -> str:
    import statsmodels.api as sm

    d = roi.dropna(subset=["NPT4_PRIV", "MD_EARN_WNE_P10", "COUNT_WNE_P10"])
    d = d[d["COUNT_WNE_P10"] >= config.MIN_COUNT_WNE_P10].copy()

    fig, ax = _fig(figsize=(10.5, 6.5))
    ax.scatter(
        d["NPT4_PRIV"],
        d["MD_EARN_WNE_P10"],
        s=18,
        alpha=0.45,
        color=PALETTE["faint"],
        linewidths=0,
        label="Other four-year\nnon-profits",
    )

    peer_ids = set(peers["UNITID"])
    peers_in = d[d["UNITID"].isin(peer_ids)]
    ax.scatter(
        peers_in["NPT4_PRIV"],
        peers_in["MD_EARN_WNE_P10"],
        s=46,
        color=PALETTE["peer"],
        edgecolors="white",
        linewidths=0.7,
        zorder=4,
        label="Peer institution",
    )

    stan = d[d["INSTNM"] == config.FOCAL_SCHOOL]
    ax.scatter(
        stan["NPT4_PRIV"],
        stan["MD_EARN_WNE_P10"],
        marker="*",
        s=420,
        color=PALETTE["stanford"],
        edgecolors="white",
        linewidths=1.0,
        zorder=6,
        label="Stanford University",
    )

    # OLS fit line on the full sample.
    fit = sm.OLS(d["MD_EARN_WNE_P10"], sm.add_constant(d["NPT4_PRIV"])).fit()
    xs = np.linspace(0, d["NPT4_PRIV"].quantile(0.98), 100)
    ax.plot(
        xs,
        fit.params.iloc[0] + fit.params.iloc[1] * xs,
        color=PALETTE["ink"],
        linewidth=1.8,
        linestyle="--",
        alpha=0.8,
        label="Fitted line (all schools)",
    )

    # Annotate Stanford and a few peers.
    labels = [
        config.FOCAL_SCHOOL,
        "Massachusetts Institute of Technology",
        "Princeton University",
        "Harvard University",
        "Rice University",
        "Northwestern University",
    ]
    for school in labels:
        hit = d[d["INSTNM"] == school]
        if len(hit):
            ax.annotate(
                school.replace("University", "U."),
                (hit["NPT4_PRIV"].iloc[0], hit["MD_EARN_WNE_P10"].iloc[0]),
                textcoords="offset points",
                xytext=(8, 5),
                fontsize=8.5,
                color=PALETTE["ink"],
            )

    ax.set_xlim(-2000, 50000)
    ax.set_ylim(0, 175000)
    _money_ticks(ax, "x")
    _money_ticks(ax, "y")
    _label_axis(
        ax,
        "The return on a degree: what students pay vs. what they earn",
        "Average net price per year (2024-25)",
        "Median earnings 10 years after entry",
    )
    ax.legend(loc="upper left", fontsize=9)
    return str(save_figure(fig, "fig_roi_scatter", SOURCE_NOTE))


# ---------------------------------------------------------------------------
# Figure 7 - cost trend
# ---------------------------------------------------------------------------


def fig_cost_trend(trend: pd.DataFrame) -> str:

    t = trend.sort_values("year_int")
    fig, ax = _fig()
    ax.plot(
        t["year_int"],
        t["real_stanford_tuition"],
        color=PALETTE["stanford"],
        linewidth=3.2,
        marker="o",
        markersize=4,
        label="Stanford tuition & fees",
    )
    ax.plot(
        t["year_int"],
        t["real_peer_median_tuition"],
        color=PALETTE["peer"],
        linewidth=2.2,
        label="Peer median",
    )
    ax.plot(
        t["year_int"],
        t["real_national_median_tuition"],
        color=PALETTE["national"],
        linewidth=2.0,
        linestyle="--",
        label="National median (four-year non-profit)",
    )

    start = t["real_stanford_tuition"].iloc[0]
    end = t["real_stanford_tuition"].iloc[-1]
    pct = (end / start - 1) * 100
    ax.annotate(
        f"Real (2025$) tuition at Stanford\n{start:,.0f} \u2192 {end:,.0f} ({pct:+.0f}%)",
        xy=(t["year_int"].iloc[-1], end),
        xytext=(-40, 14),
        textcoords="offset points",
        fontsize=9.5,
        color=PALETTE["stanford"],
        ha="right",
        va="bottom",
        arrowprops=dict(arrowstyle="-", color=PALETTE["stanford"], lw=0.8),
    )
    _money_ticks(ax)
    _label_axis(
        ax,
        "Stanford's tuition has kept climbing even after inflation",
        "Academic year",
        "Tuition & required fees (2025 dollars, CPI-adjusted)",
    )
    ax.legend(loc="upper left", fontsize=9)
    return str(save_figure(fig, "fig_cost_trend", SOURCE_NOTE))


# ---------------------------------------------------------------------------
# Interactive figure (Plotly)
# ---------------------------------------------------------------------------


def interactive_aid_curve(aid: pd.DataFrame) -> str:
    import plotly.graph_objects as go

    buckets = list(config.INCOME_BUCKETS.values())
    fig = go.Figure()
    for school, grp in aid.groupby("INSTNM"):
        vals = grp.set_index("income_bucket")["net_price"].reindex(buckets)
        is_stan = school == config.FOCAL_SCHOOL
        fig.add_trace(
            go.Scatter(
                x=buckets,
                y=vals,
                mode="lines+markers",
                name=school,
                line=dict(
                    color="#8C1515" if is_stan else "#3E78B2",
                    width=4 if is_stan else 1.6,
                ),
                opacity=1.0 if is_stan else 0.85,
                hovertemplate="%{x}<br>Net price: $%{y:,.0f}<extra>" + school + "</extra>",
            )
        )
    fig.update_layout(
        title="Average net price by family income \u2014 Stanford and its peers",
        xaxis_title="Family income (dependent students)",
        yaxis_title="Average net price per year (2024-25)",
        hovermode="closest",
        template="plotly_white",
        height=600,
        legend=dict(font=dict(size=10)),
        margin=dict(l=60, r=20, t=60, b=60),
    )
    out = config.FIGURES_DIR / "interactive" / "interactive_aid_curve.html"
    ensure_dir(out.parent)
    fig.write_html(out, include_plotlyjs="cdn", full_html=True)
    log.info("saved interactive figure: %s", out)
    return str(out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-interactive",
        action="store_true",
        help="skip the Plotly interactive figure (no JS dependency)",
    )
    args = parser.parse_args(argv)

    try:
        apply_style()
        peers = pd.read_csv(config.PROCESSED_PEERS)
        aid = pd.read_csv(config.PROCESSED_DIR / "aid_curve.csv")
        trend = pd.read_csv(config.PROCESSED_TREND)
        roi = pd.read_csv(config.PROCESSED_ROI)
        universe = pd.read_csv(config.PROCESSED_SCORECARD)

        national_median_cost = float(universe["COSTT4_A"].median())
        national_median_pell = float(universe["PCTPELL"].median())
        national_median_debt = float(universe["GRAD_DEBT_MDN"].median())
        national_median_earn = float(universe["MD_EARN_WNE_P10"].median())

        paths = {
            "fig_sticker_cost": fig_sticker_cost(peers, national_median_cost),
            "fig_aid_curve": fig_aid_curve(aid),
            "fig_pell_share": fig_pell_share(peers, national_median_pell),
            "fig_debt_by_income": fig_debt_by_income(peers, national_median_debt),
            "fig_earnings": fig_earnings(peers, national_median_earn),
            "fig_roi_scatter": fig_roi_scatter(roi, peers),
            "fig_cost_trend": fig_cost_trend(trend),
        }
        if not args.skip_interactive:
            paths["interactive_aid_curve"] = interactive_aid_curve(aid)

        log.info("figures complete: %d rendered", len(paths))
        return 0
    except Exception as exc:  # noqa: BLE001
        log.error("visualization step failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
