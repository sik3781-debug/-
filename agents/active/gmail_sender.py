"""
Gmail 발송 에이전트 (/Gmail발송) — 외부 API 연동 그룹
Gmail API (OAuth 2.0): 컨설팅 보고서·리스크 알림 이메일 자동 발송
환경변수: GMAIL_CREDENTIALS_JSON (필수 — Google Cloud Console OAuth 자격증명 경로)
필요 패키지: google-auth, google-auth-oauthlib, google-api-python-client
"""
from __future__ import annotations
import os
import base64
import json
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "token.json")
_CRED_ENV   = "GMAIL_CREDENTIALS_JSON"


def _get_service():
    """Gmail API 서비스 객체 반환 (OAuth 토큰 캐시 포함)"""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as e:
        raise ImportError(
            "Gmail 발송을 위해 다음 패키지 설치 필요:\n"
            "  pip install google-auth google-auth-oauthlib google-api-python-client\n"
            f"원본 오류: {e}"
        ) from e

    creds = None
    if os.path.exists(_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(_TOKEN_PATH, _SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            cred_path = os.environ.get(_CRED_ENV, "")
            if not cred_path or not os.path.exists(cred_path):
                raise EnvironmentError(
                    f"{_CRED_ENV} 환경변수에 Google OAuth 자격증명 JSON 경로를 지정하세요.\n"
                    "Google Cloud Console → API·서비스 → 자격증명 → OAuth 2.0 클라이언트 ID"
                )
            flow = InstalledAppFlow.from_client_secrets_file(cred_path, _SCOPES)
            creds = flow.run_local_server(port=0)
        with open(_TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    from googleapiclient.discovery import build
    return build("gmail", "v1", credentials=creds)


class GmailSenderAgent:
    """Gmail OAuth 기반 컨설팅 이메일 발송 스켈레톤"""

    classification = "외부API연동"
    group = "외부 API 연동 그룹"
    sender_email = "sik3781@gmail.com"

    # ── 내부 헬퍼 ──────────────────────────────────────────────────────────
    @staticmethod
    def _build_message(to: str, subject: str, body_html: str,
                       attachment_path: str | None = None) -> dict:
        """RFC 2822 메시지 객체 → base64url 인코딩"""
        msg = MIMEMultipart("mixed")
        msg["to"]      = to
        msg["subject"] = subject
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        if attachment_path and os.path.exists(attachment_path):
            fname = os.path.basename(attachment_path)
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{fname}"')
            msg.attach(part)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        return {"raw": raw}

    # ── 공개 API ───────────────────────────────────────────────────────────
    def send_report(self, to: str, client_name: str, report_summary: str,
                    attachment_path: str | None = None) -> dict:
        """컨설팅 보고서 발송"""
        subject = f"[정기컨설팅] {client_name} 진단 보고서 — {datetime.today().strftime('%Y-%m-%d')}"
        body = (
            f"<h2>안녕하세요, {client_name} 담당자님</h2>"
            f"<p>컨설팅 진단 결과를 아래와 같이 보내드립니다.</p>"
            f"<pre style='font-family:monospace'>{report_summary}</pre>"
            f"<hr><p>중소기업 전문 경영컨설턴트 드림 | {self.sender_email}</p>"
        )
        service = _get_service()
        message = self._build_message(to, subject, body, attachment_path)
        result  = service.users().messages().send(userId="me", body=message).execute()
        return {"sent": True, "message_id": result.get("id"), "to": to}

    def send_risk_alert(self, to: str, alert_type: str, detail: str) -> dict:
        """리스크 알림 이메일 발송"""
        subject = f"[리스크 알림] {alert_type} — {datetime.today().strftime('%Y-%m-%d %H:%M')}"
        body = (
            f"<h3>리스크 알림: {alert_type}</h3>"
            f"<p>{detail}</p>"
            f"<hr><p>{self.sender_email}</p>"
        )
        service = _get_service()
        message = self._build_message(to, subject, body)
        result  = service.users().messages().send(userId="me", body=message).execute()
        return {"sent": True, "message_id": result.get("id"), "to": to, "type": alert_type}

    def analyze(self, case: dict) -> dict:
        """CommandRouter 표준 진입점 — DRY RUN 기본값"""
        to             = case.get("to", "")
        client_name    = case.get("client_name", "테스트고객")
        report_summary = case.get("report_summary", "컨설팅 결과 요약 (테스트)")
        attachment     = case.get("attachment_path")
        dry_run        = case.get("dry_run", True)  # 기본 DRY RUN

        if dry_run:
            return {
                "classification": self.classification,
                "group": self.group,
                "dry_run": True,
                "would_send_to": to,
                "client": client_name,
                "preview_subject": f"[정기컨설팅] {client_name} 진단 보고서 — {datetime.today().strftime('%Y-%m-%d')}",
                "attachment": attachment,
                "command": "/Gmail발송",
                "note": "실 발송 시 case['dry_run']=False + GMAIL_CREDENTIALS_JSON 설정 필요",
            }

        result = self.send_report(to, client_name, report_summary, attachment)
        return {
            "classification": self.classification,
            "group": self.group,
            "dry_run": False,
            "result": result,
            "command": "/Gmail발송",
        }
