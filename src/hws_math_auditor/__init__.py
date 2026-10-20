"""
HWS-hard-math-solution-auditor — 难题解答步骤级审计与错误定位器.

审计核心：确定性数学引擎，零模型依赖。
模型接入：可插拔显式开关，默认关闭。
"""

__version__ = "0.2.1"
__all__ = [
    "__version__",
    "datadir",
    "model",
    "parser",
    "verifier",
    "locator",
    "recalc",
    "benchmark",
    "pipeline",
    "config",
]
