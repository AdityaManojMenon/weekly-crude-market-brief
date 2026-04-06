import plotly.graph_objects as go
import plotly.io as pio
import os
from datetime import datetime

# Professional Style Standards for charts
BBG_BG        = "#0a0a0a"   # near-black canvas
BBG_PANEL     = "#111111"   # slightly lighter plot area
BBG_GRID      = "#222222"   # subtle grid lines
BBG_BORDER    = "#333333"   # axis lines / tick marks
BBG_TEXT      = "#d4d4d4"   # primary text (off-white)
BBG_SUBTEXT   = "#888888"   # secondary labels / tick text
BBG_ORANGE    = "#f0a500"   # Bloomberg accent orange
BBG_RED       = "#ff3b3b"   # signal / current year
BBG_GREEN     = "#00d97e"   # positive spread / crack
BBG_BLUE      = "#4da6ff"   # futures curve
BBG_GRAY_BAND = "#3a3a3a"   # 5Y range fill
BBG_GRAY_LINE = "#666666"   # 5Y average dashed line
BBG_AMBER     = "#ffc233"   # annotation labels

FONT_FAMILY = "Courier New, monospace"  # terminal / data-terminal feel

def _base_layout(title: str, x_title: str, y_title: str) -> dict:
    """Return a shared Bloomberg-dark layout dict."""
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
        margin=dict(l=60, r=40, t=70, b=55),
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
    fig.write_image(path, scale=2)   # retina-quality PNG via kaleido
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

    # 5Y Range band
    fig.add_trace(go.Scatter(
        x=band["week"], y=band["max"],
        mode="lines", line=dict(width=0),
        showlegend=False, hoverinfo="skip",
        name="5Y Max",
    ))
    fig.add_trace(go.Scatter(
        x=band["week"], y=band["min"],
        mode="lines", line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(90,90,90,0.25)",
        name="5-Year Range (Min–Max)",
        hoverinfo="skip",
    ))

    # 5Y Average
    fig.add_trace(go.Scatter(
        x=band["week"], y=band["mean"],
        mode="lines",
        line=dict(color=BBG_GRAY_LINE, width=1.5, dash="dash"),
        name="5-Year Average",
    ))

    # Current year — thick orange/red signal line
    fig.add_trace(go.Scatter(
        x=current["week"], y=current["value_million_bbl"],
        mode="lines",
        line=dict(color=BBG_RED, width=3),
        name=f"{current_year} Inventory",
    ))

    layout = _base_layout(
        title=f"US CRUDE OIL INVENTORY  ·  {current_year} vs 5-Year Seasonality",
        x_title="Week of Year",
        y_title="Million Barrels (mbbl)",
    )
    fig.update_layout(**layout)

    # Subtle watermark-style annotation
    fig.add_annotation(
        text="EIA DATA", xref="paper", yref="paper",
        x=0.99, y=0.01, showarrow=False,
        font=dict(size=9, color="#333333", family=FONT_FAMILY),
        xanchor="right",
    )

    return _save(fig, "inventory_vs_5yr_band.png")


