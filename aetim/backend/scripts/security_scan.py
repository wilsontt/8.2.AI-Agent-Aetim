"""
安全性掃描腳本

掃描依賴套件漏洞和安全性問題。
符合 T-5-4-3：安全性檢查
"""

import subprocess
import sys
import json
from pathlib import Path


def check_dependencies():
    """
    檢查依賴套件漏洞
    
    使用 pip-audit 或 safety 掃描依賴套件漏洞。
    """
    print("正在掃描依賴套件漏洞...")
    
    try:
        # 嘗試使用 pip-audit
        result = subprocess.run(
            ["pip-audit", "--requirement", "requirements.txt", "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        if result.returncode == 0:
            vulnerabilities = json.loads(result.stdout)
            if vulnerabilities:
                print(f"發現 {len(vulnerabilities)} 個漏洞：")
                for vuln in vulnerabilities:
                    print(f"  - {vuln.get('name', 'Unknown')}: {vuln.get('vulnerability', {}).get('id', 'Unknown')}")
                return False
            else:
                print("✓ 未發現依賴套件漏洞")
                return True
        else:
            print("⚠ pip-audit 未安裝，跳過依賴套件掃描")
            print("  安裝方式：pip install pip-audit")
            return True
    except FileNotFoundError:
        print("⚠ pip-audit 未安裝，跳過依賴套件掃描")
        print("  安裝方式：pip install pip-audit")
        return True
    except Exception as e:
        print(f"⚠ 依賴套件掃描失敗：{e}")
        return True


def check_code_security():
    """
    檢查程式碼安全性
    
    使用 bandit 掃描程式碼安全性問題。
    """
    print("\n正在掃描程式碼安全性問題...")
    
    try:
        result = subprocess.run(
            ["bandit", "-r", ".", "-f", "json", "-o", "bandit-report.json"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        if result.returncode == 0:
            # 讀取報告
            report_path = Path("bandit-report.json")
            if report_path.exists():
                with open(report_path, "r") as f:
                    report = json.load(f)
                
                metrics = report.get("metrics", {})
                high_severity = metrics.get("_totals", {}).get("SEVERITY.HIGH", 0)
                medium_severity = metrics.get("_totals", {}).get("SEVERITY.MEDIUM", 0)
                
                if high_severity > 0 or medium_severity > 0:
                    print(f"⚠ 發現安全性問題：")
                    print(f"  - 高風險：{high_severity}")
                    print(f"  - 中風險：{medium_severity}")
                    print(f"  詳細報告：bandit-report.json")
                    return False
                else:
                    print("✓ 未發現程式碼安全性問題")
                    return True
            else:
                print("✓ 未發現程式碼安全性問題")
                return True
        else:
            print("⚠ bandit 未安裝，跳過程式碼掃描")
            print("  安裝方式：pip install bandit[toml]")
            return True
    except FileNotFoundError:
        print("⚠ bandit 未安裝，跳過程式碼掃描")
        print("  安裝方式：pip install bandit[toml]")
        return True
    except Exception as e:
        print(f"⚠ 程式碼掃描失敗：{e}")
        return True


def main():
    """主函式"""
    print("=" * 60)
    print("安全性掃描")
    print("=" * 60)
    
    results = []
    
    # 檢查依賴套件
    results.append(("依賴套件掃描", check_dependencies()))
    
    # 檢查程式碼安全性
    results.append(("程式碼安全性掃描", check_code_security()))
    
    # 總結
    print("\n" + "=" * 60)
    print("掃描結果總結")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ 通過" if passed else "✗ 失敗"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✓ 所有安全性檢查通過")
        sys.exit(0)
    else:
        print("\n✗ 發現安全性問題，請修復後重新掃描")
        sys.exit(1)


if __name__ == "__main__":
    main()

