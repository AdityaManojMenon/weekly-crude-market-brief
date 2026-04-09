def generate_insights(inventory_row, curve_structure, curve_spread, crack_spread, regime, spread_change = 0.0, caution_flag = False, reversal_flag = False, event_override = None):
    insights = {}

    inv_signal = inventory_row["signal"]
    inv_surprise = inventory_row["inventory_surprise"]


    divergence = False

    # INVENTORY VIEW
    if inv_signal == "bullish":
        inv_view = "Bullish inventory surprise (draw vs seasonal)"
    elif inv_signal == "bearish":
        inv_view = "Bearish inventory surprise (build vs seasonal)"
    else:
        inv_view = "Neutral inventory signal"

    insights["inventory_view"] = inv_view

    # CURVE VIEW 
    curve_view = f"{curve_structure} (CL1–CL2: {curve_spread:.2f})"
    insights["curve_view"] = curve_view

    # CRACK SPREAD VIEW
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

    #DIVERGENCE DETECTION
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

    insights["combined_view"] = combined
    insights["final_signal"] = final_signal

    #Event Override
    if event_override == "CEASEFIRE" or event_override == "DE_ESCALATION":
        combined = "EVENT OVERRIDE: Geopolitical de-escalation likely compresses prompt risk premium"
        final_signal = "BEARISH"

    elif event_override == "SUPPLY_SHOCK" or event_override == "ESCALATION":
        combined = "EVENT OVERRIDE: Geopolitical escalation reinforces prompt scarcity"
        final_signal = "BULLISH"

    insights["combined_view"] = combined
    insights["final_signal"] = final_signal

    # Regime View  
    insights["regime"] = regime

    if regime == "CRISIS_TIGHTNESS":
        insights["regime_view"] = "Extreme physical tightness — panic pricing"

    elif regime == "CRISIS_UNWIND":
        insights["regime_view"] = "Extreme tightness collapsing — high reversal risk"

    elif regime == "TIGHT":
        insights["regime_view"] = "Strong backwardation — supportive"

    elif regime == "WEAKENING_TIGHTNESS":
        insights["regime_view"] = "Backwardation weakening — caution"

    elif regime == "OVERSUPPLIED":
        insights["regime_view"] = "Contango — oversupply"

    else:
        insights["regime_view"] = "Balanced market"

    # CONFIDENCE SCORE 
    confidence = 0

    # Inventory strength
    if abs(inv_surprise) > 5:
        confidence += 2
    elif abs(inv_surprise) > 2:
        confidence += 1

    # Curve strength
    abs_spread = abs(curve_spread)
    if abs_spread > 10:
        confidence += 4
    elif abs_spread > 3:
        confidence += 3
    elif abs_spread > 1:
        confidence += 2
    elif abs_spread > 0.5:
        confidence += 1

    # Demand strength
    if crack_spread > 30:
        confidence += 2
    elif crack_spread > 20:
        confidence += 1

    # Divergence / alignment
    if divergence:
        confidence += 2
    elif "STRONG" in final_signal:
        confidence += 1

    # Regime adjustments
    if regime == "EXTREME_DISLOCATION":
        confidence -= 2
    elif regime == "WEAKENING_TIGHTNESS":
        confidence -= 1
    elif regime == "CRISIS_UNWIND":
        confidence += 1

    # Momentum adjustment
    if spread_change < -2:
        confidence -= 1

    # Event adjustment
    if event_override in {"CEASEFIRE", "DE_ESCALATION"}:
        confidence -= 2
    elif event_override in {"SUPPLY_SHOCK", "ESCALATION"}:
        confidence += 1

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

    
    #TRADE IDEA (REGIME-AWARE)
    if event_override in {"CEASEFIRE", "DE_ESCALATION"}:
        trade = (
            "Reduce or fade prompt bullish exposure. "
            "Geopolitical de-escalation can rapidly compress backwardation and remove crisis premium."
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

    # -------------------------
    # NARRATIVE (REGIME-AWARE)
    # -------------------------
    if event_override in {"CEASEFIRE", "DE_ESCALATION"}:
        insights["narrative"] = (
            "EVENT-DRIVEN NORMALIZATION: Geopolitical de-escalation is likely compressing prompt risk premium. "
            "Even if structure remains backwardated, the market may be transitioning out of crisis pricing."
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
        insights["narrative"] = "Market signals broadly aligned with fundamentals."
    # -------------------------
    # METRICS OUTPUT
    # -------------------------
    insights["inventory_level"] = inventory_row["value_million_bbl"]
    insights["weekly_change"] = inventory_row["weekly_change"]
    insights["seasonal_avg"] = inventory_row["seasonal_avg"]
    insights["inventory_surprise"] = inventory_row["inventory_surprise"]
    insights["spread"] = curve_spread
    insights["crack_spread"] = crack_spread
    insights["spread_change"] = spread_change
    insights["event_override"] = event_override

    return insights