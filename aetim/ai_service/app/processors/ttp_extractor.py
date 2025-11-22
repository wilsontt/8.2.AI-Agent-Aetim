"""
TTPs 提取器

從文字內容中提取 TTPs（Tactics, Techniques, and Procedures）。
符合 AC-009-3 要求：識別 TTPs（戰術、技術和程序）。
"""

from typing import List, Set, Dict


class TTPExtractor:
    """
    TTPs 提取器
    
    使用關鍵字匹配從文字中提取 MITRE ATT&CK TTP ID。
    """
    
    # MITRE ATT&CK TTP 關鍵字對應表
    # 格式：TTP ID -> 關鍵字列表（中英文）
    TTP_KEYWORDS: Dict[str, List[str]] = {
        # Initial Access（初始存取）
        "T1566.001": [
            "釣魚", "phishing", "email phishing", "spear phishing",
            "魚叉式釣魚", "社交工程", "social engineering",
        ],
        "T1566.002": [
            "釣魚連結", "phishing link", "惡意連結", "malicious link",
        ],
        "T1078": [
            "帳號存取", "account access", "credential", "憑證",
            "帳號盜用", "account compromise",
        ],
        "T1190": [
            "公開應用程式漏洞", "public-facing application",
            "對外服務漏洞", "remote exploit",
        ],
        
        # Execution（執行）
        "T1059.001": [
            "命令執行", "command execution", "powershell", "PowerShell",
            "命令列", "command line", "cmd",
        ],
        "T1059.003": [
            "Windows 命令", "windows command", "cmd.exe",
        ],
        "T1059.005": [
            "Visual Basic", "VBScript", "VBS",
        ],
        "T1203": [
            "利用應用程式", "exploit application", "應用程式漏洞利用",
        ],
        
        # Persistence（持久化）
        "T1547.001": [
            "開機啟動", "boot startup", "啟動項", "startup item",
        ],
        "T1543.003": [
            "Windows 服務", "windows service", "服務建立",
        ],
        "T1053.005": [
            "排程任務", "scheduled task", "工作排程", "task scheduler",
        ],
        
        # Privilege Escalation（權限提升）
        "T1548.002": [
            "繞過 UAC", "bypass UAC", "UAC bypass",
        ],
        "T1078.001": [
            "本機帳號", "local account", "本機使用者",
        ],
        "T1547.001": [
            "開機或登入自動啟動", "boot or logon autostart",
        ],
        
        # Defense Evasion（防禦規避）
        "T1562.001": [
            "停用安全工具", "disable security tool", "關閉防毒",
        ],
        "T1070.004": [
            "刪除檔案", "delete file", "檔案刪除",
        ],
        "T1027": [
            "混淆檔案或資訊", "obfuscate", "混淆", "編碼",
        ],
        
        # Credential Access（憑證存取）
        "T1003.001": [
            "LSASS 記憶體", "LSASS memory", "憑證傾印",
        ],
        "T1555.003": [
            "憑證儲存", "credential store", "密碼儲存",
        ],
        "T1110.001": [
            "暴力破解", "brute force", "密碼猜測",
        ],
        
        # Discovery（探索）
        "T1083": [
            "檔案和目錄探索", "file and directory discovery",
        ],
        "T1018": [
            "遠端系統探索", "remote system discovery",
        ],
        "T1082": [
            "系統資訊探索", "system information discovery",
        ],
        
        # Lateral Movement（橫向移動）
        "T1021.001": [
            "遠端桌面協定", "RDP", "remote desktop",
        ],
        "T1021.002": [
            "SMB/Windows 管理共用", "SMB", "windows admin share",
        ],
        "T1071.001": [
            "應用程式層協定", "application layer protocol",
        ],
        
        # Collection（收集）
        "T1005": [
            "本機資料收集", "local data collection",
        ],
        "T1039": [
            "網路共用資料收集", "network share data collection",
        ],
        "T1114.001": [
            "本地電子郵件收集", "local email collection",
        ],
        
        # Command and Control（命令與控制）
        "T1071.001": [
            "Web 協定", "web protocol", "HTTP", "HTTPS",
        ],
        "T1105": [
            "傳入工具", "ingress tool transfer",
        ],
        "T1573.002": [
            "加密通道", "encrypted channel", "TLS",
        ],
        
        # Exfiltration（外洩）
        "T1041": [
            "資料外洩", "exfiltration", "資料傳輸",
        ],
        "T1567.002": [
            "雲端儲存外洩", "cloud storage exfiltration",
        ],
        
        # Impact（影響）
        "T1486": [
            "資料加密", "data encrypted", "勒索軟體", "ransomware",
        ],
        "T1499.004": [
            "服務停止", "service stop", "服務中斷",
        ],
    }
    
    def extract(self, text: str) -> List[str]:
        """
        提取 TTPs
        
        從文字中提取 MITRE ATT&CK TTP ID。
        
        Args:
            text: 要提取的文字內容
        
        Returns:
            List[str]: TTP ID 列表（已去重）
        
        Examples:
            >>> extractor = TTPExtractor()
            >>> extractor.extract("This is a phishing attack")
            ['T1566.001']
            >>> extractor.extract("Command execution via PowerShell")
            ['T1059.001']
        """
        if not text or not isinstance(text, str):
            return []
        
        text_lower = text.lower()
        ttps: Set[str] = set()
        
        # 遍歷所有 TTP 關鍵字對應
        for ttp_id, keywords in self.TTP_KEYWORDS.items():
            # 檢查文字中是否包含任何關鍵字
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    ttps.add(ttp_id)
                    break  # 找到一個關鍵字即可，不需要繼續檢查
        
        # 轉換為排序後的列表
        return sorted(list(ttps))
    
    def get_ttp_info(self, ttp_id: str) -> Dict[str, any]:
        """
        取得 TTP 資訊
        
        Args:
            ttp_id: TTP ID（例如：T1566.001）
        
        Returns:
            Dict: TTP 資訊（包含 ID 和關鍵字列表）
        """
        if ttp_id in self.TTP_KEYWORDS:
            return {
                "id": ttp_id,
                "keywords": self.TTP_KEYWORDS[ttp_id],
            }
        return {"id": ttp_id, "keywords": []}

