import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
    Analyst callout box with arrow pointing to an inflection point.
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


def _save(fig: go.Figure, filename: str, report_date=None) -> str:
    if report_date is None:
        report_date = datetime.today()

    date_str = pd.to_datetime(report_date).strftime("%Y-%m-%d")
    folder = f"charts/{date_str}"
    os.makedirs(folder, exist_ok=True)

    path = f"{folder}/{filename}"
    fig.write_image(path, scale=2)

    return path


# ─────────────────────────────────────────────
#  1.  INVENTORY vs SEASONAL BAND
# ─────────────────────────────────────────────
def plot_inventory_vs_seasonal(df, report_date=None):
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

    return _save(fig, "inventory_vs_5yr_band.png", report_date)


# ─────────────────────────────────────────────
#  2.  FUTURES CURVE SNAPSHOT
#      6-month strip for a realistic curve shape
#      ★ timestamp ON — prices go stale fast
# ─────────────────────────────────────────────
def plot_futures_curve_snapshot(cl1_price: float, cl2_price: float, report_date=None):
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

    return _save(fig, "futures_curve.png", report_date)


# ─────────────────────────────────────────────
#  3.  SPREAD TIME SERIES
#      auto-detects peak inflection for callout
# ─────────────────────────────────────────────
def plot_spread_timeseries(curve_df, inflection_date=None, inflection_label=None,report_date=None):
    """
    curve_df         : DataFrame with 'spread' column, DatetimeIndex
    inflection_date  : pd.Timestamp for callout (auto-detects abs max if omitted)
    inflection_label : override label text (e.g. "Supply Crunch Peak – Apr 5")
    """
    spread     = curve_df["spread"]
    # spread = CL1 - CL2  →  positive = backwardation (tight), negative = contango (oversupplied)
    pos_spread = spread.where(spread >= 0)   # backwardation zone
    neg_spread = spread.where(spread <= 0)   # contango zone

    fig = go.Figure()

    fig.add_hline(y=0, line=dict(color=BBG_BORDER, width=1, dash="dot"))

    # BACKWARDATION (positive spread → green)
    fig.add_trace(go.Scatter(
        x=curve_df.index, y=pos_spread,
        mode="lines", line=dict(width=0),
        fill="tozeroy", fillcolor="rgba(0,217,126,0.15)",
        showlegend=False,
    ))

    # CONTANGO (negative spread → red)
    fig.add_trace(go.Scatter(
        x=curve_df.index, y=neg_spread,
        mode="lines", line=dict(width=0),
        fill="tozeroy", fillcolor="rgba(255,59,59,0.15)",
        showlegend=False,
    ))

    # MAIN LINE
    fig.add_trace(go.Scatter(
        x=curve_df.index, y=spread,
        mode="lines",
        line=dict(color=BBG_GREEN, width=2),
        name="CL1–CL2 Spread",
    ))

    fig.update_layout(**_base_layout(
        title="WTI PROMPT SPREAD  ·  CL1 – CL2",
        x_title="Date",
        y_title="Spread (USD)",
    ))

    # Labels — positive spread = backwardation (green), negative = contango (red)
    if spread.max() > 0:
        fig.add_annotation(
            xref="paper", yref="y",
            x=0.01, y=spread.max() * 0.8,
            text="BACKWARDATION",
            showarrow=False,
            font=dict(color=BBG_GREEN, size=11),
        )

    if spread.min() < 0:
        fig.add_annotation(
            xref="paper", yref="y",
            x=0.01, y=spread.min() * 0.8,
            text="CONTANGO",
            showarrow=False,
            font=dict(color=BBG_RED, size=11),
        )

    # Inflection
    if inflection_date is None:
        inflection_date = spread.abs().idxmax()

    peak_val = float(spread.loc[inflection_date])

    label = inflection_label or (
        "Supply Crunch Peak" if peak_val > 0 else "Contango Extreme"
    )

    _add_callout(
        fig,
        x=inflection_date,
        y=peak_val,
        label=label,
        ax=-70,
        ay=-50,
        color=BBG_AMBER,
    )

    _add_footer(fig, include_timestamp=False)

    return _save(fig, "spread_timeseries.png", report_date)


# ─────────────────────────────────────────────
#  4.  3-2-1 CRACK SPREAD
# ─────────────────────────────────────────────
def plot_crack_spread(df, report_date=None):
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

    return _save(fig, "crack_spread.png", report_date)

