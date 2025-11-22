"""
測試資料集

包含各種格式的威脅情資文字，以及標註的正確答案。
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class TestCase:
    """測試案例"""
    name: str
    text: str
    expected_cve: List[str]
    expected_products: List[Dict[str, Any]]
    expected_ttps: List[str]
    expected_iocs: Dict[str, List[str]]
    source: str  # 資料來源（CISA KEV、NVD、TWCERT 等）


# CISA KEV 格式測試資料
CISA_KEV_TEST_CASES = [
    TestCase(
        name="CISA KEV - CVE-2024-12345",
        text="""
        CISA has added CVE-2024-12345 to the Known Exploited Vulnerabilities catalog.
        This vulnerability affects VMware ESXi 7.0.3 and earlier versions.
        Attackers are actively exploiting this vulnerability using phishing emails.
        Indicators of Compromise:
        - IP: 192.168.1.100
        - Domain: malicious.example.com
        - Hash: abc123def45678901234567890123456
        """,
        expected_cve=["CVE-2024-12345"],
        expected_products=[
            {"name": "VMware", "version": "7.0.3"},
        ],
        expected_ttps=["T1566.001"],
        expected_iocs={
            "ips": ["192.168.1.100"],
            "domains": ["malicious.example.com"],
            "hashes": ["abc123def45678901234567890123456"],
        },
        source="CISA KEV",
    ),
]

# NVD 格式測試資料
NVD_TEST_CASES = [
    TestCase(
        name="NVD - CVE-2024-67890",
        text="""
        CVE-2024-67890: Critical vulnerability in Windows Server 2022.
        CVSS Score: 9.8 (Critical)
        Affected versions: Windows Server 2022, SQL Server 2019
        Attack vector: Network
        Attack complexity: Low
        """,
        expected_cve=["CVE-2024-67890"],
        expected_products=[
            {"name": "Windows Server", "version": "2022"},
            {"name": "SQL Server", "version": "2019"},
        ],
        expected_ttps=[],
        expected_iocs={"ips": [], "domains": [], "hashes": []},
        source="NVD",
    ),
]

# TWCERT 格式測試資料（中文）
TWCERT_TEST_CASES = [
    TestCase(
        name="TWCERT - 中文威脅通報",
        text="""
        TWCERT 通報：發現針對 Windows Server 的 CVE-2024-11111 漏洞攻擊。
        攻擊者使用釣魚郵件（T1566.001）進行初始存取。
        受影響產品：Windows Server 2022、Apache 2.4.41
        惡意 IP：10.0.0.1、172.16.0.1
        惡意網域：attacker.com、malware.net
        """,
        expected_cve=["CVE-2024-11111"],
        expected_products=[
            {"name": "Windows Server", "version": "2022"},
            {"name": "Apache", "version": "2.4.41"},
        ],
        expected_ttps=["T1566.001"],
        expected_iocs={
            "ips": ["10.0.0.1", "172.16.0.1"],
            "domains": ["attacker.com", "malware.net"],
            "hashes": [],
        },
        source="TWCERT",
    ),
]

# VMware VMSA 格式測試資料
VMSA_TEST_CASES = [
    TestCase(
        name="VMware VMSA - ESXi Vulnerability",
        text="""
        VMware Security Advisory VMSA-2024-0001
        CVE-2024-22222 affects VMware ESXi 7.0.3 and vSphere 8.0
        This vulnerability allows remote code execution (T1059.001)
        Recommended action: Upgrade to ESXi 7.0.4 or later
        """,
        expected_cve=["CVE-2024-22222"],
        expected_products=[
            {"name": "VMware", "version": "7.0.3"},
            {"name": "VMware", "version": "8.0"},
        ],
        expected_ttps=["T1059.001"],
        expected_iocs={"ips": [], "domains": [], "hashes": []},
        source="VMware VMSA",
    ),
]

# MSRC 格式測試資料
MSRC_TEST_CASES = [
    TestCase(
        name="MSRC - Windows Server Vulnerability",
        text="""
        Microsoft Security Advisory for CVE-2024-33333
        Affected: Windows Server 2022, SQL Server 2019
        Severity: Critical
        Attackers use credential theft (T1078) to gain access
        """,
        expected_cve=["CVE-2024-33333"],
        expected_products=[
            {"name": "Windows Server", "version": "2022"},
            {"name": "SQL Server", "version": "2019"},
        ],
        expected_ttps=["T1078"],
        expected_iocs={"ips": [], "domains": [], "hashes": []},
        source="MSRC",
    ),
]

# 混合格式測試資料
MIXED_TEST_CASES = [
    TestCase(
        name="混合格式 - 多個 CVE 和產品",
        text="""
        Multiple vulnerabilities discovered:
        - CVE-2024-44444 affects MySQL 8.0.21
        - CVE-2024-55555 affects Apache 2.4.41
        Attack techniques: Phishing (T1566.001), Command Execution (T1059.001)
        IOCs: IP 192.168.1.1, Domain attacker.com, Hash def4567890123456789012345678901234567890123456789012345678901234
        """,
        expected_cve=["CVE-2024-44444", "CVE-2024-55555"],
        expected_products=[
            {"name": "MySQL", "version": "8.0.21"},
            {"name": "Apache", "version": "2.4.41"},
        ],
        expected_ttps=["T1566.001", "T1059.001"],
        expected_iocs={
            "ips": ["192.168.1.1"],
            "domains": ["attacker.com"],
            "hashes": ["def4567890123456789012345678901234567890123456789012345678901234"],
        },
        source="Mixed",
    ),
]

# 邊界情況測試資料
EDGE_CASE_TEST_CASES = [
    TestCase(
        name="邊界情況 - 無威脅資訊",
        text="This is a general security notice with no specific threats.",
        expected_cve=[],
        expected_products=[],
        expected_ttps=[],
        expected_iocs={"ips": [], "domains": [], "hashes": []},
        source="Edge Case",
    ),
    TestCase(
        name="邊界情況 - 僅 CVE",
        text="CVE-2024-99999",
        expected_cve=["CVE-2024-99999"],
        expected_products=[],
        expected_ttps=[],
        expected_iocs={"ips": [], "domains": [], "hashes": []},
        source="Edge Case",
    ),
    TestCase(
        name="邊界情況 - 小寫 CVE",
        text="cve-2024-88888 affects the system",
        expected_cve=["CVE-2024-88888"],
        expected_products=[],
        expected_ttps=[],
        expected_iocs={"ips": [], "domains": [], "hashes": []},
        source="Edge Case",
    ),
]

# 所有測試案例
ALL_TEST_CASES = (
    CISA_KEV_TEST_CASES +
    NVD_TEST_CASES +
    TWCERT_TEST_CASES +
    VMSA_TEST_CASES +
    MSRC_TEST_CASES +
    MIXED_TEST_CASES +
    EDGE_CASE_TEST_CASES
)

