def generate_insights(inventory_row, curve_structure, curve_spread, crack_spread):
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
    if inv_signal == "bearish" and "Backwardation" in curve_structure:
        combined = "BULLISH DIVERGENCE: Physical tightness overriding inventory builds"
        final_signal = "BULLISH"
        divergence = True

    elif inv_signal == "bullish" and "Contango" in curve_structure:
        combined = "BEARISH DIVERGENCE: Inventory draws failing to tighten curve"
        final_signal = "BEARISH"
        divergence = True

    else:
        # Normal logic (no divergence)
        if inv_signal == "bullish" and "Backwardation" in curve_structure and demand_signal == "bullish":
            combined = "Strong bullish alignment (tight supply + supportive curve + strong demand)"
            final_signal = "STRONG BULLISH"
        elif inv_signal == "bearish" and "Contango" in curve_structure and demand_signal == "bearish":
            combined = "Strong bearish alignment (oversupply + weak curve + weak demand)"
            final_signal = "STRONG BEARISH"
        elif demand_signal == "bullish" and "Backwardation" in curve_structure:
            combined = "Demand-driven bullish structure despite mixed inventory signals"
            final_signal = "BULLISH"
        elif demand_signal == "bearish" and "Contango" in curve_structure:
            combined = "Weak demand reinforcing bearish structure"
            final_signal = "BEARISH"
        else:
            combined = "Mixed signals across fundamentals and curve"
            final_signal = "NEUTRAL"

    insights["combined_view"] = combined
    insights["final_signal"] = final_signal


    # CONFIDENCE SCORE
    confidence = 0

    # Inventory strength
    if abs(inv_surprise) > 5:
        confidence += 2
    elif abs(inv_surprise) > 2:
        confidence += 1

    # Curve dominance
    abs_spread = abs(curve_spread)
    if abs_spread > 10:
        confidence += 4   # DISLOCATION / CRISIS
    elif abs_spread > 3:
        confidence += 3   # EXTREME
    elif abs_spread > 1:
        confidence += 2
    elif abs_spread > 0.5:
        confidence += 1

    # Demand (crack spread) strength
    if crack_spread > 30:
        confidence += 2   # very strong demand
    elif crack_spread > 20:
        confidence += 1

    # Divergence boost
    if divergence:
        confidence += 2   # high conviction anomaly
    elif "STRONG" in final_signal:
        confidence += 1   # aligned system

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

  
    # TRADE IDEA 
    if divergence and curve_spread > 10:
        trade = "High-conviction long WTI and long roll (CL1–CL2). Position for continued extreme backwardation driven by physical scarcity. Favorable carry dominates return profile."
    elif divergence and curve_spread > 2:
        trade = "Long WTI and long roll (CL1–CL2). Curve signals physical tightness overriding inventory data. Focus on roll yield and front-month strength."
    elif final_signal == "STRONG BULLISH":
        trade = "Long WTI and long prompt spreads. Aligned supply, demand, and curve signals support upside continuation."
    elif final_signal == "STRONG BEARISH":
        trade = "Short WTI and short spreads. Weak demand and oversupply conditions favor downside and negative carry."
    elif final_signal == "BULLISH":
        trade = "Long WTI or position for strengthening backwardation"
    elif final_signal == "BEARISH":
        trade = "Short WTI or position for widening contango"
    else:
        trade = "No clear edge. Stay neutral and wait for alignment across supply, demand, and curve signals."

    insights["trade_idea"] = trade

    if divergence:
        if "Backwardation" in curve_structure:
            insights["narrative"] = (
                "BULLISH DIVERGENCE: The physical market is ignoring headline inventory builds. "
                "Severe backwardation combined with strong refinery margins indicates acute prompt demand and supply stress."
            )
        else: # It must be Contango
            insights["narrative"] = (
                "BEARISH DIVERGENCE: Inventory draws are not translating into structural tightness. "
                "Weak demand signals from crack spreads confirm oversupply conditions."
            )
    elif "Extreme" in curve_structure:
        # Handle non-divergent but extreme states
        state = "undersupply" if "Backwardation" in curve_structure else "oversupply"
        insights["narrative"] = f"MARKET STRESS: The curve indicates extreme {state}. High conviction alignment with data."
    else:
        insights["narrative"] = "Market signals broadly aligned with fundamental data."

    
    insights["inventory_level"] = inventory_row["value_million_bbl"]
    insights["weekly_change"] = inventory_row["weekly_change"]
    insights["seasonal_avg"] = inventory_row["seasonal_avg"]
    insights["inventory_surprise"] = inventory_row["inventory_surprise"]
    insights["spread"] = curve_spread
    insights["crack_spread"] = crack_spread
    
    return insights