# ─────────────────────────────────────────────
#  2.  FUTURES CURVE SNAPSHOT
# ─────────────────────────────────────────────
def plot_futures_curve_snapshot(cl1_price: float, cl2_price: float):
    months = ["Front Month (CL1)", "Next Month (CL2)"]
    prices = [cl1_price, cl2_price]
    state = "BACKWARDATION" if cl1_price > cl2_price else "CONTANGO"
    accent = BBG_RED if cl1_price > cl2_price else BBG_GREEN

    fig = go.Figure()

    # Shaded area under curve
    fig.add_trace(go.Scatter(
        x=months, y=prices,
        fill="tozeroy",
        fillcolor=f"rgba(77,166,255,0.08)",
        mode="none",
        showlegend=False, hoverinfo="skip",
    ))

    # Connecting line
    fig.add_trace(go.Scatter(
        x=months, y=prices,
        mode="lines+markers+text",
        line=dict(color=BBG_BLUE, width=3),
        marker=dict(size=14, color=BBG_BLUE,
                    line=dict(color=BBG_ORANGE, width=2)),
        text=[f"<b>${p:.2f}</b>" for p in prices],
        textposition=["top center", "top center"],
        textfont=dict(size=14, color=BBG_AMBER, family=FONT_FAMILY),
        name="WTI Futures",
    ))

    layout = _base_layout(
        title=f"WTI FUTURES CURVE  ·  {state}",
        x_title="",
        y_title="Price per Barrel (USD)",
    )
    layout["xaxis"]["showgrid"] = False
    layout["yaxis"]["range"] = [min(prices) - 3, max(prices) + 4]
    layout["title"]["font"]["color"] = accent
    layout["hovermode"] = False
    fig.update_layout(**layout)

    # State badge annotation
    fig.add_annotation(
        text=f"● {state}",
        xref="paper", yref="paper", x=0.99, y=0.97,
        showarrow=False,
        font=dict(size=11, color=accent, family=FONT_FAMILY),
        xanchor="right",
        bgcolor="rgba(20,20,20,0.7)",
        bordercolor=accent, borderwidth=1,
        borderpad=6,
    )

    return _save(fig, "futures_curve.png")


# ─────────────────────────────────────────────
#  3.  SPREAD TIME SERIES
# ─────────────────────────────────────────────
def plot_spread_timeseries(curve_df):
    spread = curve_df["spread"]

    # Split into positive (backwardation) and negative (contango) for dual coloring
    pos_spread = spread.where(spread >= 0)
    neg_spread = spread.where(spread <= 0)

    fig = go.Figure()

    # Zero reference line
    fig.add_hline(y=0, line=dict(color=BBG_BORDER, width=1, dash="dot"))

    # Positive fills (backwardation)
    fig.add_trace(go.Scatter(
        x=curve_df.index, y=pos_spread,
        mode="lines", line=dict(width=0),
        fill="tozeroy", fillcolor="rgba(0,217,126,0.15)",
        showlegend=False, hoverinfo="skip",
    ))

    # Negative fills (contango)
    fig.add_trace(go.Scatter(
        x=curve_df.index, y=neg_spread,
        mode="lines", line=dict(width=0),
        fill="tozeroy", fillcolor="rgba(255,59,59,0.15)",
        showlegend=False, hoverinfo="skip",
    ))

    # Main spread line
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

    # Label regions
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

    return _save(fig, "spread_timeseries.png")


# ─────────────────────────────────────────────
#  4.  3-2-1 CRACK SPREAD
# ─────────────────────────────────────────────
def plot_crack_spread(df):
    crack = df["crack_spread"]

    # Rolling 30-day average overlay
    rolling = crack.rolling(30, min_periods=1).mean()

    fig = go.Figure()

    # Shaded area
    fig.add_trace(go.Scatter(
        x=df.index, y=crack,
        mode="none",
        fill="tozeroy",
        fillcolor="rgba(240,165,0,0.10)",
        showlegend=False, hoverinfo="skip",
    ))

    # Raw crack spread
    fig.add_trace(go.Scatter(
        x=df.index, y=crack,
        mode="lines",
        line=dict(color=BBG_ORANGE, width=1.5),
        name="3-2-1 Crack Spread",
        hovertemplate="<b>%{x}</b><br>Crack: $%{y:.2f}/bbl<extra></extra>",
    ))

    # 30-day rolling average
    fig.add_trace(go.Scatter(
        x=df.index, y=rolling,
        mode="lines",
        line=dict(color="#ffffff", width=2, dash="dot"),
        name="30-Day Average",
        hovertemplate="<b>%{x}</b><br>30d Avg: $%{y:.2f}/bbl<extra></extra>",
    ))

    layout = _base_layout(
        title="3-2-1 CRACK SPREAD  ·  Refinery Margin Indicator",
        x_title="Date",
        y_title="USD / Barrel",
    )
    fig.update_layout(**layout)

    return _save(fig, "crack_spread.png")