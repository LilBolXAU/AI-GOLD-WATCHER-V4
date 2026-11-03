"""
Robustness and statistical significance calculations for AI GOLD WATCHER V4.
Implements Deflated Sharpe Ratio (Bailey and Lopez de Prado, 2014).
"""

import math
from typing import Sequence
import numpy as np


def compute_deflated_sharpe(
    observed_sharpe: float,
    num_trials: int,
    returns: Sequence[float],
    benchmark_sharpe: float = 0.0,
) -> float:
    """
    Computes the Deflated Sharpe Ratio (DSR) p-value.
    Adjusts for multiple testing bias, non-normality (skewness/kurtosis), and sample length.
    Returns: p-value in [0.0, 1.0]. A value > 0.95 indicates statistical significance at 5% level.
    """
    n = len(returns)
    if n < 30 or num_trials < 1:
        return 0.0

    ret_arr = np.array(returns)
    mean = np.mean(ret_arr)
    std = np.std(ret_arr, ddof=1)
    if std == 0:
        return 0.0

    # Skewness and Kurtosis
    skew = float(np.mean(((ret_arr - mean) / std) ** 3))
    kurt = float(np.mean(((ret_arr - mean) / std) ** 4))

    # Expected maximum Sharpe under null hypothesis of zero edge across `num_trials`
    # E[max_N] ≈ (1 - gamma) * Z^{-1}(1 - 1/N) + gamma * Z^{-1}(1 - 1/(N*e))
    # Approximation from Lopez de Prado (2014):
    euler_mascheroni = 0.5772156649
    if num_trials > 1:
        z_n = math.sqrt(2.0 * math.log(num_trials))
        expected_max_sharpe = z_n + (euler_mascheroni / z_n)
    else:
        expected_max_sharpe = benchmark_sharpe

    # Variance of Sharpe estimator under non-normal returns
    var_sharpe = (1.0 + 0.5 * (observed_sharpe ** 2) - skew * observed_sharpe + ((kurt - 3.0) / 4.0) * (observed_sharpe ** 2)) / n

    if var_sharpe <= 0:
        return 0.0

    # Test statistic
    z_stat = (observed_sharpe - expected_max_sharpe) / math.sqrt(var_sharpe)

    # Standard normal cumulative distribution function
    dsr_pvalue = 0.5 * (1.0 + math.erf(z_stat / math.sqrt(2.0)))
    return round(float(dsr_pvalue), 4)
