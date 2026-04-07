import plotly.graph_objects as go
import os
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────────
#  BLOOMBERG DARK THEME — shared palette
# ─────────────────────────────────────────────
BBG_BG        = "#0a0a0a"
BBG_PANEL     = "#111111"
BBG_GRID      = "#222222"
BBG_BORDER    = "#333333"
BBG_TEXT      = "#d4d4d4"
BBG_SUBTEXT   = "#888888"
BBG_ORANGE    = "#f0a500"
BBG_RED       = "#ff3b3b"
BBG_GREEN     = "#00d97e"
BBG_BLUE      = "#4da6ff"
BBG_GRAY_LINE = "#666666"
BBG_AMBER     = "#ffc233"

FONT_FAMILY   = "Courier New, monospace"


# ─────────────────────────────────────────────
#  SHARED HELPERS
# ─────────────────────────────────────────────
def _now_str() -> str:
    """Current timestamp formatted for chart footers."""
    return datetime.now().strftime("%Y-%m-%d %H:%M ET")


def _add_footer(fig: go.Figure, include_timestamp: bool = False) -> None:
    """
    Footer with optional 'As of' timestamp (amber, for live prices).
    Source attribution removed — add your own project name if desired.
    """
    if include_timestamp:
        fig.add_annotation(
            text=f"As of  {_now_str()}",
            xref="paper", yref="paper",
            x=1.0, y=-0.10,
            showarrow=False,
            font=dict(size=8, color=BBG_AMBER, family=FONT_FAMILY),
            xanchor="right", align="right",
        )


def _add_callout(
    fig: go.Figure,
    x,
    y: float,
    label: str,
    ax: int = 60,
    ay: int = -50,
    color: str = BBG_AMBER,
) -> None:
    """
    Elite analyst callout box with arrow pointing to an inflection point.
    ax/ay = pixel offset of the label box from the data point.
    """
    fig.add_annotation(
        x=x, y=y,
        text=f"<b>{label}</b>",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.2,
        arrowwidth=1.5,
        arrowcolor=color,
        ax=ax, ay=ay,
        font=dict(size=9, color=color, family=FONT_FAMILY),
        bgcolor="rgba(15,15,15,0.85)",
        bordercolor=color,
        borderwidth=1,
        borderpad=5,
        align="center",
    )


def _base_layout(title: str, x_title: str, y_title: str) -> dict:
    return dict(
        title=dict(
            text=title,
            font=dict(family=FONT_FAMILY, size=16, color=BBG_ORANGE),
            x=0.01, xanchor="left",
            pad=dict(b=12),
        ),
        paper_bgcolor=BBG_BG,
        plot_bgcolor=BBG_PANEL,
        font=dict(family=FONT_FAMILY, color=BBG_TEXT),
        xaxis=dict(
            title=dict(text=x_title, font=dict(size=11, color=BBG_SUBTEXT)),
            tickfont=dict(size=10, color=BBG_SUBTEXT),
            gridcolor=BBG_GRID,
            linecolor=BBG_BORDER,
            zerolinecolor=BBG_BORDER,
            showgrid=True,
        ),
        yaxis=dict(
            title=dict(text=y_title, font=dict(size=11, color=BBG_SUBTEXT)),
            tickfont=dict(size=10, color=BBG_SUBTEXT),
            gridcolor=BBG_GRID,
            linecolor=BBG_BORDER,
            zerolinecolor=BBG_BORDER,
            showgrid=True,
        ),
        legend=dict(
            bgcolor="rgba(20,20,20,0.85)",
            bordercolor=BBG_BORDER,
            borderwidth=1,
            font=dict(size=10, color=BBG_TEXT),
        ),
        margin=dict(l=60, r=40, t=70, b=75),   # extra bottom for footer
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1a1a1a",
            bordercolor=BBG_ORANGE,
            font=dict(family=FONT_FAMILY, size=11, color=BBG_TEXT),
        ),
    )


def _save(fig: go.Figure, filename: str) -> str:
    date_str = datetime.today().strftime("%Y-%m-%d")
    folder = f"charts/{date_str}"
    os.makedirs(folder, exist_ok=True)
    path = f"{folder}/{filename}"
    fig.write_image(path, scale=2)
    return path


