"""
agents/active/post_management_tracker.py
==========================================
PostManagementTracker — 법정 사후관리 의무 일정표 + 기한 알림
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta
from typing import Any

_ROOT    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TRACKER = os.path.join(_ROOT, "storage", "post_management.jsonl")
_NOTIFY  = os.path.join(_ROOT, "storage", "notifications.jsonl")

# 거래유형별 사후관리 정의
MANAGEMENT_RULES: dict[str, dict] = {
    "SUCCESSION": {
        "name": "가업승계",
        "years": 7,
        "law_ref": "상증세법 제18조의2 제6항",
        "checkpoints": [
            {"year": 2, "desc": "2년차 고용 유지 확인 (상속개시 전 2년 평균 대비 80% 이상)"},
            {"year": 3, "desc": "3년차 대표이사(상속인) 경영 유지 확인"},
            {"year": 5, "desc": "5년차 주된 업종 유지 확인"},
            {"year": 7, "desc": "7년차 최종 사후관리 완료 확인"},
        ],
        "penalty": "공제액 전액 추징 + 이자 상당액 가산세",
    },
    "NOMINEE": {
        "name": "차명주식 해소",
        "years": 5,
        "law_ref": "금융실명법 제3조, 상증세법 제45조의2",
        "checkpoints": [
            {"year": 1, "desc": "실명전환 완료 여부 확인"},
            {"year": 3, "desc": "증여세 과세 관련 이의신청 기간 경과 확인"},
            {"year": 5, "desc": "5년 경과 — 차명주식 사후관리 종료"},
        ],
        "penalty": "증여세 추징 + 40% 가산세",
    },
    "GIFT": {
        "name": "증여",
        "years": 5,
        "law_ref": "상증세법 제68조",
        "checkpoints": [
            {"year": 1, "desc": "증여세 신고·납부 완료 확인"},
            {"year": 3, "desc": "3년내 재증여 합산 여부 점검"},
            {"year": 5, "desc": "5년 사후관리 종료"},
        ],
        "penalty": "증여세 추징 + 가산세 최대 40%",
    },
    "INHERITANCE": {
        "name": "상속",
        "years": 10,
        "law_ref": "상증세법 제18조, 제67조",
        "checkpoints": [
            {"year": 1, "desc": "상속세 신고·납부 완료 확인"},
            {"year": 5, "desc": "분납·연부연납 이행 여부 확인"},
            {"year": 10, "desc": "10년 가산 합산 기간 종료"},
        ],
        "penalty": "상속세 추징 + 이자 상당액",
    },
    "MERGER": {
        "name": "합병·분할",
        "years": 3,
        "law_ref": "법인세법 제44조의3",
        "checkpoints": [
            {"year": 1, "desc": "합병등기일 이후 사업 계속 여부"},
            {"year": 3, "desc": "3년 사후관리 종료 (고용유지, 사업유지)"},
        ],
        "penalty": "과세특례 취소 + 법인세 추징",
    },
    "PATENT": {
        "name": "특허 이전",
        "years": 3,
        "law_ref": "조세특례제한법 제12조",
        "checkpoints": [
            {"year": 1, "desc": "특허 사용 실적 확인"},
            {"year": 3, "desc": "세액공제 사후관리 종료"},
        ],
        "penalty": "세액공제 취소 + 가산세",
    },
}


class PostManagementTracker:

    def register(self, transaction_date: str, transaction_type: str,
                 amount: int = 0, company: str = "") -> dict[str, Any]:
        rule = MANAGEMENT_RULES.get(transaction_type.upper())
        if not rule:
            return {
                "status": "unknown_type",
                "available_types": list(MANAGEMENT_RULES.keys()),
            }

        tx_date = date.fromisoformat(transaction_date)
        end_date = tx_date.replace(year=tx_date.year + rule["years"])
        today = date.today()
        days_remaining = (end_date - today).days

        schedule = []
        for cp in rule["checkpoints"]:
            cp_date = tx_date.replace(year=tx_date.year + cp["year"])
            warning_date = cp_date - timedelta(days=30)
            is_due = today >= warning_date
            is_overdue = today > cp_date
            schedule.append({
                "year": cp["year"],
                "due_date": cp_date.isoformat(),
                "warning_date": warning_date.isoformat(),
                "description": cp["desc"],
                "status": "overdue" if is_overdue else ("due_soon" if is_due else "upcoming"),
            })

        result = {
            "company": company,
            "transaction_type": transaction_type.upper(),
            "transaction_name": rule["name"],
            "transaction_date": transaction_date,
            "law_ref": rule["law_ref"],
            "management_end": end_date.isoformat(),
            "days_remaining": days_remaining,
            "schedule": schedule,
            "penalty": rule["penalty"],
            "status": "active" if days_remaining > 0 else "completed",
            "registered_at": datetime.now().isoformat(timespec="seconds"),
        }

        self._save(result)
        self._check_notifications(result, schedule)
        return result

    def _save(self, result: dict) -> None:
        try:
            os.makedirs(os.path.dirname(_TRACKER), exist_ok=True)
            with open(_TRACKER, "a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def _check_notifications(self, result: dict, schedule: list) -> None:
        urgent = [s for s in schedule if s["status"] in ("due_soon", "overdue")]
        for item in urgent:
            self._notify(
                f"[사후관리 {item['status'].upper()}] {result.get('company', '')} "
                f"{result['transaction_name']} — {item['description']} "
                f"(기한: {item['due_date']})",
                urgency="high" if item["status"] == "overdue" else "medium",
            )

    def _notify(self, message: str, urgency: str = "info") -> None:
        try:
            os.makedirs(os.path.dirname(_NOTIFY), exist_ok=True)
            entry = {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "urgency": urgency,
                "type": "post_management",
                "message": message,
            }
            with open(_NOTIFY, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def analyze(self, data: dict) -> dict:
        return self.register(
            transaction_date=data.get("transaction_date", date.today().isoformat()),
            transaction_type=data.get("transaction_type", "SUCCESSION"),
            amount=data.get("amount", 0),
            company=data.get("company_name", ""),
        )
