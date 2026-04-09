def classify_regime(spread):
    """
    Classifies market regime based on CL1-CL2 spread level.
    """
    if spread > 10:
        return "EXTREME_DISLOCATION"
    elif spread > 3:
        return "TIGHT"
    elif spread > 0:
        return "NORMAL_TIGHT"
    elif spread > -1:
        return "BALANCED"
    elif spread > -3:
        return "OVERSUPPLIED"
    else:
        return "DEEP_CONTANGO"


def detect_regime_with_momentum(curve_df):
    """
    Detects regime using both spread level and recent spread momentum.
    """
    if curve_df is None or curve_df.empty:
        raise ValueError("Curve data empty in regime model")

    spread = curve_df["spread"].iloc[-1]

    # 1-week change
    if len(curve_df) > 5:
        prev_spread = curve_df["spread"].iloc[-5]
        spread_change = spread - prev_spread
    else:
        spread_change = 0.0

    regime = classify_regime(spread)
    caution_flag = False
    reversal_flag = False

    # Extreme threshold logic
    if regime == "EXTREME_DISLOCATION":
        caution_flag = True

    # Reversal logic
    if regime == "EXTREME_DISLOCATION" and spread_change < -2:
        regime = "CRISIS_UNWIND"
        reversal_flag = True
        caution_flag = True

    elif regime == "TIGHT" and spread_change < -1.5:
        regime = "WEAKENING_TIGHTNESS"
        caution_flag = True

    elif regime == "OVERSUPPLIED" and spread_change > 1.5:
        regime = "RECOVERING_BALANCE"

    return regime, spread_change, caution_flag, reversal_flag