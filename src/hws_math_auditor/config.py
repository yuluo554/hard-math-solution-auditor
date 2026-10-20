"""配置与模型开关。"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class Config:
    """全局配置。

    模型开关默认关——审计核心零模型可跑。
    """

    model_enabled: bool = False  # K7: 默认关
    model_endpoint: str = ""
    model_provider: Literal["openai_compat", "llama_cpp", "omni_infer"] = "openai_compat"
    model_timeout: int = 60

    # 数值口径唯一定义点（K8）
    tolerance: float = 1e-9


config = Config()
