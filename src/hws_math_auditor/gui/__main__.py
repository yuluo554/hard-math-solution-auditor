"""GUI 入口 — 绝对导入薄模块（PyInstaller 构建安全）。

窗口 exe 纪律：对未知参数必须**报错退出 2**，不得静默忽略——
静默忽略会挂进 Qt 事件循环永不返回，验收从"失败"退化成"卡住"。
"""

import sys


def main(argv=None) -> int:
    """GUI 主入口。"""
    argv = list(sys.argv[1:] if argv is None else argv)

    if argv:
        # 支持 --selftest 做无窗口冒烟（冻结态验收用）
        if argv == ["--selftest"]:
            from hws_math_auditor.pipeline import selftest

            print("自检通过" if selftest() else "自检失败")
            return 0 if selftest() else 1

        print(f"错误: 未知参数 {argv}（本程序不接受命令行参数）", file=sys.stderr)
        return 2

    from hws_math_auditor.gui import run_gui

    run_gui()
    return 0


if __name__ == "__main__":
    sys.exit(main())
