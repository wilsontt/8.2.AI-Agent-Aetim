"""
資產匯入服務

提供 CSV 檔案匯入功能。
"""

import csv
import io
from typing import List, Dict, Optional
from ..services.asset_service import AssetService
from ..dtos.asset_dto import CreateAssetRequest, ImportPreviewResponse, ImportResultResponse
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class AssetImportService:
    """
    資產匯入服務
    
    提供 CSV 檔案匯入功能，包含解析、驗證、預覽和匯入。
    """
    
    # CSV 必要欄位
    REQUIRED_COLUMNS = [
        "主機名稱",
        "作業系統(含版本)",
        "運行的應用程式(含版本)",
        "負責人",
        "資料敏感度",
        "是否對外(Public-facing)",
        "業務關鍵性",
    ]
    
    # CSV 可選欄位
    OPTIONAL_COLUMNS = [
        "ITEM",
        "IP",
    ]
    
    # 所有欄位
    ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS
    
    def __init__(self, asset_service: AssetService):
        """
        初始化服務
        
        Args:
            asset_service: 資產服務
        """
        self.asset_service = asset_service
    
    def parse_csv(self, csv_content: str) -> List[Dict[str, str]]:
        """
        解析 CSV 檔案
        
        Args:
            csv_content: CSV 檔案內容（字串）
        
        Returns:
            List[Dict[str, str]]: 解析後的記錄清單
        
        Raises:
            ValueError: 當 CSV 格式錯誤時
        """
        try:
            # 使用 StringIO 將字串轉換為檔案物件
            csv_file = io.StringIO(csv_content)
            
            # 讀取 CSV
            reader = csv.DictReader(csv_file)
            records = []
            
            for row_num, row in enumerate(reader, start=2):  # 從第 2 行開始（第 1 行是標題）
                # 清理空白字元
                cleaned_row = {k.strip(): v.strip() if v else "" for k, v in row.items()}
                records.append(cleaned_row)
            
            return records
        
        except Exception as e:
            raise ValueError(f"CSV 解析失敗：{str(e)}")
    
    def validate_csv_format(self, records: List[Dict[str, str]]) -> tuple[bool, List[Dict]]:
        """
        驗證 CSV 格式
        
        Args:
            records: CSV 記錄清單
        
        Returns:
            tuple[bool, List[Dict]]: (是否有效, 錯誤清單)
        """
        errors = []
        
        # 檢查是否有記錄
        if not records:
            errors.append({
                "row": 0,
                "field": "general",
                "error": "CSV 檔案為空或沒有資料行",
            })
            return False, errors
        
        # 檢查每筆記錄
        for idx, record in enumerate(records, start=2):  # 從第 2 行開始
            row_errors = []
            
            # 檢查必要欄位
            for column in self.REQUIRED_COLUMNS:
                if column not in record or not record[column] or not record[column].strip():
                    row_errors.append({
                        "row": idx,
                        "field": column,
                        "error": f"必要欄位「{column}」不能為空",
                    })
            
            # 驗證資料敏感度
            if "資料敏感度" in record and record["資料敏感度"]:
                if record["資料敏感度"] not in ["高", "中", "低"]:
                    row_errors.append({
                        "row": idx,
                        "field": "資料敏感度",
                        "error": "資料敏感度必須為「高」、「中」或「低」",
                    })
            
            # 驗證業務關鍵性
            if "業務關鍵性" in record and record["業務關鍵性"]:
                if record["業務關鍵性"] not in ["高", "中", "低"]:
                    row_errors.append({
                        "row": idx,
                        "field": "業務關鍵性",
                        "error": "業務關鍵性必須為「高」、「中」或「低」",
                    })
            
            # 驗證是否對外
            if "是否對外(Public-facing)" in record and record["是否對外(Public-facing)"]:
                value = record["是否對外(Public-facing)"].upper()
                if value not in ["Y", "N", "YES", "NO"]:
                    row_errors.append({
                        "row": idx,
                        "field": "是否對外(Public-facing)",
                        "error": "是否對外必須為「Y」或「N」",
                    })
            
            errors.extend(row_errors)
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    async def preview_import(
        self,
        csv_content: str,
        max_preview_rows: int = 10,
    ) -> ImportPreviewResponse:
        """
        匯入預覽
        
        Args:
            csv_content: CSV 檔案內容
            max_preview_rows: 最大預覽行數（預設 10）
        
        Returns:
            ImportPreviewResponse: 預覽回應
        """
        logger.info("開始匯入預覽", extra={"max_preview_rows": max_preview_rows})
        
        # 1. 解析 CSV
        try:
            records = self.parse_csv(csv_content)
        except ValueError as e:
            return ImportPreviewResponse(
                total_count=0,
                valid_count=0,
                invalid_count=0,
                preview_data=[],
                errors=[{"row": 0, "field": "general", "error": str(e)}],
            )
        
        # 2. 驗證格式
        is_valid, errors = self.validate_csv_format(records)
        
        # 3. 準備預覽資料（只顯示前 max_preview_rows 筆）
        preview_data = []
        for idx, record in enumerate(records[:max_preview_rows]):
            # 轉換為預覽格式
            preview_record = {
                "row": idx + 2,  # 從第 2 行開始
                "data": {
                    "item": record.get("ITEM", ""),
                    "ip": record.get("IP", ""),
                    "host_name": record.get("主機名稱", ""),
                    "operating_system": record.get("作業系統(含版本)", ""),
                    "running_applications": record.get("運行的應用程式(含版本)", ""),
                    "owner": record.get("負責人", ""),
                    "data_sensitivity": record.get("資料敏感度", ""),
                    "is_public_facing": record.get("是否對外(Public-facing)", ""),
                    "business_criticality": record.get("業務關鍵性", ""),
                },
            }
            preview_data.append(preview_record)
        
        # 4. 計算有效和無效筆數
        valid_count = len(records) - len(errors)
        invalid_count = len(errors)
        
        logger.info("匯入預覽完成", extra={
            "total_count": len(records),
            "valid_count": valid_count,
            "invalid_count": invalid_count,
        })
        
        return ImportPreviewResponse(
            total_count=len(records),
            valid_count=valid_count,
            invalid_count=invalid_count,
            preview_data=preview_data,
            errors=errors,
        )
    
    async def import_assets(
        self,
        csv_content: str,
        user_id: str = "system",
        batch_size: int = 100,
    ) -> ImportResultResponse:
        """
        執行匯入（支援批次處理至少 1000 筆）
        
        Args:
            csv_content: CSV 檔案內容
            user_id: 使用者 ID（預設 "system"）
            batch_size: 批次大小（預設 100，至少支援 1000 筆）
        
        Returns:
            ImportResultResponse: 匯入結果回應
        """
        logger.info("開始匯入資產", extra={"user_id": user_id, "batch_size": batch_size})
        
        # 1. 解析 CSV
        try:
            records = self.parse_csv(csv_content)
        except ValueError as e:
            return ImportResultResponse(
                total_count=0,
                success_count=0,
                failure_count=0,
                results=[{"row": 0, "success": False, "error": str(e)}],
            )
        
        # 2. 驗證格式
        is_valid, errors = self.validate_csv_format(records)
        if not is_valid:
            # 如果有格式錯誤，返回錯誤結果
            return ImportResultResponse(
                total_count=len(records),
                success_count=0,
                failure_count=len(records),
                results=[
                    {
                        "row": error["row"],
                        "success": False,
                        "error": f"{error['field']}: {error['error']}",
                    }
                    for error in errors
                ],
            )
        
        # 3. 批次處理（每批 batch_size 筆）
        results = []
        total_batches = (len(records) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(records))
            batch = records[start_idx:end_idx]
            
            logger.info("處理批次", extra={
                "batch_num": batch_num + 1,
                "total_batches": total_batches,
                "batch_size": len(batch),
            })
            
            batch_results = await self._process_batch(batch, user_id, start_idx + 2)  # 從第 2 行開始
            results.extend(batch_results)
        
        # 4. 統計結果
        success_count = sum(1 for r in results if r.get("success", False))
        failure_count = len(results) - success_count
        
        logger.info("匯入完成", extra={
            "total_count": len(records),
            "success_count": success_count,
            "failure_count": failure_count,
        })
        
        return ImportResultResponse(
            total_count=len(records),
            success_count=success_count,
            failure_count=failure_count,
            results=results,
        )
    
    async def _process_batch(
        self,
        batch: List[Dict[str, str]],
        user_id: str,
        start_row: int,
    ) -> List[Dict]:
        """
        處理批次
        
        Args:
            batch: 批次記錄清單
            user_id: 使用者 ID
            start_row: 起始行號
        
        Returns:
            List[Dict]: 處理結果清單
        """
        results = []
        
        for idx, record in enumerate(batch):
            row_num = start_row + idx
            
            try:
                # 轉換記錄為 CreateAssetRequest
                request = self._convert_to_create_request(record)
                
                # 建立資產
                asset_id = await self.asset_service.create_asset(request, user_id)
                
                results.append({
                    "row": row_num,
                    "success": True,
                    "asset_id": asset_id,
                })
            
            except Exception as e:
                logger.error("匯入資產失敗", extra={"row": row_num, "error": str(e)})
                results.append({
                    "row": row_num,
                    "success": False,
                    "error": str(e),
                })
        
        return results
    
    def _convert_to_create_request(self, record: Dict[str, str]) -> CreateAssetRequest:
        """
        將 CSV 記錄轉換為 CreateAssetRequest
        
        Args:
            record: CSV 記錄
        
        Returns:
            CreateAssetRequest: 建立資產請求
        """
        # 轉換「是否對外」
        is_public_facing = False
        if "是否對外(Public-facing)" in record and record["是否對外(Public-facing)"]:
            value = record["是否對外(Public-facing)"].upper()
            is_public_facing = value in ["Y", "YES"]
        
        # 轉換 ITEM（可選）
        item = None
        if "ITEM" in record and record["ITEM"]:
            try:
                item = int(record["ITEM"])
            except ValueError:
                item = None
        
        return CreateAssetRequest(
            host_name=record.get("主機名稱", ""),
            ip=record.get("IP", None),
            item=item,
            operating_system=record.get("作業系統(含版本)", ""),
            running_applications=record.get("運行的應用程式(含版本)", ""),
            owner=record.get("負責人", ""),
            data_sensitivity=record.get("資料敏感度", ""),
            is_public_facing=is_public_facing,
            business_criticality=record.get("業務關鍵性", ""),
        )
    
    def generate_import_result(
        self,
        result: ImportResultResponse,
    ) -> str:
        """
        生成匯入結果報告
        
        Args:
            result: 匯入結果
        
        Returns:
            str: 匯入結果報告（文字格式）
        """
        report_lines = [
            "=" * 50,
            "資產匯入結果報告",
            "=" * 50,
            f"總筆數：{result.total_count}",
            f"成功筆數：{result.success_count}",
            f"失敗筆數：{result.failure_count}",
            f"成功率：{(result.success_count / result.total_count * 100):.2f}%" if result.total_count > 0 else "0%",
            "",
        ]
        
        if result.failure_count > 0:
            report_lines.append("失敗記錄：")
            report_lines.append("-" * 50)
            for r in result.results:
                if not r.get("success", False):
                    report_lines.append(f"第 {r['row']} 行：{r.get('error', '未知錯誤')}")
        
        return "\n".join(report_lines)

