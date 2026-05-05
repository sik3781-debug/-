"""
자금리서치 알림 에이전트 (/자금리서치알림) — 외부 API 연동 그룹
ECOS API (한국은행 경제통계시스템): 기준금리·통화량·기업대출금리 조회
환경변수: ECOS_API_KEY (필수)
"""
from __future__ import annotations
import os
import json
from datetime import datetime, timedelta
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import URLError


_ECOS_BASE = "https://ecos.bok.or.kr/api"

# 주요 통계 코드 (ECOS 통계표 코드)
_STAT_CODES = {
    "기준금리":      ("722Y001", "0101000"),   # 한국은행 기준금리
    "CD금리_91일":   ("817Y002", "010190000"), # CD 유통수익률 91일
    "기업대출금리":  ("121Y006", "BECBLA01"),  # 예금은행 기업대출금리
    "M2통화량":      ("101Y003", "BBHS00"),    # 광의통화(M2) 말잔
}


class FundingResearchAlertAgent:
    """ECOS API로 금리·통화량 조회 → 자금조달 환경 알림 생성"""

    classification = "외부API연동"
    group = "외부 API 연동 그룹"

    def __init__(self) -> None:
        self._api_key = os.environ.get("ECOS_API_KEY", "")
        self.is_authenticated = bool(self._api_key)
        # 모킹 모드: API 키 없이도 초기화 가능 (실제 호출은 인증 후)

    # ── 내부 헬퍼 ──────────────────────────────────────────────────────────
    def _fetch_stat(self, stat_code: str, item_code: str,
                    period: str | None = None) -> list[dict]:
        """ECOS 단일 지표 시계열 조회 (JSON). period: 'YYYYMM' 또는 'YYYY'"""
        if period is None:
            period = (datetime.today() - timedelta(days=30)).strftime("%Y%m")
        end_period = datetime.today().strftime("%Y%m")
        url = (
            f"{_ECOS_BASE}/StatisticSearch/{self._api_key}/json/kr/1/10/"
            f"{stat_code}/MM/{period}/{end_period}/{item_code}"
        )
        try:
            with urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            rows = data.get("StatisticSearch", {}).get("row", [])
            return rows
        except URLError as e:
            return [{"error": str(e), "stat_code": stat_code}]
        except (KeyError, json.JSONDecodeError) as e:
            return [{"error": f"파싱 오류: {e}", "stat_code": stat_code}]

    def _latest_value(self, rows: list[dict]) -> tuple[str, str]:
        """최신 데이터 포인트 (기간, 값) 반환"""
        if not rows or "error" in rows[-1]:
            return ("N/A", "오류")
        last = rows[-1]
        return last.get("TIME", "N/A"), last.get("DATA_VALUE", "N/A")

    # ── 공개 API ───────────────────────────────────────────────────────────
    def fetch_all(self, period: str | None = None) -> dict:
        """4대 지표 일괄 조회"""
        results = {}
        for name, (stat, item) in _STAT_CODES.items():
            rows = self._fetch_stat(stat, item, period)
            t, v = self._latest_value(rows)
            results[name] = {"period": t, "value": v, "raw": rows}
        return results

    def generate_alert(self, period: str | None = None) -> dict:
        """자금조달 환경 알림 메시지 생성 (4자관점)"""
        data = self.fetch_all(period)
        base_rate = data.get("기준금리", {}).get("value", "N/A")
        corp_rate  = data.get("기업대출금리", {}).get("value", "N/A")
        cd_rate    = data.get("CD금리_91일", {}).get("value", "N/A")
        m2         = data.get("M2통화량", {}).get("value", "N/A")

        try:
            br = float(base_rate)
            cr = float(corp_rate)
            rate_spread = cr - br
            env = "고금리 환경 — 차입 비용 증가" if br >= 3.0 else "저금리 환경 — 자금조달 유리"
        except (ValueError, TypeError):
            rate_spread = None
            env = "금리 데이터 수신 불가"

        alert = {
            "timestamp": datetime.today().isoformat(timespec="seconds"),
            "summary": {
                "기준금리": f"{base_rate}%",
                "기업대출금리": f"{corp_rate}%",
                "CD금리91일": f"{cd_rate}%",
                "M2통화량": m2,
                "금리스프레드": f"{rate_spread:.2f}%p" if rate_spread is not None else "N/A",
                "환경진단": env,
            },
            "4자관점": {
                "법인":       f"기준금리 {base_rate}% — 운전·시설자금 조달금리 점검 필요",
                "주주(오너)": f"기업대출금리 {corp_rate}% — 대주주 대여금 vs 은행차입 비교 검토",
                "과세관청":   f"CD금리 {cd_rate}% — 특수관계인 대여금 당좌대출이자율(국기칙§5) 산정 기준",
                "금융기관":   f"M2 {m2}억원 — 유동성 환경 기반 여신 한도·금리 재협상 시점 판단",
            },
            "raw_data": data,
        }
        return alert

    def analyze(self, case: dict) -> dict:
        """CommandRouter 표준 진입점 — 미인증 시 모킹 응답"""
        if not self.is_authenticated or case.get("mock"):
            strategy = {"auth_status": "인증 대기 (ECOS_API_KEY 미설정)", "indicators": list(_STAT_CODES.keys())}
            process = {"auth_status": "mock", "note": "ECOS_API_KEY 설정 후 본격 가동"}
            return {"classification": self.classification, "group": self.group,
                    "strategy": strategy, "process": process, "command": "/자금리서치알림"}
        period = case.get("period")
        alert  = self.generate_alert(period)
        strategy = {"auth_status": "인증 완료", "data": alert.get("summary", {})}
        return {
            "classification": self.classification, "group": self.group,
            "strategy": strategy, "process": alert, "alert": alert,
            "command": "/자금리서치알림",
        }
