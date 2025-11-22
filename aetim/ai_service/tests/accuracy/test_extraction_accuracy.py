"""
AI 提取準確度測試

測試各種提取器的準確度，確保達到目標準確度要求。
"""

import pytest
from typing import Tuple
from app.services.extraction_service import ExtractionService
from tests.fixtures.test_data import ALL_TEST_CASES, TestCase


class TestExtractionAccuracy:
    """AI 提取準確度測試"""
    
    @pytest.fixture
    def service(self):
        """建立 ExtractionService 實例"""
        return ExtractionService()
    
    def _calculate_precision_recall(
        self,
        extracted: List[str],
        expected: List[str],
    ) -> Tuple[float, float]:
        """
        計算精確度和召回率
        
        Args:
            extracted: 提取的結果列表
            expected: 預期的結果列表
        
        Returns:
            tuple[float, float]: (精確度, 召回率)
        """
        if not extracted and not expected:
            return 1.0, 1.0
        
        if not extracted:
            return 0.0, 0.0
        
        if not expected:
            return 0.0, 1.0
        
        # 轉換為集合以便比較
        extracted_set = set(extracted)
        expected_set = set(expected)
        
        # 計算交集
        intersection = extracted_set & expected_set
        
        # 精確度 = 正確提取的數量 / 總提取數量
        precision = len(intersection) / len(extracted_set) if extracted_set else 0.0
        
        # 召回率 = 正確提取的數量 / 總預期數量
        recall = len(intersection) / len(expected_set) if expected_set else 0.0
        
        return precision, recall
    
    def _calculate_f1_score(self, precision: float, recall: float) -> float:
        """
        計算 F1 分數
        
        Args:
            precision: 精確度
            recall: 召回率
        
        Returns:
            float: F1 分數
        """
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
    
    def _test_cve_accuracy(self, service: ExtractionService, test_case: TestCase) -> Tuple[float, float]:
        """測試 CVE 提取準確度"""
        result = service.extract(test_case.text)
        extracted_cve = result["cve"]
        expected_cve = test_case.expected_cve
        
        precision, recall = self._calculate_precision_recall(extracted_cve, expected_cve)
        
        return precision, recall
    
    def _test_product_accuracy(self, service: ExtractionService, test_case: TestCase) -> Tuple[float, float]:
        """測試產品提取準確度"""
        result = service.extract(test_case.text)
        extracted_products = result["products"]
        expected_products = test_case.expected_products
        
        # 轉換為可比較的格式
        extracted_names = [
            f"{p['name']}:{p.get('version', '')}" for p in extracted_products
        ]
        expected_names = [
            f"{p['name']}:{p.get('version', '')}" for p in expected_products
        ]
        
        precision, recall = self._calculate_precision_recall(extracted_names, expected_names)
        
        return precision, recall
    
    def _test_ttp_accuracy(self, service: ExtractionService, test_case: TestCase) -> Tuple[float, float]:
        """測試 TTP 提取準確度"""
        result = service.extract(test_case.text)
        extracted_ttps = result["ttps"]
        expected_ttps = test_case.expected_ttps
        
        precision, recall = self._calculate_precision_recall(extracted_ttps, expected_ttps)
        
        return precision, recall
    
    def _test_ioc_accuracy(self, service: ExtractionService, test_case: TestCase) -> Tuple[float, float]:
        """測試 IOC 提取準確度"""
        result = service.extract(test_case.text)
        extracted_iocs = result["iocs"]
        expected_iocs = test_case.expected_iocs
        
        # 合併所有 IOC 類型
        extracted_all = []
        for ioc_type, values in extracted_iocs.items():
            extracted_all.extend([f"{ioc_type}:{v}" for v in values])
        
        expected_all = []
        for ioc_type, values in expected_iocs.items():
            expected_all.extend([f"{ioc_type}:{v}" for v in values])
        
        precision, recall = self._calculate_precision_recall(extracted_all, expected_all)
        
        return precision, recall
    
    def test_cve_extraction_accuracy(self, service):
        """測試 CVE 提取準確度（目標 ≥ 95%）"""
        total_precision = 0.0
        total_recall = 0.0
        count = 0
        
        for test_case in ALL_TEST_CASES:
            if test_case.expected_cve:  # 只測試有預期 CVE 的案例
                precision, recall = self._test_cve_accuracy(service, test_case)
                total_precision += precision
                total_recall += recall
                count += 1
        
        if count > 0:
            avg_precision = total_precision / count
            avg_recall = total_recall / count
            f1_score = self._calculate_f1_score(avg_precision, avg_recall)
            
            print(f"\nCVE 提取準確度：")
            print(f"  平均精確度：{avg_precision:.2%}")
            print(f"  平均召回率：{avg_recall:.2%}")
            print(f"  F1 分數：{f1_score:.2%}")
            
            # 使用 F1 分數作為準確度指標（目標 ≥ 95%）
            assert f1_score >= 0.95, f"CVE 提取準確度 {f1_score:.2%} 低於目標 95%"
    
    def test_product_extraction_accuracy(self, service):
        """測試產品提取準確度（目標 ≥ 80%）"""
        total_precision = 0.0
        total_recall = 0.0
        count = 0
        
        for test_case in ALL_TEST_CASES:
            if test_case.expected_products:  # 只測試有預期產品的案例
                precision, recall = self._test_product_accuracy(service, test_case)
                total_precision += precision
                total_recall += recall
                count += 1
        
        if count > 0:
            avg_precision = total_precision / count
            avg_recall = total_recall / count
            f1_score = self._calculate_f1_score(avg_precision, avg_recall)
            
            print(f"\n產品提取準確度：")
            print(f"  平均精確度：{avg_precision:.2%}")
            print(f"  平均召回率：{avg_recall:.2%}")
            print(f"  F1 分數：{f1_score:.2%}")
            
            # 使用 F1 分數作為準確度指標（目標 ≥ 80%）
            assert f1_score >= 0.80, f"產品提取準確度 {f1_score:.2%} 低於目標 80%"
    
    def test_ttp_extraction_accuracy(self, service):
        """測試 TTP 提取準確度（目標 ≥ 85%）"""
        total_precision = 0.0
        total_recall = 0.0
        count = 0
        
        for test_case in ALL_TEST_CASES:
            if test_case.expected_ttps:  # 只測試有預期 TTP 的案例
                precision, recall = self._test_ttp_accuracy(service, test_case)
                total_precision += precision
                total_recall += recall
                count += 1
        
        if count > 0:
            avg_precision = total_precision / count
            avg_recall = total_recall / count
            f1_score = self._calculate_f1_score(avg_precision, avg_recall)
            
            print(f"\nTTP 提取準確度：")
            print(f"  平均精確度：{avg_precision:.2%}")
            print(f"  平均召回率：{avg_recall:.2%}")
            print(f"  F1 分數：{f1_score:.2%}")
            
            # 使用 F1 分數作為準確度指標（目標 ≥ 85%）
            assert f1_score >= 0.85, f"TTP 提取準確度 {f1_score:.2%} 低於目標 85%"
    
    def test_ioc_extraction_accuracy(self, service):
        """測試 IOC 提取準確度（目標 ≥ 90%）"""
        total_precision = 0.0
        total_recall = 0.0
        count = 0
        
        for test_case in ALL_TEST_CASES:
            # 檢查是否有預期 IOC
            has_expected_ioc = any(
                len(values) > 0 for values in test_case.expected_iocs.values()
            )
            
            if has_expected_ioc:
                precision, recall = self._test_ioc_accuracy(service, test_case)
                total_precision += precision
                total_recall += recall
                count += 1
        
        if count > 0:
            avg_precision = total_precision / count
            avg_recall = total_recall / count
            f1_score = self._calculate_f1_score(avg_precision, avg_recall)
            
            print(f"\nIOC 提取準確度：")
            print(f"  平均精確度：{avg_precision:.2%}")
            print(f"  平均召回率：{avg_recall:.2%}")
            print(f"  F1 分數：{f1_score:.2%}")
            
            # 使用 F1 分數作為準確度指標（目標 ≥ 90%）
            assert f1_score >= 0.90, f"IOC 提取準確度 {f1_score:.2%} 低於目標 90%"
    
    def test_overall_accuracy(self, service):
        """測試整體提取準確度"""
        results = {
            "cve": {"precision": [], "recall": []},
            "products": {"precision": [], "recall": []},
            "ttps": {"precision": [], "recall": []},
            "iocs": {"precision": [], "recall": []},
        }
        
        for test_case in ALL_TEST_CASES:
            # CVE
            if test_case.expected_cve:
                p, r = self._test_cve_accuracy(service, test_case)
                results["cve"]["precision"].append(p)
                results["cve"]["recall"].append(r)
            
            # Products
            if test_case.expected_products:
                p, r = self._test_product_accuracy(service, test_case)
                results["products"]["precision"].append(p)
                results["products"]["recall"].append(r)
            
            # TTPs
            if test_case.expected_ttps:
                p, r = self._test_ttp_accuracy(service, test_case)
                results["ttps"]["precision"].append(p)
                results["ttps"]["recall"].append(r)
            
            # IOCs
            has_expected_ioc = any(
                len(values) > 0 for values in test_case.expected_iocs.values()
            )
            if has_expected_ioc:
                p, r = self._test_ioc_accuracy(service, test_case)
                results["iocs"]["precision"].append(p)
                results["iocs"]["recall"].append(r)
        
        # 計算平均準確度
        print("\n=== 整體提取準確度報告 ===")
        for extractor_type, metrics in results.items():
            if metrics["precision"]:
                avg_precision = sum(metrics["precision"]) / len(metrics["precision"])
                avg_recall = sum(metrics["recall"]) / len(metrics["recall"])
                f1_score = self._calculate_f1_score(avg_precision, avg_recall)
                
                print(f"\n{extractor_type.upper()}:")
                print(f"  平均精確度：{avg_precision:.2%}")
                print(f"  平均召回率：{avg_recall:.2%}")
                print(f"  F1 分數：{f1_score:.2%}")

