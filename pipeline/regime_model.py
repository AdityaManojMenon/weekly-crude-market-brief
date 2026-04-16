def classify_regime(spread):
    """
    spread = CL1 - CL2
    Positive spread → backwardation → tight physical market
    Negative spread → contango → oversupplied market
    """
    if spread > 10:
        return "CRISIS_TIGHTNESS"
    elif spread > 5:
        return "TIGHT"
    elif spread > 2:
        return "NORMAL_TIGHT"
    elif spread > 0:
        return "BALANCED"
    elif spread > -3:
        return "OVERSUPPLIED"
    else:
        return "DEEP_CONTANGO"


def detect_regime_with_momentum(curve_df):
    spread = curve_df["spread"].iloc[-1]

    if len(curve_df) > 5:
        prev_spread = curve_df["spread"].iloc[-5]
        spread_change = spread - prev_spread
    else:
        spread_change = 0.0

    regime = classify_regime(spread)

    # Positive spread_change = backwardation strengthening
    # Negative spread_change = backwardation weakening / contango deepening
    if regime == "CRISIS_TIGHTNESS" and spread_change < -2:
        regime = "CRISIS_UNWIND"
    elif regime in {"TIGHT", "NORMAL_TIGHT"} and spread_change < -1.5:
        regime = "WEAKENING_TIGHTNESS"
    elif regime in {"OVERSUPPLIED", "DEEP_CONTANGO"} and spread_change > 1.5:
        regime = "RECOVERING_BALANCE"

    caution_flag = regime in {"CRISIS_UNWIND", "WEAKENING_TIGHTNESS"}
    reversal_flag = regime == "CRISIS_UNWIND"

    return regime, spread_change, caution_flag, reversal_flag