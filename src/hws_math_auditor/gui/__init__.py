"""GUI 模块（PySide6）。

桌面报告形态：主窗口（审计输入/结果展示）+ 设置页（模型端点配置）。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QIODeviceBase
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton, QFileDialog, QMessageBox,
    QTabWidget, QFormLayout, QLineEdit, QSpinBox, QProgressBar,
    QStatusBar, QTextBrowser
)

from hws_math_auditor.config import config
from hws_math_auditor.pipeline import AuditRequest, audit, selftest


class AuditWindow(QMainWindow):
    """主窗口：审计输入与结果展示。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HWS 难题解答审计器")
        self.resize(900, 700)
        self._setup_ui()

    def _setup_ui(self):
        """设置 UI。"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Tab 控件
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # 审计 Tab
        self._setup_audit_tab()
        # 设置 Tab
        self._setup_settings_tab()
        # 关于 Tab
        self._setup_about_tab()

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def _setup_audit_tab(self):
        """审计 Tab。"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 文件选择
        file_layout = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        file_layout.addWidget(self.file_label)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)

        # 最终断言
        assertion_layout = QHBoxLayout()
        assertion_layout.addWidget(QLabel("最终断言:"))
        self.assertion_input = QLineEdit()
        self.assertion_input.setPlaceholderText("如 x = 5 或 2(x+3) = 2x + 6")
        assertion_layout.addWidget(self.assertion_input)
        layout.addLayout(assertion_layout)

        # 模型开关
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("启用模型:"))
        self.model_check = QPushButton("关")
        self.model_check.setCheckable(True)
        self.model_check.clicked.connect(self._toggle_model)
        model_layout.addWidget(self.model_check)
        layout.addLayout(model_layout)

        # 审计按钮
        audit_btn = QPushButton("开始审计")
        audit_btn.clicked.connect(self._run_audit)
        layout.addWidget(audit_btn)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 结果展示
        self.result_view = QTextBrowser()
        self.result_view.setReadOnly(True)
        layout.addWidget(self.result_view)

        self.tabs.addTab(widget, "审计")

    def _setup_settings_tab(self):
        """设置 Tab。"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # 模型端点
        self.endpoint_input = QLineEdit(config.model_endpoint)
        self.endpoint_input.setPlaceholderText("http://localhost:11434/v1")
        layout.addRow("模型端点:", self.endpoint_input)

        # 模型提供商
        self.provider_input = QLineEdit(config.model_provider)
        layout.addRow("提供商:", self.provider_input)

        # 超时
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(10, 300)
        self.timeout_input.setValue(config.model_timeout)
        layout.addRow("超时(秒):", self.timeout_input)

        # 保存按钮
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self._save_settings)
        layout.addRow(save_btn)

        self.tabs.addTab(widget, "设置")

    def _setup_about_tab(self):
        """关于 Tab。"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        about_text = QTextBrowser()
        about_text.setReadOnly(True)
        about_text.setHtml("""
        <h2>HWS 难题解答审计器</h2>
        <p>难题解答步骤级审计与错误定位器</p>
        <p><b>核心特性:</b></p>
        <ul>
            <li>步骤级审计：逐步骤符号等价性验证</li>
            <li>三级裁决语义：ok / invalid / unverifiable</li>
            <li>首错锚定：最小索引 + 污染 vs 独立失败分类</li>
            <li>零假阳性优先：干净解永不被标记为错误</li>
            <li>真值库纪律：只存 input + expect，不存 observed</li>
        </ul>
        <p><b>版本:</b> 0.1.0</p>
        """)
        layout.addWidget(about_text)
        self.tabs.addTab(widget, "关于")

    def _browse_file(self):
        """浏览文件。"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择解答文件", "", "文本文件 (*.txt);;所有文件 (*.*)"
        )
        if file_path:
            self.current_file = file_path
            self.file_label.setText(Path(file_path).name)

    def _toggle_model(self):
        """切换模型开关。"""
        config.model_enabled = self.model_check.isChecked()
        self.model_check.setText("开" if config.model_enabled else "关")

    def _run_audit(self):
        """运行审计。"""
        if not hasattr(self, 'current_file'):
            QMessageBox.warning(self, "警告", "请先选择解答文件")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.result_view.clear()

        try:
            # 读取文件
            with open(self.current_file, 'r', encoding='utf-8') as f:
                solution_text = f.read()

            # 执行审计
            request = AuditRequest(
                solution_text=solution_text,
                final_assertion=self.assertion_input.text() or "",
                enable_model=config.model_enabled,
            )
            result = audit(request)

            # 显示结果
            self._display_result(result.report)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"审计失败: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)

    def _display_result(self, report):
        """显示审计结果。"""
        html = f"""
        <h2>审计报告</h2>
        <p><b>首错步骤:</b> {report.first_error.first_error}</p>
        <p><b>解释:</b> {report.first_error.explanation}</p>
        <p><b>独立重算:</b> {report.recalc_result}</p>
        <p><b>覆盖率:</b> {report.coverage.get('coverage', 0):.1%}</p>
        <hr>
        <h3>逐步骤判定</h3>
        <table border="1" cellpadding="5">
        <tr><th>步骤</th><th>状态</th><th>证据</th></tr>
        """
        for step, verdict in zip(report.steps, report.verdicts):
            html += f"""
            <tr>
                <td>{step.step_no}</td>
                <td>{verdict.status}</td>
                <td>{verdict.evidence}</td>
            </tr>
            """
        html += "</table>"
        self.result_view.setHtml(html)

    def _save_settings(self):
        """保存设置。"""
        config.model_endpoint = self.endpoint_input.text()
        config.model_provider = self.provider_input.text()
        config.model_timeout = self.timeout_input.value()
        QMessageBox.information(self, "信息", "设置已保存")


def run_gui():
    """启动 GUI。"""
    app = QApplication(sys.argv)
    window = AuditWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
