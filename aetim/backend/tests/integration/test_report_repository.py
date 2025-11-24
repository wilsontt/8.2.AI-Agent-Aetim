"""
報告 Repository 整合測試

測試報告儲存與查詢功能。
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from reporting_notification.domain.aggregates.report import Report
from reporting_notification.domain.value_objects.report_type import ReportType
from reporting_notification.domain.value_objects.file_format import FileFormat
from reporting_notification.infrastructure.persistence.report_repository import (
    ReportRepository,
)
from reporting_notification.infrastructure.persistence.models import Report as ReportModel


@pytest.fixture
def temp_reports_dir():
    """建立臨時報告目錄"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def report_repository(db_session: AsyncSession, temp_reports_dir):
    """建立報告 Repository"""
    return ReportRepository(session=db_session, reports_base_path=temp_reports_dir)


@pytest.mark.asyncio
async def test_save_report(report_repository: ReportRepository):
    """測試儲存報告"""
    # 建立報告
    report = Report.create(
        report_type=ReportType.CISO_WEEKLY,
        title="CISO Weekly Report 2025-01-27",
        file_path="",  # 將由 repository 設定
        file_format=FileFormat.HTML,
        period_start=datetime(2025, 1, 20),
        period_end=datetime(2025, 1, 27),
        summary="本週發現 10 個嚴重威脅",
    )
    
    # 準備檔案內容
    file_content = b"<html><body><h1>CISO Weekly Report</h1></body></html>"
    
    # 儲存報告
    await report_repository.save(report, file_content)
    
    # 驗證報告已儲存到資料庫
    saved_report = await report_repository.get_by_id(report.id)
    assert saved_report is not None
    assert saved_report.id == report.id
    assert saved_report.title == report.title
    assert saved_report.report_type == ReportType.CISO_WEEKLY
    assert saved_report.file_format == FileFormat.HTML
    
    # 驗證檔案已儲存
    file_path = await report_repository.get_file_path(report.id)
    assert file_path is not None
    assert Path(file_path).exists()
    
    # 驗證目錄結構（AC-015-5）
    assert "2025" in file_path
    assert "202501" in file_path
    
    # 驗證檔案命名格式（AC-015-6）
    assert "CISO_Weekly_Report_2025-01-27.html" in file_path


@pytest.mark.asyncio
async def test_get_by_id(report_repository: ReportRepository):
    """測試依 ID 查詢報告"""
    # 建立並儲存報告
    report = Report.create(
        report_type=ReportType.CISO_WEEKLY,
        title="Test Report",
        file_path="",
        file_format=FileFormat.PDF,
    )
    
    file_content = b"PDF content"
    await report_repository.save(report, file_content)
    
    # 查詢報告
    found_report = await report_repository.get_by_id(report.id)
    
    assert found_report is not None
    assert found_report.id == report.id
    assert found_report.title == report.title


@pytest.mark.asyncio
async def test_get_by_id_not_found(report_repository: ReportRepository):
    """測試查詢不存在的報告"""
    found_report = await report_repository.get_by_id("non-existent-id")
    assert found_report is None


@pytest.mark.asyncio
async def test_get_all_with_pagination(report_repository: ReportRepository):
    """測試查詢所有報告（分頁）"""
    # 建立多個報告
    for i in range(5):
        report = Report.create(
            report_type=ReportType.CISO_WEEKLY,
            title=f"Report {i}",
            file_path="",
            file_format=FileFormat.HTML,
            generated_at=datetime(2025, 1, 27, hour=i),
        )
        await report_repository.save(report, b"content")
    
    # 查詢第一頁
    result = await report_repository.get_all(page=1, page_size=2)
    
    assert result["total"] == 5
    assert result["page"] == 1
    assert result["page_size"] == 2
    assert result["total_pages"] == 3
    assert len(result["items"]) == 2


@pytest.mark.asyncio
async def test_get_all_with_filter_by_type(report_repository: ReportRepository):
    """測試依報告類型篩選"""
    # 建立不同類型的報告
    ciso_report = Report.create(
        report_type=ReportType.CISO_WEEKLY,
        title="CISO Report",
        file_path="",
        file_format=FileFormat.HTML,
    )
    await report_repository.save(ciso_report, b"content")
    
    ticket_report = Report.create(
        report_type=ReportType.IT_TICKET,
        title="IT Ticket",
        file_path="",
        file_format=FileFormat.JSON,
    )
    await report_repository.save(ticket_report, b"content")
    
    # 查詢 CISO 週報
    result = await report_repository.get_all(report_type=ReportType.CISO_WEEKLY)
    
    assert result["total"] == 1
    assert result["items"][0].report_type == ReportType.CISO_WEEKLY