# ─────────────────────────────────────────────
#  5.  PnL CURVE  +  DRAWDOWN (2-panel)
# ─────────────────────────────────────────────
def plot_pnl_drawdown(df: pd.DataFrame, win_rate: float, sharpe: float | None, max_dd: float, report_date=None) -> str:
    """
    df       : output of compute_cumulative_returns() — must have 'date',
               'wealth_growth', 'drawdown', and optionally 'return_pct' columns
    win_rate : % e.g. 62.5
    sharpe   : annualised Sharpe ratio (or None if insufficient data)
    max_dd   : drawdown as a decimal e.g. -0.12 (will be displayed as -12.00%)
    """
    df = df.copy()
    starting_capital = df["wealth_growth"].iloc[0]
    final_value      = df["wealth_growth"].iloc[-1]
    total_return_pct = (final_value / starting_capital - 1) * 100
    sharpe_str       = f"{sharpe:.2f}" if sharpe is not None else "N/A"

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3],
    )

    fig.add_hline(
        y=starting_capital,
        line=dict(color=BBG_BORDER, width=1, dash="dot"),
        row=1, col=1,
    )

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["wealth_growth"],
        mode="lines",
        line=dict(color=BBG_BLUE, width=2.5),
        name="Equity Curve",
        hovertemplate="<b>%{x|%b %d}</b><br>$%{y:,.2f}<extra></extra>",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["drawdown"],
        mode="lines", fill="tozeroy",
        fillcolor="rgba(255,59,59,0.18)",
        line=dict(color=BBG_RED, width=1.5),
        name="Drawdown",
        hovertemplate="<b>%{x|%b %d}</b><br>DD: %{y:.2%}<extra></extra>",
    ), row=2, col=1)

    axis_common = dict(
        tickfont=dict(size=10, color=BBG_SUBTEXT, family=FONT_FAMILY),
        gridcolor=BBG_GRID,
        linecolor=BBG_BORDER,
        zerolinecolor=BBG_BORDER,
        showgrid=True,
    )

    stats_text = (
        f"Return: {'+' if total_return_pct >= 0 else ''}{total_return_pct:.2f}%   "
        f"Win Rate: {win_rate:.1f}%   "
        f"Sharpe: {sharpe_str}   "
        f"Max DD: {max_dd * 100:.2f}%"
    )

    fig.update_layout(
        title=dict(
            text=f"WTI STRATEGY  ·  Portfolio Performance & Risk<br>"
                 f"<span style='font-size:10px;color:#f5c542'>{stats_text}</span>",
            font=dict(family=FONT_FAMILY, size=16, color=BBG_ORANGE),
            x=0.01, xanchor="left",
        ),
        paper_bgcolor=BBG_BG,
        plot_bgcolor=BBG_PANEL,
        font=dict(family=FONT_FAMILY, color=BBG_TEXT),
        height=700,
        hovermode="x unified",
        legend=dict(
            bgcolor="rgba(20,20,20,0.85)",
            bordercolor=BBG_BORDER, borderwidth=1,
            font=dict(size=10, color=BBG_TEXT),
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=0.99,   
        ),
        margin=dict(l=65, r=40, t=110, b=55),
        xaxis=dict(**axis_common),
        xaxis2=dict(**axis_common, title=dict(text="Trade Date", font=dict(size=11, color=BBG_SUBTEXT))),
        yaxis=dict(**axis_common,
                   title=dict(text="Account Value (USD)", font=dict(size=11, color=BBG_SUBTEXT)),
                   tickprefix="$", tickformat=",.0f"),
        yaxis2=dict(**axis_common,
                    title=dict(text="Drawdown (%)", font=dict(size=11, color=BBG_SUBTEXT)),
                    ticksuffix="%"),
    )

    _add_footer(fig, include_timestamp=True)

    return _save(fig, "pnl_curve.png", report_date)

