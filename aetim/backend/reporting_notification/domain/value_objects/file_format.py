"""
檔案格式值物件

定義報告檔案格式的枚舉值。
"""

from enum import Enum


class FileFormat(str, Enum):
    """檔案格式枚舉"""
    
    HTML = "HTML"  # HTML 格式
    PDF = "PDF"  # PDF 格式
    TEXT = "TEXT"  # 純文字格式
    JSON = "JSON"  # JSON 格式
    
    def __str__(self) -> str:
        return self.value
    
    @classmethod
    def from_string(cls, value: str) -> "FileFormat":
        """從字串建立檔案格式"""
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"無效的檔案格式: {value}")
    
    def get_file_extension(self) -> str:
        """取得檔案副檔名"""
        return {
            "HTML": ".html",
            "PDF": ".pdf",
            "TEXT": ".txt",
            "JSON": ".json",
        }[self.value]

