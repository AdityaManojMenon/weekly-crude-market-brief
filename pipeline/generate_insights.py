def generate_insights(inventory_row, curve_structure, curve_spread):
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
        if inv_signal == "bullish" and "Backwardation" in curve_structure:
            combined = "Strong bullish alignment (tight supply + supportive curve)"
            final_signal = "STRONG BULLISH"
        elif inv_signal == "bearish" and "Contango" in curve_structure:
            combined = "Strong bearish alignment (oversupply + weak curve)"
            final_signal = "STRONG BEARISH"
        else:
            combined = "Mixed signals across fundamentals and curve"
            final_signal = "NEUTRAL"

    insights["combined_view"] = combined
    insights["final_signal"] = final_signal


    # CONFIDENCE SCORE
    confidence = 0

    # Inventory strength
    if abs(inv_surprise) > 3:
        confidence += 1

    # Curve dominance
    abs_spread = abs(curve_spread)
    if abs_spread > 2:
        confidence += 3   
    elif abs_spread > 1:
        confidence += 2
    elif abs_spread > 0.5:
        confidence += 1

    # Divergence boost
    if divergence:
        confidence += 2

    if confidence >= 4:
        confidence_label = "Very High"
    elif confidence >= 3:
        confidence_label = "High"
    elif confidence == 2:
        confidence_label = "Medium"
    else:
        confidence_label = "Low"

    insights["confidence"] = confidence_label

  
    # TRADE IDEA 
    if divergence and curve_spread > 2:
        trade = "Long WTI and long roll (CL1–CL2) — capture extreme backwardation carry"
    elif final_signal == "STRONG BULLISH":
        trade = "Long WTI and long prompt spreads"
    elif final_signal == "STRONG BEARISH":
        trade = "Short WTI and short spreads"
    elif final_signal == "BULLISH":
        trade = "Long WTI or position for strengthening backwardation"
    elif final_signal == "BEARISH":
        trade = "Short WTI or position for widening contango"
    else:
        trade = "No clear edge — wait for confirmation"

    insights["trade_idea"] = trade

    if divergence:
        if "Backwardation" in curve_structure:
            insights["narrative"] = (
                "BULLISH DIVERGENCE: The physical market is ignoring headline inventory builds. "
                "Severe backwardation suggests imminent supply risk or extreme prompt scarcity."
            )
        else: # It must be Contango
            insights["narrative"] = (
                "BEARISH DIVERGENCE: Massive inventory draws are failing to support the curve. "
                "Deep contango suggests the market is structurally oversupplied despite the headline draw."
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
    
    return insights