import logging
import os
from backend.schemas.internal_models import RiskLevel
from backend.schemas.request_schema import AnalyzeRequest
from backend.services.supabase_service import SupabaseService
from backend.config import settings

logger = logging.getLogger("NotificationService")

class NotificationService:
    def __init__(self, db_service: SupabaseService):
        self.db = db_service
        self.admin_email = settings.ADMIN_EMAIL

    def check_and_alert(self, input_id: str, user_id: str, patient_data: AnalyzeRequest, risk_level: RiskLevel):
        if risk_level not in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return
        bp_label = {0: "Low", 1: "Medium", 2: "High"}.get(patient_data.blood_pressure, "Unknown")
        msg_body = f"URGENT: Assessment {input_id} flagged as {risk_level.value}.\nVitals: BP {bp_label} Category, HR {patient_data.heart_rate}, Hb {patient_data.hemoglobin}"
        return self._send_email_mock(self.admin_email, f"Maternal Health Alert: {risk_level.value}", msg_body)

    def _send_email_mock(self, to: str, subject: str, body: str) -> bool:
        if settings.SMTP_SERVER and settings.SMTP_USER:
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                msg = MIMEMultipart()
                msg['From'] = settings.SMTP_USER
                msg['To'] = to
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))
                server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_USER, to, msg.as_string())
                server.quit()
                return True
            except Exception:
                return False
        else:
            logger.info(f"Mock email logged for {to}")
            return True
