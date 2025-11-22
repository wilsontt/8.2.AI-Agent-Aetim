"""
ML 模型載入器

負責載入與管理 ML 模型（spaCy、transformers 等）。
"""

from typing import Optional
import spacy
from transformers import pipeline


class ModelLoader:
    """ML 模型載入器"""
    
    def __init__(self):
        """初始化模型載入器"""
        self.nlp: Optional[spacy.Language] = None
        self.summarizer: Optional[object] = None
    
    def load_spacy_model(self, model_name: str = "zh_core_web_sm"):
        """
        載入 spaCy 模型
        
        Args:
            model_name: spaCy 模型名稱（預設：zh_core_web_sm）
        
        Raises:
            OSError: 當模型不存在時
        """
        try:
            self.nlp = spacy.load(model_name)
            print(f"✅ 已載入 spaCy 模型：{model_name}")
        except OSError:
            print(f"⚠️  spaCy 模型 {model_name} 不存在，請先下載：python -m spacy download {model_name}")
            raise
    
    def load_summarizer(self, model_name: str = "facebook/bart-large-cnn"):
        """
        載入摘要模型
        
        Args:
            model_name: Transformers 模型名稱（預設：facebook/bart-large-cnn）
        """
        try:
            self.summarizer = pipeline("summarization", model=model_name)
            print(f"✅ 已載入摘要模型：{model_name}")
        except Exception as e:
            print(f"⚠️  載入摘要模型失敗：{e}")
            raise
    
    def get_nlp(self) -> Optional[spacy.Language]:
        """
        取得 spaCy NLP 物件
        
        Returns:
            Optional[spacy.Language]: spaCy NLP 物件，如果未載入則返回 None
        """
        return self.nlp
    
    def get_summarizer(self) -> Optional[object]:
        """
        取得摘要模型
        
        Returns:
            Optional[object]: 摘要模型，如果未載入則返回 None
        """
        return self.summarizer


# 全域模型載入器實例
model_loader = ModelLoader()

