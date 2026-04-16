import pandas as pd

def generate_insights(inventory_row, curve_structure, curve_spread, crack_spread, crack_change,refinery_util, refinery_change, crude_exp_surprise, gasoline_exp_surprise, distillate_exp_surprise, cushing_exp_surprise, spread_magnitude, spread_zscore, EXPECTATIONS, regime, spread_change = 0.0, caution_flag = False, reversal_flag = False, event_override = None):
    insights = {}

    inv_signal = inventory_row["signal"]
    inv_surprise = inventory_row["inventory_surprise"]

    def classify_expectation_signal(x):
        try:
            x = float(x)
        except (TypeError, ValueError):
            return "neutral"

        if pd.isna(x):
            return "neutral"
        if x < -1:
            return "bullish"   # bigger draw than expected
        if x > 1:
            return "bearish"   # bigger build than expected
        return "neutral"

    crude_exp_signal = classify_expectation_signal(crude_exp_surprise)
    gas_exp_signal = classify_expectation_signal(gasoline_exp_surprise)
    dist_exp_signal = classify_expectation_signal(distillate_exp_surprise)
    cushing_exp_signal = classify_expectation_signal(cushing_exp_surprise)

    # =========================
    # Inventory View
    # =========================
    if crude_exp_surprise > 1:
        inv_view = "Bearish vs expectations (build above consensus)"
    elif crude_exp_surprise < -1:
        inv_view = "Bullish vs expectations (draw below consensus)"
    else:
        inv_view = "Neutral vs expectations"

    if inv_signal == "bullish":
        inv_view += " | Bullish vs seasonal"
    elif inv_signal == "bearish":
        inv_view += " | Bearish vs seasonal"
    else:
        inv_view += " | Neutral vs seasonal"

    insights["inventory_view"] = inv_view

    divergence = False

    # =========================
    # Curve View
    # =========================
    curve_view = f"{curve_structure} (CL1–CL2: {curve_spread:.2f})"
    insights["curve_view"] = curve_view

    # =========================
    # Crack / Demand View
    # =========================
    if crack_spread > 25:
        crack_view = f"Strong refinery margins (Crack: {crack_spread:.2f}) — strong demand"
        demand_signal = "bullish"
    elif crack_spread > 15:
        crack_view = f"Moderate refinery margins (Crack: {crack_spread:.2f})"
        demand_signal = "neutral"
    else:
        crack_view = f"Weak refinery margins (Crack: {crack_spread:.2f}) — weak demand"
        demand_signal = "bearish"

    insights["crack_view"] = crack_view

    # =========================
    # Spread Regime
    # IMPORTANT:
    # spread > 0 = backwardation
    # spread < 0 = contango
    # =========================
    def classify_spread_regime(magnitude, zscore, spread):
        # spread = CL1 - CL2: positive = backwardation, negative = contango
        # zscore = (spread - rolling_mean) / rolling_std
        #   high positive zscore → unusually tight (backwardation extreme)
        #   high negative zscore → unusually loose (contango extreme)
        if spread > 0:  # backwardation
            if zscore > 2:
                return "CRISIS TIGHTNESS"
            elif zscore > 1:
                return "STRONG BACKWARDATION"
            else:
                return "NORMAL BACKWARDATION"
        else:  # contango
            if zscore < -2:
                return "DEEP CONTANGO"
            else:
                return "MILD CONTANGO"

    spread_regime = classify_spread_regime(
        spread_magnitude,
        spread_zscore,
        curve_spread,
    )
    insights["spread_regime"] = spread_regime

    # =========================
    # Product Demand
    # =========================
    gas_signal = inventory_row.get("gasoline_signal", None)
    dist_signal = inventory_row.get("distillates_signal", None)

    product_bias = 0

    if gas_signal == "bullish":
        product_bias += 1
    elif gas_signal == "bearish":
        product_bias -= 1

    if dist_signal == "bullish":
        product_bias += 1
    elif dist_signal == "bearish":
        product_bias -= 1

    if product_bias >= 2:
        demand_signal = "bullish"
        insights["product_view"] = "Strong product demand (gasoline + distillates draws)"
    elif product_bias <= -2:
        demand_signal = "bearish"
        insights["product_view"] = "Weak product demand (builds across products)"
    else:
        insights["product_view"] = "Mixed product signals"

    # =========================
    # Cushing Distortion
    # =========================
    cushing_change = inventory_row.get("cushing_million_bbl_change", 0)
    cushing_flag = False

    if abs(cushing_change) > 2:
        cushing_flag = True
        insights["cushing_flag"] = "Cushing distortion affecting headline crude"
    else:
        insights["cushing_flag"] = "No major Cushing distortion"

    # =========================
    # Divergence / Alignment
    # IMPORTANT:
    # spread > 0 = backwardation
    # spread < 0 = contango
    # =========================
    is_backwardation = curve_spread > 0
    is_contango = curve_spread < 0

    if inv_signal == "bearish" and is_backwardation:
        combined = "BULLISH DIVERGENCE: Physical tightness overriding inventory builds"
        final_signal = "BULLISH"
        divergence = True

    elif inv_signal == "bullish" and is_contango:
        combined = "BEARISH DIVERGENCE: Inventory draws failing to tighten curve"
        final_signal = "BEARISH"
        divergence = True

    else:
        if inv_signal == "bullish" and is_backwardation and demand_signal == "bullish":
            combined = "Strong bullish alignment (tight supply + curve + demand)"
            final_signal = "STRONG BULLISH"

        elif inv_signal == "bearish" and is_contango and demand_signal == "bearish":
            combined = "Strong bearish alignment (oversupply + weak curve + weak demand)"
            final_signal = "STRONG BEARISH"

        elif demand_signal == "bullish" and is_backwardation:
            combined = "Demand-driven bullish structure despite mixed inventory signals"
            final_signal = "BULLISH"

        elif demand_signal == "bearish" and is_contango:
            combined = "Weak demand reinforcing bearish structure"
            final_signal = "BEARISH"

        else:
            combined = "Mixed signals across supply, demand, and curve"
            final_signal = "NEUTRAL"

    # =========================
    # Event Override
    # =========================
    if event_override in {"CEASEFIRE", "DE_ESCALATION"}:
        combined = "EVENT OVERRIDE: Geopolitical de-escalation likely compresses prompt risk premium"
        final_signal = "BEARISH"
    elif event_override in {"SUPPLY_SHOCK", "ESCALATION"}:
        combined = "EVENT OVERRIDE: Geopolitical escalation reinforces prompt scarcity"
        final_signal = "BULLISH"

    insights["combined_view"] = combined
    insights["final_signal"] = final_signal

    # =========================
    # Expectation Table
    # =========================
    insights["expectation_table"] = {
        "crude": {
            "actual": float(inventory_row.get("weekly_change", 0)),
            "expected": float(EXPECTATIONS.get("crude", 0)),
            "surprise": float(crude_exp_surprise),
            "signal": crude_exp_signal,
        },
        "gasoline": {
            "actual": float(inventory_row.get("gasoline_million_bbl_change", 0)),
            "expected": float(EXPECTATIONS.get("gasoline", 0)),
            "surprise": float(gasoline_exp_surprise),
            "signal": gas_exp_signal,
        },
        "distillates": {
            "actual": float(inventory_row.get("distillates_million_bbl_change", 0)),
            "expected": float(EXPECTATIONS.get("distillates", 0)),
            "surprise": float(distillate_exp_surprise),
            "signal": dist_exp_signal,
        },
        "cushing": {
            "actual": float(inventory_row.get("cushing_million_bbl_change", 0)),
            "expected": float(EXPECTATIONS.get("cushing", 0)),
            "surprise": float(cushing_exp_surprise),
            "signal": cushing_exp_signal,
        },
    }

    # =========================
    # Regime View
    # =========================
    insights["regime"] = regime

    if regime == "CRISIS_TIGHTNESS":
        insights["regime_view"] = "Extreme physical tightness — panic pricing"
    elif regime == "CRISIS_UNWIND":
        insights["regime_view"] = "Extreme tightness collapsing — high reversal risk"
    elif regime == "TIGHT":
        insights["regime_view"] = "Strong backwardation — supportive"
    elif regime == "NORMAL_TIGHT":
        insights["regime_view"] = "Mild backwardation — modestly supportive"
    elif regime == "WEAKENING_TIGHTNESS":
        insights["regime_view"] = "Backwardation weakening — caution"
    elif regime == "BALANCED":
        insights["regime_view"] = "Balanced market — flat curve"
    elif regime == "RECOVERING_BALANCE":
        insights["regime_view"] = "Contango recovering — improving balance"
    elif regime == "OVERSUPPLIED":
        insights["regime_view"] = "Mild contango — oversupplied"
    elif regime == "DEEP_CONTANGO":
        insights["regime_view"] = "Deep contango — severe oversupply"
    else:
        insights["regime_view"] = "Balanced market"

    # =========================
    # Confidence Score
    # =========================
    confidence = 0

    if abs(inv_surprise) > 5:
        confidence += 2
    elif abs(inv_surprise) > 2:
        confidence += 1

    abs_spread = abs(curve_spread)
    if abs_spread > 10:
        confidence += 4
    elif abs_spread > 3:
        confidence += 3
    elif abs_spread > 1:
        confidence += 2
    elif abs_spread > 0.5:
        confidence += 1

    if crack_spread > 30:
        confidence += 2
    elif crack_spread > 20:
        confidence += 1

    if divergence:
        confidence += 2
    elif "STRONG" in final_signal:
        confidence += 1

    if regime in ["WEAKENING_TIGHTNESS", "CRISIS_UNWIND"]:
        confidence -= 1
    elif regime == "EXTREME_DISLOCATION":
        confidence -= 2

    # Positive spread_change = backwardation strengthening
    # Negative spread_change = backwardation weakening / contango widening
    if spread_change < -2:
        confidence -= 1
    if abs(spread_change) > 3:
        confidence -= 1

    if event_override is not None:
        confidence -= 1
    if event_override in {"CEASEFIRE", "DE_ESCALATION"}:
        confidence -= 2
    elif event_override in {"SUPPLY_SHOCK", "ESCALATION"}:
        confidence += 1

    if cushing_flag:
        confidence -= 1

    confidence = max(confidence, 0)

    if confidence >= 7:
        confidence_label = "Extreme"
    elif confidence >= 5:
        confidence_label = "Very High"
    elif confidence >= 3:
        confidence_label = "High"
    elif confidence >= 2:
        confidence_label = "Medium"
    else:
        confidence_label = "Low"

    insights["confidence"] = confidence_label

    # =========================
    # Trade Idea
    # =========================
    if event_override in {"CEASEFIRE", "DE_ESCALATION"}:
        trade = (
            "Fade prompt strength. Avoid fresh longs. "
            "Position for continued backwardation compression unless geopolitical risk re-escalates."
        )

    elif reversal_flag or regime == "CRISIS_UNWIND":
        trade = (
            "Short WTI or short CL1–CL2 spreads. "
            "Extreme backwardation is unwinding, indicating normalization and reversal risk."
        )

    elif regime == "EXTREME_DISLOCATION":
        trade = (
            "Stay cautious on fresh longs. "
            "Market remains structurally tight, but dislocation levels imply elevated reversal risk and unstable carry."
        )

    elif regime == "WEAKENING_TIGHTNESS":
        trade = (
            "Tactically long WTI only with reduced conviction. "
            "Backwardation remains supportive, but weakening spread momentum raises reversal risk."
        )

    elif divergence and curve_spread > 2:
        trade = (
            "Long WTI and long CL1–CL2 roll. "
            "Curve signals physical tightness overriding inventory data."
        )

    elif final_signal == "STRONG BULLISH":
        trade = "Long WTI and long prompt spreads."
    elif final_signal == "STRONG BEARISH":
        trade = "Short WTI and short spreads."
    elif final_signal == "BULLISH":
        trade = "Long WTI or position for strengthening backwardation."
    elif final_signal == "BEARISH":
        trade = "Short WTI or position for widening contango."
    else:
        trade = "No clear edge. Stay neutral."

    insights["trade_idea"] = trade

    # =========================
    # Narrative
    # =========================
    insights["narrative"] = (
        f"{combined}. Demand signal: {demand_signal}. "
        f"Spread momentum: {spread_change:.2f}. "
        f"{'Cushing distortion present.' if cushing_flag else ''}"
    )

    if event_override in {"CEASEFIRE", "DE_ESCALATION"}:
        insights["narrative"] = (
            "EVENT-DRIVEN NORMALIZATION: Crude inventories printed above expectations "
            "(bearish), while product draws indicate resilient demand. "
            f"However, rapid spread compression ({spread_change:.2f}) confirms "
            "that geopolitical risk premium is unwinding and dominating price action."
        )

    elif reversal_flag or regime == "CRISIS_UNWIND":
        insights["narrative"] = (
            "REVERSAL REGIME: The market is exiting extreme backwardation. "
            "Spread compression suggests normalization of supply conditions and elevated downside risk in the prompt premium."
        )

    elif divergence:
        if is_backwardation:
            insights["narrative"] = (
                "BULLISH DIVERGENCE: Physical market strength overrides inventory builds. "
                "Backwardation and strong demand indicate prompt scarcity."
            )
        else:
            insights["narrative"] = (
                "BEARISH DIVERGENCE: Inventory draws are not tightening the curve. "
                "Weak demand confirms structural oversupply."
            )

    elif regime == "EXTREME_DISLOCATION":
        insights["narrative"] = (
            "EXTREME MARKET CONDITION: The curve reflects severe dislocation. "
            "Such levels may still indicate scarcity, but they are historically unstable and prone to reversal."
        )

    else:
        insights["narrative"] = (
            "Market signals broadly aligned: inventory, demand, and curve structure "
            "support the current directional bias."
        )

    # =========================
    # Metrics Output
    # =========================
    insights["inventory_level"] = inventory_row["value_million_bbl"]
    insights["weekly_change"] = inventory_row["weekly_change"]
    insights["seasonal_avg"] = inventory_row["seasonal_avg"]
    insights["inventory_surprise"] = inventory_row["inventory_surprise"]

    insights["gasoline_change"] = inventory_row.get("gasoline_million_bbl_change")
    insights["gasoline_seasonal_avg"] = inventory_row.get("gasoline_seasonal_avg")
    insights["gasoline_surprise"] = inventory_row.get("gasoline_surprise")
    insights["gasoline_signal"] = inventory_row.get("gasoline_signal")

    insights["distillates_change"] = inventory_row.get("distillates_million_bbl_change")
    insights["distillates_seasonal_avg"] = inventory_row.get("distillates_seasonal_avg")
    insights["distillates_surprise"] = inventory_row.get("distillates_surprise")
    insights["distillates_signal"] = inventory_row.get("distillates_signal")

    insights["cushing_change"] = inventory_row.get("cushing_million_bbl_change")
    insights["cushing_seasonal_avg"] = inventory_row.get("cushing_seasonal_avg")
    insights["cushing_surprise"] = inventory_row.get("cushing_surprise")
    insights["cushing_signal"] = inventory_row.get("cushing_signal")

    insights["refinery_util"] = refinery_util
    insights["refinery_change"] = refinery_change

    insights["spread_zscore"] = spread_zscore
    insights["spread_magnitude"] = spread_magnitude
    insights["spread"] = curve_spread
    insights["spread_change"] = spread_change

    insights["crack_spread"] = crack_spread
    insights["crack_change"] = crack_change

    insights["crude_exp_surprise"] = crude_exp_surprise
    insights["gasoline_exp_surprise"] = gasoline_exp_surprise
    insights["distillate_exp_surprise"] = distillate_exp_surprise
    insights["cushing_exp_surprise"] = cushing_exp_surprise

    insights["crude_exp_signal"] = crude_exp_signal
    insights["gasoline_exp_signal"] = gas_exp_signal
    insights["distillate_exp_signal"] = dist_exp_signal
    insights["cushing_exp_signal"] = cushing_exp_signal

    insights["event_override"] = event_override

    return insights