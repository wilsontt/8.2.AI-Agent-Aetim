"""
準確度測試報告生成器

生成準確度測試報告，包含各提取器的準確度統計。
"""

from typing import Dict, List, Tuple
from app.services.extraction_service import ExtractionService
from tests.fixtures.test_data import ALL_TEST_CASES, TestCase


def calculate_accuracy_metrics(
    service: ExtractionService,
    test_cases: List[TestCase],
) -> Dict[str, Dict[str, float]]:
    """
    計算準確度指標
    
    Args:
        service: 提取服務
        test_cases: 測試案例列表
    
    Returns:
        Dict: 準確度指標字典
    """
    def _calculate_precision_recall(extracted: List[str], expected: List[str]) -> Tuple[float, float]:
        """計算精確度和召回率"""
        if not extracted and not expected:
            return 1.0, 1.0
        if not extracted:
            return 0.0, 0.0
        if not expected:
            return 0.0, 1.0
        
        extracted_set = set(extracted)
        expected_set = set(expected)
        intersection = extracted_set & expected_set
        
        precision = len(intersection) / len(extracted_set) if extracted_set else 0.0
        recall = len(intersection) / len(expected_set) if expected_set else 0.0
        
        return precision, recall
    
    def _calculate_f1_score(precision: float, recall: float) -> float:
        """計算 F1 分數"""
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
    
    results = {
        "cve": {"precision": [], "recall": []},
        "products": {"precision": [], "recall": []},
        "ttps": {"precision": [], "recall": []},
        "iocs": {"precision": [], "recall": []},
    }
    
    for test_case in test_cases:
        result = service.extract(test_case.text)
        
        # CVE
        if test_case.expected_cve:
            p, r = _calculate_precision_recall(result["cve"], test_case.expected_cve)
            results["cve"]["precision"].append(p)
            results["cve"]["recall"].append(r)
        
        # Products
        if test_case.expected_products:
            extracted_names = [
                f"{p['name']}:{p.get('version', '')}" for p in result["products"]
            ]
            expected_names = [
                f"{p['name']}:{p.get('version', '')}" for p in test_case.expected_products
            ]
            p, r = _calculate_precision_recall(extracted_names, expected_names)
            results["products"]["precision"].append(p)
            results["products"]["recall"].append(r)
        
        # TTPs
        if test_case.expected_ttps:
            p, r = _calculate_precision_recall(result["ttps"], test_case.expected_ttps)
            results["ttps"]["precision"].append(p)
            results["ttps"]["recall"].append(r)
        
        # IOCs
        has_expected_ioc = any(
            len(values) > 0 for values in test_case.expected_iocs.values()
        )
        if has_expected_ioc:
            extracted_all = []
            for ioc_type, values in result["iocs"].items():
                extracted_all.extend([f"{ioc_type}:{v}" for v in values])
            
            expected_all = []
            for ioc_type, values in test_case.expected_iocs.items():
                expected_all.extend([f"{ioc_type}:{v}" for v in values])
            
            p, r = _calculate_precision_recall(extracted_all, expected_all)
            results["iocs"]["precision"].append(p)
            results["iocs"]["recall"].append(r)
    
    # 計算平均指標
    metrics = {}
    for extractor_type, data in results.items():
        if data["precision"]:
            avg_precision = sum(data["precision"]) / len(data["precision"])
            avg_recall = sum(data["recall"]) / len(data["recall"])
            f1_score = _calculate_f1_score(avg_precision, avg_recall)
            
            metrics[extractor_type] = {
                "precision": avg_precision,
                "recall": avg_recall,
                "f1_score": f1_score,
                "test_count": len(data["precision"]),
            }
    
    return metrics


def generate_accuracy_report() -> str:
    """
    生成準確度測試報告
    
    Returns:
        str: 準確度測試報告（Markdown 格式）
    """
    service = ExtractionService()
    metrics = calculate_accuracy_metrics(service, ALL_TEST_CASES)
    
    report = "# AI 提取準確度測試報告\n\n"
    report += f"**測試日期**：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report += f"**測試案例總數**：{len(ALL_TEST_CASES)}\n\n"
    
    report += "## 準確度指標\n\n"
    report += "| 提取器類型 | 精確度 | 召回率 | F1 分數 | 測試案例數 | 目標 | 狀態 |\n"
    report += "|-----------|--------|--------|---------|-----------|------|------|\n"
    
    targets = {
        "cve": 0.95,
        "products": 0.80,
        "ttps": 0.85,
        "iocs": 0.90,
    }
    
    for extractor_type, target in targets.items():
        if extractor_type in metrics:
            m = metrics[extractor_type]
            status = "✅" if m["f1_score"] >= target else "❌"
            report += (
                f"| {extractor_type.upper()} | "
                f"{m['precision']:.2%} | "
                f"{m['recall']:.2%} | "
                f"{m['f1_score']:.2%} | "
                f"{m['test_count']} | "
                f"{target:.0%} | "
                f"{status} |\n"
            )
    
    report += "\n## 詳細說明\n\n"
    report += "- **精確度 (Precision)**：提取結果中正確的比例\n"
    report += "- **召回率 (Recall)**：預期結果中被正確提取的比例\n"
    report += "- **F1 分數**：精確度和召回率的調和平均數\n"
    
    return report


if __name__ == "__main__":
    report = generate_accuracy_report()
    print(report)

