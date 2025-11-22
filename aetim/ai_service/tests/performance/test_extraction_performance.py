"""
AI 提取效能測試

測試 AI 提取服務的效能，包括處理時間、並發處理、資源使用量等。
"""

import pytest
import time
import psutil
import os
from app.services.extraction_service import ExtractionService
from tests.fixtures.test_data import ALL_TEST_CASES


class TestExtractionPerformance:
    """AI 提取效能測試"""
    
    @pytest.fixture
    def service(self):
        """建立 ExtractionService 實例"""
        return ExtractionService()
    
    def test_single_request_processing_time(self, service):
        """測試單一請求處理時間（目標 ≤ 5 秒）"""
        test_text = """
        CVE-2024-12345 affects VMware ESXi 7.0.3.
        This is a phishing attack using IP 192.168.1.1 and domain malicious.com.
        """
        
        start_time = time.time()
        result = service.extract(test_text)
        processing_time = time.time() - start_time
        
        print(f"\n單一請求處理時間：{processing_time:.3f} 秒")
        
        assert processing_time <= 5.0, f"處理時間 {processing_time:.3f} 秒超過目標 5 秒"
        assert result is not None
    
    def test_multiple_requests_processing_time(self, service):
        """測試多個請求的平均處理時間"""
        processing_times = []
        
        for test_case in ALL_TEST_CASES[:10]:  # 測試前 10 個案例
            start_time = time.time()
            result = service.extract(test_case.text)
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
        
        avg_time = sum(processing_times) / len(processing_times)
        max_time = max(processing_times)
        
        print(f"\n多個請求處理時間：")
        print(f"  平均處理時間：{avg_time:.3f} 秒")
        print(f"  最大處理時間：{max_time:.3f} 秒")
        
        assert avg_time <= 5.0, f"平均處理時間 {avg_time:.3f} 秒超過目標 5 秒"
        assert max_time <= 10.0, f"最大處理時間 {max_time:.3f} 秒超過目標 10 秒"
    
    def test_large_text_processing_time(self, service):
        """測試大文字內容的處理時間"""
        # 建立大文字內容（重複測試案例）
        large_text = "\n\n".join([test_case.text for test_case in ALL_TEST_CASES] * 3)
        
        start_time = time.time()
        result = service.extract(large_text)
        processing_time = time.time() - start_time
        
        print(f"\n大文字內容處理時間：{processing_time:.3f} 秒")
        print(f"  文字長度：{len(large_text)} 字元")
        
        # 大文字內容的處理時間可以稍微放寬
        assert processing_time <= 10.0, f"大文字處理時間 {processing_time:.3f} 秒超過目標 10 秒"
        assert result is not None
    
    def test_memory_usage(self, service):
        """測試記憶體使用量"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 執行多次提取
        for test_case in ALL_TEST_CASES[:10]:
            service.extract(test_case.text)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"\n記憶體使用量：")
        print(f"  初始記憶體：{initial_memory:.2f} MB")
        print(f"  最終記憶體：{final_memory:.2f} MB")
        print(f"  記憶體增加：{memory_increase:.2f} MB")
        
        # 記憶體增加應在合理範圍內（< 500 MB）
        assert memory_increase < 500, f"記憶體增加 {memory_increase:.2f} MB 超過合理範圍"
    
    def test_cpu_usage(self, service):
        """測試 CPU 使用量"""
        process = psutil.Process(os.getpid())
        
        # 執行提取並監控 CPU
        cpu_percentages = []
        for test_case in ALL_TEST_CASES[:5]:
            cpu_percent = process.cpu_percent(interval=0.1)
            service.extract(test_case.text)
            cpu_percentages.append(cpu_percent)
        
        avg_cpu = sum(cpu_percentages) / len(cpu_percentages) if cpu_percentages else 0
        
        print(f"\nCPU 使用量：")
        print(f"  平均 CPU 使用率：{avg_cpu:.2f}%")
        
        # CPU 使用率應在合理範圍內（< 100%，考慮多核心）
        assert avg_cpu < 100, f"平均 CPU 使用率 {avg_cpu:.2f}% 超過合理範圍"
    
    def test_concurrent_requests(self, service):
        """測試並發請求處理"""
        import concurrent.futures
        
        test_texts = [test_case.text for test_case in ALL_TEST_CASES[:5]]
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(service.extract, text) for text in test_texts]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        print(f"\n並發請求處理：")
        print(f"  請求數量：{len(test_texts)}")
        print(f"  總處理時間：{total_time:.3f} 秒")
        print(f"  平均處理時間：{total_time / len(test_texts):.3f} 秒")
        
        assert len(results) == len(test_texts)
        assert all(result is not None for result in results)
    
    def test_empty_text_performance(self, service):
        """測試空文字的處理時間"""
        start_time = time.time()
        result = service.extract("")
        processing_time = time.time() - start_time
        
        print(f"\n空文字處理時間：{processing_time:.3f} 秒")
        
        # 空文字應快速處理（< 0.1 秒）
        assert processing_time < 0.1, f"空文字處理時間 {processing_time:.3f} 秒超過目標 0.1 秒"
        assert result is not None