# ─────────────────────────────────────────────
#  7.  PRODUCT INVENTORY SNAPSHOT
#      Weekly change bar chart for Gasoline,
#      Distillates, and Cushing crude stocks
# ─────────────────────────────────────────────
def plot_product_snapshot(df: pd.DataFrame, report_date=None) -> str:
    """
    df : must contain columns:
         'gasoline_million_bbl_change', 'distillates_million_bbl_change',
         'cushing_million_bbl_change'
    Uses the most recent row (iloc[-1]).
    Color logic: draw < 0 = bullish (green), build > 0 = bearish (red).
    """
    latest = df.iloc[-1]
 
    labels = ["Gasoline", "Distillates", "Cushing"]
    values = [
        latest["gasoline_million_bbl_change"],
        latest["distillates_million_bbl_change"],
        latest["cushing_million_bbl_change"],
    ]
 
    # draw (negative) = supply tightening = bullish = green
    # build (positive) = supply loosening = bearish = red
    bar_colors  = [BBG_GREEN if v < 0 else BBG_RED for v in values]
    text_colors = [BBG_GREEN if v < 0 else BBG_RED for v in values]
 
    fig = go.Figure()
 
    # Zero reference line
    fig.add_hline(y=0, line=dict(color=BBG_BORDER, width=1, dash="dot"))
 
    fig.add_trace(go.Bar(
        x=labels,
        y=values,
        marker_color=bar_colors,
        marker_line=dict(color=BBG_BG, width=1.5),
        text=[f"{'▼' if v < 0 else '▲'} {abs(v):.2f} mbbl" for v in values],
        textposition="outside",
        textfont=dict(size=11, family=FONT_FAMILY, color=text_colors),
        width=0.45,
        hovertemplate="<b>%{x}</b><br>Change: %{y:+.2f} mbbl<extra></extra>",
    ))
 
    # Sentiment label inside each bar
    for label, val in zip(labels, values):
        sentiment  = "BULLISH DRAW" if val < 0 else "BEARISH BUILD"
        sent_color = BBG_GREEN if val < 0 else BBG_RED
        fig.add_annotation(
            x=label, y=val * 0.5,
            text=f"<b>{sentiment}</b>",
            showarrow=False,
            font=dict(size=8, color=sent_color, family=FONT_FAMILY),
            align="center",
        )
 
    layout = _base_layout(
        title="PRODUCT INVENTORY SNAPSHOT  ·  Weekly Change (MMbbl)",
        x_title="",
        y_title="Change (Million Barrels)",
    )
 
    # Widen y range so outside text labels don't clip
    max_abs = max(abs(v) for v in values)
    layout["yaxis"]["range"]      = [-(max_abs * 1.55), max_abs * 1.55]
    layout["yaxis"]["ticksuffix"] = " mbbl"
    layout["xaxis"]["showgrid"]   = False
    layout["hovermode"]           = "closest"
 
    fig.update_layout(**layout)
 
    # Week-ending date badge
    try:
        if "period" in latest.index:
            week_end = pd.to_datetime(latest["period"]).strftime("%b %d, %Y")
        elif "date" in latest.index:
            week_end = pd.to_datetime(latest["date"]).strftime("%b %d, %Y")
        else:
            week_end = ""

        fig.add_annotation(
            text=f"Week ending  {week_end}",
            xref="paper", yref="paper", x=0.01, y=1.02,
            showarrow=False,
            font=dict(size=9, color=BBG_SUBTEXT, family=FONT_FAMILY),
            xanchor="left",
        )
    except Exception:
        pass
 
    # Net summary badge (top-right)
    net       = sum(values)
    net_label = (
        f"Net: {'+' if net >= 0 else ''}{net:.2f} mbbl<br>"
        f"{'Overall Bearish Build' if net > 0 else 'Overall Bullish Draw'}"
    )
    net_color = BBG_RED if net > 0 else BBG_GREEN
    fig.add_annotation(
        text=f"<b>{net_label}</b>",
        xref="paper", yref="paper", x=0.99, y=0.97,
        showarrow=False,
        font=dict(size=10, color=net_color, family=FONT_FAMILY),
        xanchor="right",
        bgcolor="rgba(20,20,20,0.80)",
        bordercolor=net_color, borderwidth=1, borderpad=6,
    )
 
    _add_footer(fig, include_timestamp=False)
 
    return _save(fig, "product_snapshot.png", report_date)


