"""
Email 服務（Infrastructure Layer）

負責發送 Email 通知，支援 SMTP 和 Email API（如 SendGrid、AWS SES）。
"""

from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import structlog
from dataclasses import dataclass

logger = structlog.get_logger(__name__)


@dataclass
class EmailConfig:
    """Email 設定"""
    smtp_host: str
    smtp_port: int
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    from_email: str = "noreply@example.com"
    from_name: str = "AETIM Security System"


class EmailService:
    """
    Email 服務
    
    負責發送 Email 通知，支援：
    1. SMTP 發送
    2. HTML 格式郵件
    3. 錯誤處理與重試機制
    """
    
    def __init__(self, config: EmailConfig):
        """
        初始化 Email 服務
        
        Args:
            config: Email 設定
        """
        self.config = config
    
    async def send(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        max_retries: int = 3,
    ) -> bool:
        """
        發送 Email（AC-016-3, AC-019-3）
        
        Args:
            recipients: 收件人清單（Email 地址）
            subject: 主旨
            body: 純文字內容
            html_body: HTML 內容（可選）
            max_retries: 最大重試次數（預設：3）
        
        Returns:
            bool: 發送是否成功
        
        Raises:
            ValueError: 當收件人清單為空時
            Exception: 當發送失敗時
        """
        if not recipients or len(recipients) == 0:
            raise ValueError("收件人清單不能為空")
        
        # 驗證 Email 地址格式（簡單驗證）
        for recipient in recipients:
            if "@" not in recipient:
                raise ValueError(f"無效的 Email 地址：{recipient}")
        
        # 建立郵件訊息
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        
        # 添加純文字內容
        text_part = MIMEText(body, "plain", "utf-8")
        msg.attach(text_part)
        
        # 添加 HTML 內容（如果提供）
        if html_body:
            html_part = MIMEText(html_body, "html", "utf-8")
            msg.attach(html_part)
        
        # 發送郵件（含重試機制）
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                await self._send_via_smtp(msg, recipients)
                
                logger.info(
                    "Email 發送成功",
                    recipients=recipients,
                    subject=subject,
                    attempt=attempt,
                )
                
                return True
                
            except Exception as e:
                last_error = e
                logger.warning(
                    "Email 發送失敗，準備重試",
                    recipients=recipients,
                    subject=subject,
                    attempt=attempt,
                    max_retries=max_retries,
                    error=str(e),
                )
                
                if attempt < max_retries:
                    # 等待後重試（指數退避）
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
        
        # 所有重試都失敗
        logger.error(
            "Email 發送失敗，已達最大重試次數",
            recipients=recipients,
            subject=subject,
            error=str(last_error),
        )
        
        raise Exception(f"Email 發送失敗：{str(last_error)}")
    
    async def send_batch(
        self,
        emails: List[dict],
        max_retries: int = 3,
    ) -> List[dict]:
        """
        批次發送 Email
        
        Args:
            emails: Email 清單，每個元素包含：
                - recipients: List[str]
                - subject: str
                - body: str
                - html_body: Optional[str]
            max_retries: 最大重試次數（預設：3）
        
        Returns:
            List[dict]: 發送結果清單，每個元素包含：
                - success: bool
                - recipients: List[str]
                - error: Optional[str]
        """
        results = []
        
        for email in emails:
            try:
                success = await self.send(
                    recipients=email["recipients"],
                    subject=email["subject"],
                    body=email["body"],
                    html_body=email.get("html_body"),
                    max_retries=max_retries,
                )
                
                results.append({
                    "success": success,
                    "recipients": email["recipients"],
                    "error": None,
                })
                
            except Exception as e:
                logger.error(
                    "批次發送 Email 失敗",
                    recipients=email.get("recipients"),
                    error=str(e),
                )
                
                results.append({
                    "success": False,
                    "recipients": email.get("recipients", []),
                    "error": str(e),
                })
        
        return results
    
    async def _send_via_smtp(
        self,
        msg: MIMEMultipart,
        recipients: List[str],
    ) -> None:
        """
        透過 SMTP 發送郵件
        
        Args:
            msg: 郵件訊息
            recipients: 收件人清單
        
        Raises:
            Exception: 當發送失敗時
        """
        try:
            # 建立 SMTP 連線
            if self.config.smtp_use_tls:
                server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.config.smtp_host, self.config.smtp_port)
            
            # 登入（如果需要）
            if self.config.smtp_username and self.config.smtp_password:
                server.login(self.config.smtp_username, self.config.smtp_password)
            
            # 發送郵件
            server.send_message(msg, to_addrs=recipients)
            server.quit()
            
        except Exception as e:
            logger.error(
                "SMTP 發送失敗",
                smtp_host=self.config.smtp_host,
                smtp_port=self.config.smtp_port,
                recipients=recipients,
                error=str(e),
                exc_info=True,
            )
            raise

