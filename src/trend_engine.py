import numpy as np
from scipy.stats import kendalltau, theilslopes


def analyze_trend(values):
    """
    Analyze a time series using:
    - Mann-Kendall test (via Kendall's tau)
    - Theil-Sen slope

    values: ordered time-series values
    """

    values = np.asarray(values, dtype=float)

    # Remove missing observations
    values = values[np.isfinite(values)]

    if len(values) < 8:
        raise ValueError("At least 8 valid observations are required.")

    time = np.arange(len(values))

    # Mann-Kendall-style monotonic trend test
    tau, p_value = kendalltau(time, values)

    # Theil-Sen robust slope
    slope, intercept, low_slope, high_slope = theilslopes(
        values,
        time,
        0.95
    )

    if p_value < 0.05:
        if tau > 0:
            direction = "Increasing"
        elif tau < 0:
            direction = "Decreasing"
        else:
            direction = "No trend"
        significant = True
    else:
        direction = "No significant trend"
        significant = False

    return {
        "observations": len(values),
        "tau": float(tau),
        "p_value": float(p_value),
        "sen_slope": float(slope),
        "slope_low": float(low_slope),
        "slope_high": float(high_slope),
        "direction": direction,
        "significant": significant,
    }


if __name__ == "__main__":

    # Temporary test data.
    # Later this will be replaced with NASA SMAP observations.
    rng = np.random.default_rng(42)

    time = np.arange(120)

    # Artificial decreasing signal
    values = 0.35 - (0.0015 * time) + rng.normal(0, 0.01, 120)

    result = analyze_trend(values)

    print("\nEARTH TREND DETECTIVE")
    print("====================")
    print(f"Observations: {result['observations']}")
    print(f"Trend: {result['direction']}")
    print(f"Sen's slope: {result['sen_slope']:.6f}")
    print(f"95% slope range: {result['slope_low']:.6f} → {result['slope_high']:.6f}")
    print(f"Kendall tau: {result['tau']:.4f}")
    print(f"p-value: {result['p_value']:.6f}")
    print(f"Statistically significant: {result['significant']}")
