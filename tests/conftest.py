"""测试配置。"""

import pytest


@pytest.fixture
def sample_solution_clean():
    """干净解答样例。"""
    return """步骤1: 解方程 x² - 5x + 6 = 0
步骤2: 因式分解 (x-2)(x-3) = 0
步骤3: 所以 x = 2 或 x = 3"""


@pytest.fixture
def sample_solution_dirty():
    """含错解答样例。"""
    return """步骤1: 解方程 x² - 5x + 6 = 0
步骤2: 因式分解 (x-2)(x-3) = 0
步骤3: 所以 x = 2 - 3 = -1"""
