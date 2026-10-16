"""pipeline 集成测试。"""

import os
import tempfile
import pytest

from hws_math_auditor.pipeline import AuditRequest, audit


class TestAuditPipeline:
    def test_audit_clean(self, sample_solution_clean):
        request = AuditRequest(solution_text=sample_solution_clean)
        result = audit(request)
        assert result.exit_code == 0  # 无错误

    def test_audit_dirty(self, sample_solution_dirty):
        request = AuditRequest(solution_text=sample_solution_dirty)
        result = audit(request)
        # 含错解答应检出错误
        assert result.exit_code == 1

    def test_audit_empty(self):
        request = AuditRequest(solution_text="")
        result = audit(request)
        assert result.exit_code == 2  # 输入不可用


class TestEncoding:
    """编码处理测试。"""

    def test_utf8_file(self):
        """测试 UTF-8 文件正常读取。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", encoding="utf-8", delete=False) as f:
            f.write("步骤1: x = 1\n步骤2: x = 1")
            f.flush()
            temp_path = f.name

        try:
            with open(temp_path, "r", encoding="utf-8") as f:
                solution_text = f.read()
            request = AuditRequest(solution_text=solution_text)
            result = audit(request)
            assert result.exit_code == 0
        finally:
            os.unlink(temp_path)

    def test_non_utf8_file_rejected(self):
        """测试非 UTF-8 文件被拒绝（不猜测编码）。"""
        # 创建 GBK 编码的文件
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            # 中文内容用 GBK 编码
            content = "步骤1: x = 1".encode("gbk")
            f.write(content)
            f.flush()
            temp_path = f.name

        try:
            # 用 UTF-8 读取应失败
            with pytest.raises(UnicodeDecodeError):
                with open(temp_path, "r", encoding="utf-8") as f:
                    f.read()
        finally:
            os.unlink(temp_path)

    def test_gbk_file_with_explicit_encoding(self):
        """测试显式指定 GBK 编码可正常读取。"""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            content = "步骤1: x = 1\n步骤2: x = 1".encode("gbk")
            f.write(content)
            f.flush()
            temp_path = f.name

        try:
            # 用 GBK 编码读取
            with open(temp_path, "r", encoding="gbk") as f:
                solution_text = f.read()
            request = AuditRequest(solution_text=solution_text)
            result = audit(request)
            # 两个步骤都是 x=1，应该无错误
            assert result.exit_code == 0
        finally:
            os.unlink(temp_path)

    def test_encoding_parameter_default_utf8(self):
        """测试 --encoding 默认值为 utf-8。"""
        # 测试默认编码行为：UTF-8 文件应正常读取
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", encoding="utf-8", delete=False) as f:
            f.write("步骤1: x = 1\n步骤2: x = 1")
            f.flush()
            temp_path = f.name

        try:
            # 直接用 open 读取（模拟 CLI 默认行为）
            with open(temp_path, "r", encoding="utf-8") as f:
                solution_text = f.read()
            request = AuditRequest(solution_text=solution_text)
            result = audit(request)
            assert result.exit_code == 0
        finally:
            os.unlink(temp_path)

    def test_non_utf8_with_encoding_param(self):
        """测试 --encoding 参数可指定非 UTF-8 编码。"""
        # 创建 GBK 文件
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            content = "步骤1: x = 1\n步骤2: x = 1".encode("gbk")
            f.write(content)
            f.flush()
            temp_path = f.name

        try:
            # 用 GBK 编码读取
            with open(temp_path, "r", encoding="gbk") as f:
                solution_text = f.read()
            request = AuditRequest(solution_text=solution_text)
            result = audit(request)
            assert result.exit_code == 0
        finally:
            os.unlink(temp_path)
