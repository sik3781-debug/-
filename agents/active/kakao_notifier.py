"""
카카오톡 알림 에이전트 (/카톡알림) — 외부 API 연동 그룹
카카오 비즈메시지(알림톡) API: 컨설팅 결과 요약 자동 발송
환경변수: KAKAO_BIZ_API_KEY, KAKAO_SENDER_KEY, KAKAO_TEMPLATE_CODE (필수)
주의: 실 발송 전 카카오 비즈채널 심사·템플릿 승인 필요
"""
from __future__ import annotations
import os
import json
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


_KAKAO_BIZ_URL = "https://alimtalk-api.kakao.com/v2/sender/send"


class KakaoNotifierAgent:
    """카카오 알림톡 발송 스켈레톤 — 실 발송 전 채널·템플릿 등록 필수"""

    classification = "외부API연동"
    group = "외부 API 연동 그룹"

    def __init__(self) -> None:
        self._api_key      = os.environ.get("KAKAO_BIZ_API_KEY", "")
        self._sender_key   = os.environ.get("KAKAO_SENDER_KEY", "")
        self._template_code = os.environ.get("KAKAO_TEMPLATE_CODE", "")
        self.is_authenticated = all([self._api_key, self._sender_key, self._template_code])
        # 모킹 모드: API 키 없이도 초기화 가능 (실제 발송은 인증 후)

    # ── 내부 헬퍼 ──────────────────────────────────────────────────────────
    def _build_payload(self, phone: str, template_params: dict) -> bytes:
        """알림톡 전송 페이로드 (JSON) 구성"""
        payload = {
            "senderKey": self._sender_key,
            "templateCode": self._template_code,
            "recipientList": [
                {
                    "recipientNo": phone.replace("-", ""),
                    "templateParameter": template_params,
                }
            ],
        }
        return json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def _post(self, payload: bytes) -> dict:
        req = Request(
            _KAKAO_BIZ_URL,
            data=payload,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"KakaoAK {self._api_key}",
            },
            method="POST",
        )
        try:
            with urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            return {"error": f"HTTP {e.code}: {e.reason}", "sent": False}
        except URLError as e:
            return {"error": str(e), "sent": False}

    # ── 공개 API ───────────────────────────────────────────────────────────
    def send_consulting_summary(self, phone: str, client_name: str,
                                 summary_text: str, advisor: str = "정기컨설팅") -> dict:
        """컨설팅 결과 요약 알림톡 발송"""
        params = {
            "고객명": client_name,
            "컨설팅결과": summary_text[:200],  # 템플릿 글자 수 제한 대비
            "담당자": advisor,
            "발송일시": datetime.today().strftime("%Y-%m-%d %H:%M"),
        }
        result = self._post(self._build_payload(phone, params))
        result["phone"] = phone
        result["client"] = client_name
        return result

    def send_alert(self, phone: str, alert_type: str, message: str) -> dict:
        """리스크·일정 알림 발송 (범용)"""
        params = {
            "알림유형": alert_type,
            "메시지": message[:200],
            "발송일시": datetime.today().strftime("%Y-%m-%d %H:%M"),
        }
        return self._post(self._build_payload(phone, params))

    def analyze(self, case: dict) -> dict:
        """CommandRouter 표준 진입점 — 미인증 시 모킹 응답"""
        phone        = case.get("phone", "")
        client_name  = case.get("client_name", "테스트고객")
        summary_text = case.get("summary_text", "컨설팅 결과 요약 (테스트)")
        dry_run      = case.get("dry_run", True)

        if not self.is_authenticated or case.get("mock"):
            strategy = {"auth_status": "인증 대기 (KAKAO_BIZ_API_KEY 미설정)"}
            process  = {"auth_status": "mock", "note": "카카오 비즈채널 심사·템플릿 승인 후 가동"}
            return {"classification": self.classification, "group": self.group,
                    "strategy": strategy, "process": process, "command": "/카톡알림"}

        if dry_run:
            strategy = {"auth_status": "인증 완료", "dry_run": True}
            process  = {"would_send_to": phone, "client": client_name,
                        "preview": summary_text[:200]}
            return {"classification": self.classification, "group": self.group,
                    "strategy": strategy, "process": process, "command": "/카톡알림",
                    "note": "실 발송 시 case['dry_run']=False 설정 필요"}

        result = self.send_consulting_summary(phone, client_name, summary_text)
        return {"classification": self.classification, "group": self.group,
                "strategy": {"auth_status": "인증 완료"}, "process": result,
                "command": "/카톡알림"}
