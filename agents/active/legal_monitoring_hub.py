"""
agents/active/legal_monitoring_hub.py
=======================================
LegalMonitoringHub — 8종 법령 일간 모니터링 허브
외부 API 없이 memory 캐시 기반 오프라인 동작 (LAW_API_ID는 D+16 활성화)
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime
from typing import Any

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CACHE_DIR = os.path.join(_ROOT, "memory", "law_cache")
_LOG       = os.path.join(_ROOT, "storage", "legal_monitoring_log.jsonl")

# 8종 법령 정의
LAW_REGISTRY: dict[str, dict] = {
    "CIT": {
        "name": "법인세법·시행령·시행규칙",
        "key_articles": ["§55 세율", "§28 가지급금", "§40 손금불산입"],
        "affected_agents": ["TaxAgent", "FinanceAgent", "ValuationOptimizationAgent",
                            "RetainedEarningsManagementAgent"],
    },
    "PIT": {
        "name": "소득세법",
        "key_articles": ["§22 퇴직소득", "§89 비과세"],
        "affected_agents": ["ExecutivePayAgent", "PerformancePayAgent"],
    },
    "IPT": {
        "name": "상속세및증여세법",
        "key_articles": ["§18의2 가업상속공제", "§54~56 비상장주식", "§45의5 특수관계거래"],
        "affected_agents": ["StockAgent", "ValuationOptimizationAgent",
                            "SpecialCorpTransactionAgent", "InheritanceTaxAgent",
                            "CivilTrustAgent", "LongTermAssetTransferAgent"],
    },
    "STX": {
        "name": "조세특례제한법",
        "key_articles": ["R&D 세액공제", "중소기업 특례"],
        "affected_agents": ["RDTaxCreditAgent", "InvestTaxCreditAgent", "TaxAgent"],
    },
    "BTA": {
        "name": "국세기본법",
        "key_articles": ["경정청구", "제척기간", "가산세"],
        "affected_agents": ["TaxRefundClaimAgent", "TaxAgent"],
    },
    "COM": {
        "name": "상법",
        "key_articles": ["§341 자기주식", "§360의2~의18 분할·합병"],
        "affected_agents": ["TreasuryStockStrategyAgent", "ChildCorpDesignAgent",
                            "SpecialCorpTransactionAgent"],
    },
    "LAB": {
        "name": "근로기준법",
        "key_articles": ["퇴직금", "연장수당", "근로시간"],
        "affected_agents": ["LaborAgent", "SocialInsuranceAgent", "ExecutivePayAgent"],
    },
    "LTX": {
        "name": "지방세법",
        "key_articles": ["취득세", "재산세", "법인지방소득세"],
        "affected_agents": ["RealEstateAgent", "TaxAgent"],
    },
}

# 캐시에서 변경 감지 (오프라인 모드용 패턴)
_KNOWN_CHANGES_2026 = [
    {
        "law_code": "CIT",
        "article": "§55",
        "change_type": "rate_change",
        "description": "법인세율 1%p 환원 (2026년 귀속 사업연도~): 9→10%, 19→20%, 21→22%, 24→25%",
        "effective_date": "2026-01-01",
        "impact_level": "high",
    },
]


class LegalMonitoringHub:
    """
    오프라인 모드: memory 캐시 + 알려진 변경 사항 DB 활용.
    LAW_API_ID 등록(D+16) 후 온라인 모드 자동 전환.
    """

    def __init__(self):
        os.makedirs(_CACHE_DIR, exist_ok=True)

    def detect_changes(self, target_date: str | None = None) -> dict[str, Any]:
        target = target_date or date.today().isoformat()
        api_key = os.environ.get("LAW_API_ID")
        if api_key:
            return self._online_detect(target, api_key)
        return self._offline_detect(target)

    def _offline_detect(self, target_date: str) -> dict[str, Any]:
        cache_file = os.path.join(_CACHE_DIR, f"{target_date[:7]}.json")
        if os.path.exists(cache_file):
            with open(cache_file, encoding="utf-8") as f:
                return json.load(f)

        # 알려진 2026년 변경사항 반환
        changes = _KNOWN_CHANGES_2026.copy()
        result = self._build_result(target_date, changes, mode="offline_cache")
        self._save_log(result)
        return result

    def _online_detect(self, target_date: str, api_key: str) -> dict[str, Any]:
        # D+16 LAW_API_ID 활성화 후 구현 예정
        # 현재는 오프라인 모드와 동일
        return self._offline_detect(target_date)

    def _build_result(self, target_date: str, raw_changes: list[dict],
                      mode: str = "offline") -> dict[str, Any]:
        enriched = []
        for ch in raw_changes:
            code = ch.get("law_code", "")
            reg = LAW_REGISTRY.get(code, {})
            enriched.append({
                **ch,
                "law_name": reg.get("name", code),
                "affected_agents": reg.get("affected_agents", []),
                "_4_perspective": self._classify_impact(code),
            })

        return {
            "date": target_date,
            "mode": mode,
            "changes_detected": len(enriched),
            "items": enriched,
            "propagation_status": "pending" if enriched else "no_change",
            "laws_monitored": list(LAW_REGISTRY.keys()),
            "_generated": datetime.now().isoformat(timespec="seconds"),
        }

    def _classify_impact(self, law_code: str) -> dict[str, str]:
        matrix = {
            "CIT": {"법인": "high", "주주": "medium", "과세관청": "high", "금융기관": "low"},
            "PIT": {"법인": "medium", "주주": "high", "과세관청": "high", "금융기관": "low"},
            "IPT": {"법인": "medium", "주주": "high", "과세관청": "high", "금융기관": "low"},
            "STX": {"법인": "high", "주주": "medium", "과세관청": "high", "금융기관": "low"},
            "BTA": {"법인": "medium", "주주": "low", "과세관청": "high", "금융기관": "low"},
            "COM": {"법인": "high", "주주": "high", "과세관청": "medium", "금융기관": "medium"},
            "LAB": {"법인": "medium", "주주": "low", "과세관청": "medium", "금융기관": "low"},
            "LTX": {"법인": "medium", "주주": "medium", "과세관청": "high", "금융기관": "medium"},
        }
        return matrix.get(law_code, {"법인": "unknown", "주주": "unknown",
                                     "과세관청": "unknown", "금융기관": "unknown"})

    def _save_log(self, result: dict) -> None:
        try:
            os.makedirs(os.path.dirname(_LOG), exist_ok=True)
            with open(_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def analyze(self, data: dict) -> dict:
        return self.detect_changes(data.get("target_date"))