@pytest.mark.asyncio
async def test_get_all_with_filter_by_date(report_repository: ReportRepository):
    """測試依日期篩選"""
    # 建立不同日期的報告
    report1 = Report.create(
        report_type=ReportType.CISO_WEEKLY,
        title="Report 1",
        file_path="",
        file_format=FileFormat.HTML,
        generated_at=datetime(2025, 1, 20),
    )
    await report_repository.save(report1, b"content")
    
    report2 = Report.create(
        report_type=ReportType.CISO_WEEKLY,
        title="Report 2",
        file_path="",
        file_format=FileFormat.HTML,
        generated_at=datetime(2025, 1, 27),
    )
    await report_repository.save(report2, b"content")
    
    # 查詢 2025-01-25 之後的報告
    result = await report_repository.get_all(
        start_date=datetime(2025, 1, 25)
    )
    
    assert result["total"] == 1
    assert result["items"][0].id == report2.id


@pytest.mark.asyncio
async def test_get_file_path(report_repository: ReportRepository):
    """測試取得檔案路徑"""
    report = Report.create(
        report_type=ReportType.CISO_WEEKLY,
        title="Test Report",
        file_path="",
        file_format=FileFormat.HTML,
    )
    
    file_content = b"<html><body>Test</body></html>"
    await report_repository.save(report, file_content)
    
    file_path = await report_repository.get_file_path(report.id)
    
    assert file_path is not None
    assert Path(file_path).exists()


@pytest.mark.asyncio
async def test_get_file_content(report_repository: ReportRepository):
    """測試取得檔案內容"""
    report = Report.create(
        report_type=ReportType.CISO_WEEKLY,
        title="Test Report",
        file_path="",
        file_format=FileFormat.TEXT,
    )
    
    file_content = b"Test report content"
    await report_repository.save(report, file_content)
    
    retrieved_content = await report_repository.get_file_content(report.id)
    
    assert retrieved_content == file_content


@pytest.mark.asyncio
async def test_directory_structure(report_repository: ReportRepository, temp_reports_dir):
    """測試目錄結構（AC-015-5）"""
    # 建立不同月份的報告
    report1 = Report.create(
        report_type=ReportType.CISO_WEEKLY,
        title="January Report",
        file_path="",
        file_format=FileFormat.HTML,
        generated_at=datetime(2025, 1, 15),
    )
    await report_repository.save(report1, b"content")
    
    report2 = Report.create(
        report_type=ReportType.CISO_WEEKLY,
        title="February Report",
        file_path="",
        file_format=FileFormat.HTML,
        generated_at=datetime(2025, 2, 15),
    )
    await report_repository.save(report2, b"content")
    
    # 驗證目錄結構
    base_path = Path(temp_reports_dir)
    assert (base_path / "2025" / "202501").exists()
    assert (base_path / "2025" / "202502").exists()


@pytest.mark.asyncio
async def test_file_naming_format(report_repository: ReportRepository):
    """測試檔案命名格式（AC-015-6）"""
    report = Report.create(
        report_type=ReportType.CISO_WEEKLY,
        title="CISO Weekly Report 2025-01-27",
        file_path="",
        file_format=FileFormat.HTML,
        generated_at=datetime(2025, 1, 27),
    )
    
    await report_repository.save(report, b"content")
    
    file_path = await report_repository.get_file_path(report.id)
    
    # 驗證檔案命名格式
    assert "CISO_Weekly_Report_2025-01-27.html" in file_path


@pytest.mark.asyncio
async def test_save_with_metadata(report_repository: ReportRepository):
    """測試儲存帶有元資料的報告"""
    metadata = {
        "threat_count": 10,
        "critical_threats": 3,
        "affected_assets": 25,
    }
    
    report = Report.create(
        report_type=ReportType.CISO_WEEKLY,
        title="Test Report",
        file_path="",
        file_format=FileFormat.HTML,
        metadata=metadata,
    )
    
    await report_repository.save(report, b"content")
    
    saved_report = await report_repository.get_by_id(report.id)
    assert saved_report.metadata == metadata


@pytest.mark.asyncio
async def test_save_with_summary(report_repository: ReportRepository):
    """測試儲存帶有摘要的報告"""
    summary = "本週發現 10 個嚴重威脅，建議立即處理。"
    
    report = Report.create(
        report_type=ReportType.CISO_WEEKLY,
        title="Test Report",
        file_path="",
        file_format=FileFormat.HTML,
        summary=summary,
    )
    
    await report_repository.save(report, b"content")
    
    saved_report = await report_repository.get_by_id(report.id)
    assert saved_report.summary == summary