# ─────────────────────────────────────────────
#  8.  MARKET SNAPSHOT TICKER BOARD
#      Bloomberg-style grid of prices + WoW Δ
#      ★ timestamp ON — prices go stale fast
# ─────────────────────────────────────────────
def plot_market_snapshot(snap: dict, report_date=None) -> str:
    """
    snap : dict returned by pipeline.market_snapshot.fetch_market_snapshot()
           Keys: WTI, BRENT, NAT_GAS, RBOB, HEATING_OIL, DXY, SP500
           Each value has: price, wow_change, wow_pct  (may be None if unavailable)

    Renders a Bloomberg-style ticker board with two rows:
        Row 1: Energy commodities
        Row 2: Macro / cross-asset
    """
    # ── display config ──────────────────────────────────────────────────────
    ROWS = [
        [
            ("WTI_CRUDE",    "WTI CRUDE",   "$/bbl"),
            ("BRENT",        "BRENT",       "$/bbl"),
            ("NAT_GAS",      "NAT GAS",     "$/MMBtu"),
            ("RBOB",         "RBOB",        "$/gal"),
            ("HEATING_OIL",  "HEATING OIL", "$/gal"),
        ],
        [
            ("DXY",   "DXY",   "index"),
            ("SP500", "S&P 500", "pts"),
        ],
    ]

    # Flatten for layout maths
    all_cells = [cell for row in ROWS for cell in row]
    n_cols    = max(len(row) for row in ROWS)
    n_rows    = len(ROWS)

    fig_height = 280
    fig_width  = 1100

    fig = go.Figure()

    fig.update_layout(
        paper_bgcolor=BBG_BG,
        plot_bgcolor=BBG_BG,
        font=dict(family=FONT_FAMILY, color=BBG_TEXT),
        width=fig_width,
        height=fig_height,
        margin=dict(l=20, r=20, t=60, b=40),
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(visible=False, range=[0, 1]),
        title=dict(
            text="MARKET SNAPSHOT  ·  Prices & Week-over-Week Changes",
            font=dict(family=FONT_FAMILY, size=14, color=BBG_ORANGE),
            x=0.01, xanchor="left",
        ),
    )

    # ── grid layout ─────────────────────────────────────────────────────────
    col_w = 1.0 / n_cols
    row_h = 0.42   # fraction of normalised y-space per row (leaves margin)

    for r_idx, row in enumerate(ROWS):
        n_in_row  = len(row)
        row_col_w = 1.0 / n_in_row
        # centre short rows
        x_offset = (1.0 - n_in_row * row_col_w) / 2

        y_centre = 0.72 - r_idx * 0.50   # top row ~0.72, bottom ~0.22

        for c_idx, (key, label, unit) in enumerate(row):
            data = snap.get(key, {})
            price      = data.get("price")
            wow_change = data.get("wow_change")
            wow_pct    = data.get("wow_pct")

            x_centre = x_offset + (c_idx + 0.5) * row_col_w

            if price is None:
                price_str = "N/A"
                wow_str   = "—"
                cell_color = BBG_SUBTEXT
            else:
                # Format price — large indices (S&P) use comma notation
                if price > 999:
                    price_str = f"{price:,.0f}"
                elif price > 10:
                    price_str = f"{price:.2f}"
                else:
                    price_str = f"{price:.3f}"

                if wow_change is not None and wow_pct is not None:
                    sign      = "+" if wow_change >= 0 else ""
                    cell_color = BBG_GREEN if wow_change >= 0 else BBG_RED
                    wow_str   = f"{sign}{wow_change:.2f}  ({sign}{wow_pct:.2f}%)"
                else:
                    wow_str   = "—"
                    cell_color = BBG_SUBTEXT

            # ── Cell box ────────────────────────────────────────────────────
            fig.add_shape(
                type="rect",
                xref="paper", yref="paper",
                x0=x_centre - row_col_w * 0.46,
                x1=x_centre + row_col_w * 0.46,
                y0=y_centre - 0.22,
                y1=y_centre + 0.22,
                fillcolor=BBG_PANEL,
                line=dict(color=BBG_BORDER, width=1),
            )

            # Label (top)
            fig.add_annotation(
                xref="paper", yref="paper",
                x=x_centre, y=y_centre + 0.13,
                text=f"<b>{label}</b>",
                showarrow=False,
                font=dict(size=9, color=BBG_SUBTEXT, family=FONT_FAMILY),
                xanchor="center",
            )

            # Price (middle — large)
            fig.add_annotation(
                xref="paper", yref="paper",
                x=x_centre, y=y_centre + 0.02,
                text=f"<b>{price_str}</b>",
                showarrow=False,
                font=dict(size=16, color=BBG_AMBER, family=FONT_FAMILY),
                xanchor="center",
            )

            # Unit (small, below price)
            fig.add_annotation(
                xref="paper", yref="paper",
                x=x_centre, y=y_centre - 0.08,
                text=unit,
                showarrow=False,
                font=dict(size=8, color=BBG_SUBTEXT, family=FONT_FAMILY),
                xanchor="center",
            )

            # WoW change (bottom — coloured)
            fig.add_annotation(
                xref="paper", yref="paper",
                x=x_centre, y=y_centre - 0.17,
                text=f"WoW  {wow_str}",
                showarrow=False,
                font=dict(size=9, color=cell_color, family=FONT_FAMILY),
                xanchor="center",
            )

    _add_footer(fig, include_timestamp=True)

    return _save(fig, "market_snapshot.png", report_date)