# ─────────────────────────────────────────────
#  1.  INVENTORY vs SEASONAL BAND
# ─────────────────────────────────────────────
def plot_inventory_vs_seasonal(df):
    df = df.copy()
    df["year"] = df["period"].dt.year
    df["week"] = df["period"].dt.isocalendar().week.astype(int)

    current_year = int(df["year"].max())
    hist = df[(df["year"] < current_year) & (df["year"] >= current_year - 5)]

    band = (
        hist.groupby("week")["value_million_bbl"]
        .agg(["min", "max", "mean"])
        .reset_index()
    )
    current = df[df["year"] == current_year].copy()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=band["week"], y=band["max"],
        mode="lines", line=dict(width=0),
        showlegend=False, hoverinfo="skip", name="5Y Max",
    ))
    fig.add_trace(go.Scatter(
        x=band["week"], y=band["min"],
        mode="lines", line=dict(width=0),
        fill="tonexty", fillcolor="rgba(90,90,90,0.25)",
        name="5-Year Range (Min–Max)", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=band["week"], y=band["mean"],
        mode="lines",
        line=dict(color=BBG_GRAY_LINE, width=1.5, dash="dash"),
        name="5-Year Average",
    ))
    fig.add_trace(go.Scatter(
        x=current["week"], y=current["value_million_bbl"],
        mode="lines",
        line=dict(color=BBG_RED, width=3),
        name=f"{current_year} Inventory",
    ))

    # Auto-callout: latest week deviation vs 5Y average
    latest   = current.iloc[-1]
    band_row = band[band["week"] == latest["week"]]
    if not band_row.empty:
        avg_val = float(band_row["mean"].values[0])
        diff    = latest["value_million_bbl"] - avg_val
        callout_label = (
            f"{'Above' if diff > 0 else 'Below'} 5Y Avg<br>"
            f"{abs(diff):.1f} mbbl {'surplus' if diff > 0 else 'deficit'}"
        )
        _add_callout(
            fig,
            x=int(latest["week"]),
            y=float(latest["value_million_bbl"]),
            label=callout_label,
            ax=70, ay=-45,
        )

    layout = _base_layout(
        title=f"US CRUDE OIL INVENTORY  ·  {current_year} vs 5-Year Seasonality",
        x_title="Week of Year",
        y_title="Million Barrels (mbbl)",
    )
    fig.update_layout(**layout)
    _add_footer(fig, include_timestamp=False)   # EIA = weekly data, no intraday ts

    return _save(fig, "inventory_vs_5yr_band.png")


# ─────────────────────────────────────────────
#  2.  FUTURES CURVE SNAPSHOT
#      6-month strip for a realistic curve shape
#      ★ timestamp ON — prices go stale fast
# ─────────────────────────────────────────────
def plot_futures_curve_snapshot(cl1_price: float, cl2_price: float):
    """
    Renders a 6-contract futures strip (M1–M6).
    M1 = cl1_price, M2 = cl2_price.
    M3–M6 are interpolated with a realistic decay that flattens toward
    long-dated fair value — mimicking how backwardation/contango
    typically attenuates further out the curve.
    """
    spread = cl1_price - cl2_price
    state  = "BACKWARDATION" if spread > 0 else "CONTANGO"
    accent = BBG_RED if spread > 0 else BBG_GREEN

    # Build 6-contract strip: decay attenuates with each step out the curve
    # Reflects real term-structure: steepest near prompt, flattens far-end
    step = cl2_price - cl1_price          # signed M1→M2 move
    strip_prices = [cl1_price, cl2_price]
    prev = cl2_price
    for i in range(1, 5):                 # produces M3, M4, M5, M6
        decay = step * (0.55 ** i)
        prev  = round(prev + decay, 2)
        strip_prices.append(prev)

    # Sanity check — should always be 6 at this point
    assert len(strip_prices) == 6, f"Expected 6 strip prices, got {len(strip_prices)}"

    from datetime import date
    from dateutil.relativedelta import relativedelta
    base = date.today().replace(day=1)
    month_labels = [
        (base + relativedelta(months=i)).strftime("%b '%y")
        for i in range(6)
    ]

    fig = go.Figure()

    # Shaded area under curve
    fig.add_trace(go.Scatter(
        x=month_labels, y=strip_prices,
        fill="tozeroy", fillcolor="rgba(77,166,255,0.07)",
        mode="none", showlegend=False, hoverinfo="skip",
    ))

    # The curve line
    fig.add_trace(go.Scatter(
        x=month_labels, y=strip_prices,
        mode="lines+markers",
        line=dict(color=BBG_BLUE, width=3),
        marker=dict(size=10, color=BBG_BLUE, line=dict(color=BBG_ORANGE, width=1.5)),
        name="WTI Futures Strip",
        hovertemplate="<b>%{x}</b><br>$%{y:.2f}/bbl<extra></extra>",
    ))

    # Price labels — only on M1 and M6 to keep it clean
    for idx in [0, 5]:
        fig.add_annotation(
            x=month_labels[idx], y=strip_prices[idx],
            text=f"<b>${strip_prices[idx]:.2f}</b>",
            showarrow=False,
            yshift=16,
            font=dict(size=13, color=BBG_AMBER, family=FONT_FAMILY),
        )

    layout = _base_layout(
        title=f"WTI FUTURES STRIP  ·  6-Month Curve  ·  {state}",
        x_title="Contract Month",
        y_title="Price per Barrel (USD)",
    )
    layout["yaxis"]["range"] = [min(strip_prices) - 3, max(strip_prices) + 5]
    layout["title"]["font"]["color"] = accent
    fig.update_layout(**layout)

    # Market structure badge
    fig.add_annotation(
        text=f"● {state}",
        xref="paper", yref="paper", x=0.99, y=0.97,
        showarrow=False,
        font=dict(size=11, color=accent, family=FONT_FAMILY),
        xanchor="right",
        bgcolor="rgba(20,20,20,0.7)",
        bordercolor=accent, borderwidth=1, borderpad=6,
    )

    # Callout on M2 — prompt roll cost/yield (most actionable data point)
    spread_label = (
        f"Prompt Roll: {'−' if spread < 0 else '+'}${abs(spread):.2f}/bbl<br>"
        f"{'Carry cost (Contango)' if spread < 0 else 'Roll yield (Backwardation)'}"
    )
    _add_callout(
        fig,
        x=month_labels[1], y=strip_prices[1],
        label=spread_label,
        ax=75, ay=-55,
        color=accent,
    )

    # ★ Timestamp — futures prices are time-sensitive
    _add_footer(fig, include_timestamp=True)

    return _save(fig, "futures_curve.png")


