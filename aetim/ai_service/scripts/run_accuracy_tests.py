"""
執行準確度測試腳本

執行準確度測試並生成報告。
"""

import sys
import os

# 加入專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.accuracy.accuracy_report import generate_accuracy_report


def main():
    """主函數"""
    print("開始執行準確度測試...\n")
    
    report = generate_accuracy_report()
    print(report)
    
    # 儲存報告到檔案
    report_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "accuracy_report.md"
    )
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n✅ 準確度測試報告已儲存至：{report_file}")


if __name__ == "__main__":
    main()

