"""
追蹤功能單元測試
"""

import pytest
from shared_kernel.infrastructure.tracing import (
    generate_trace_id,
    get_trace_id,
    trace_id_var,
)


@pytest.mark.unit
def test_generate_trace_id():
    """測試追蹤 ID 生成"""
    trace_id = generate_trace_id()
    
    assert trace_id is not None
    assert isinstance(trace_id, str)
    assert len(trace_id) == 36  # UUID 格式長度


@pytest.mark.unit
def test_get_trace_id():
    """測試取得追蹤 ID"""
    # 初始狀態應該為 None
    assert get_trace_id() is None
    
    # 設定追蹤 ID
    test_id = "test-trace-id"
    trace_id_var.set(test_id)
    
    # 驗證取得正確的追蹤 ID
    assert get_trace_id() == test_id