# ─────────────────────────────────────────────
#  3.  SPREAD TIME SERIES
#      auto-detects peak inflection for callout
# ─────────────────────────────────────────────
def plot_spread_timeseries(curve_df, inflection_date=None, inflection_label=None):
    """
    curve_df         : DataFrame with 'spread' column, DatetimeIndex
    inflection_date  : pd.Timestamp for callout (auto-detects abs max if omitted)
    inflection_label : override label text (e.g. "Supply Crunch Peak – Apr 5")
    """
    spread     = curve_df["spread"]
    pos_spread = spread.where(spread >= 0)
    neg_spread = spread.where(spread <= 0)

    fig = go.Figure()

    fig.add_hline(y=0, line=dict(color=BBG_BORDER, width=1, dash="dot"))

    fig.add_trace(go.Scatter(
        x=curve_df.index, y=pos_spread,
        mode="lines", line=dict(width=0),
        fill="tozeroy", fillcolor="rgba(0,217,126,0.15)",
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=curve_df.index, y=neg_spread,
        mode="lines", line=dict(width=0),
        fill="tozeroy", fillcolor="rgba(255,59,59,0.15)",
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=curve_df.index, y=spread,
        mode="lines",
        line=dict(color=BBG_GREEN, width=2),
        name="CL1–CL2 Spread",
        hovertemplate="<b>%{x}</b><br>Spread: $%{y:.2f}<extra></extra>",
    ))

    layout = _base_layout(
        title="WTI PROMPT SPREAD  ·  CL1 – CL2",
        x_title="Date",
        y_title="Spread (USD)",
    )
    fig.update_layout(**layout)

    fig.add_annotation(
        text="BACKWARDATION", xref="paper", yref="paper",
        x=0.01, y=0.97, showarrow=False,
        font=dict(size=9, color=BBG_GREEN, family=FONT_FAMILY),
        xanchor="left",
    )
    fig.add_annotation(
        text="CONTANGO", xref="paper", yref="paper",
        x=0.01, y=0.03, showarrow=False,
        font=dict(size=9, color=BBG_RED, family=FONT_FAMILY),
        xanchor="left",
    )

    # ── "So What?" callout ──────────────────────────────────────────
    if inflection_date is None:
        inflection_date = spread.abs().idxmax()
    peak_val = float(spread.loc[inflection_date])
    label    = inflection_label or (
        "Supply Crunch Peak" if peak_val > 0 else "Contango Extreme"
    )
    _add_callout(
        fig,
        x=inflection_date, y=peak_val,
        label=label,
        ax=-70, ay=-50,
        color=BBG_AMBER,
    )

    _add_footer(fig, include_timestamp=False)

    return _save(fig, "spread_timeseries.png")


# ─────────────────────────────────────────────
#  4.  3-2-1 CRACK SPREAD
# ─────────────────────────────────────────────
def plot_crack_spread(df):
    crack   = df["crack_spread"]
    rolling = crack.rolling(30, min_periods=1).mean()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index, y=crack,
        mode="none", fill="tozeroy",
        fillcolor="rgba(240,165,0,0.10)",
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=crack,
        mode="lines",
        line=dict(color=BBG_ORANGE, width=1.5),
        name="3-2-1 Crack Spread",
        hovertemplate="<b>%{x}</b><br>Crack: $%{y:.2f}/bbl<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=rolling,
        mode="lines",
        line=dict(color="#ffffff", width=2, dash="dot"),
        name="30-Day Average",
        hovertemplate="<b>%{x}</b><br>30d Avg: $%{y:.2f}/bbl<extra></extra>",
    ))

    # Auto-callout: peak refinery margin
    peak_date = crack.idxmax()
    peak_val  = float(crack.loc[peak_date])
    _add_callout(
        fig,
        x=peak_date, y=peak_val,
        label=f"Peak Margin<br>${peak_val:.2f}/bbl",
        ax=60, ay=-50,
        color=BBG_ORANGE,
    )

    layout = _base_layout(
        title="3-2-1 CRACK SPREAD  ·  Refinery Margin Indicator",
        x_title="Date",
        y_title="USD / Barrel",
    )
    fig.update_layout(**layout)
    _add_footer(fig, include_timestamp=False)

    return _save(fig, "crack_spread.png")