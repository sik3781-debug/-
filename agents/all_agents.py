"""
agents/all_agents.py
====================
MonitorAgent  — output/ 폴더 이전 스냅샷과 현재 지표를 비교하는 Delta 분석 에이전트
ScenarioAgent — 임원퇴직금 / 가업승계 / 자녀법인 3개 시나리오 수치 시뮬레이션 에이전트

두 에이전트 모두 BaseAgent 상속 + analyze(company_data) 인터페이스 제공
orchestrator.py GROUP_D 에 등록되어 Phase 1 마지막 배치로 실행됩니다.
"""

from __future__ import annotations

import json
import os
import glob
from datetime import datetime
from agents.base_agent import BaseAgent, MODEL

# ═══════════════════════════════════════════════════════════════════════════
# MonitorAgent
# ═══════════════════════════════════════════════════════════════════════════

_MONITOR_SYS = """당신은 중소기업 경영지표 변화 분석(Delta Analysis) 전문가입니다.
이전 스냅샷과 현재 지표를 비교하여 개선·악화 항목을 정량적으로 보고합니다.

【출력 형식 — 반드시 준수】
## 경영지표 Delta 분석 보고서

### 핵심 변화 요약
| 지표 | 이전 | 현재 | Delta | 방향 |
|------|------|------|-------|------|
...

### 개선 항목 (▲)
- 항목명: 수치 변화 / 의미 / 후속 과제

### 악화 항목 (▼)
- 항목명: 수치 변화 / 위험도 / 즉시 조치

### 스냅샷 비교 불가 항목
- 항목명: 사유

### Delta 종합 판정
- 전체 방향: 개선 / 유지 / 악화
- 핵심 메시지: (1문장)
- 다음 모니터링 권고 시점: (날짜 또는 기간)"""


class MonitorAgent(BaseAgent):
    """이전 실행 JSON 스냅샷과 현재 COMPANY_DATA를 비교하는 Delta 분석 에이전트."""

    name  = "MonitorAgent"
    role  = "경영지표 Delta 분석 전문가"
    model = MODEL
    system_prompt = _MONITOR_SYS

    # output/ 스냅샷 디렉터리 (orchestrator.py 기준 상대 경로)
    SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "snapshots")

    # Delta 를 계산할 재무 지표 목록
    KPI_KEYS = [
        ("revenue",            "매출액",      1e8, "억원"),
        ("net_income",         "순이익",      1e8, "억원"),
        ("total_debt",         "총부채",      1e8, "억원"),
        ("total_equity",       "자기자본",    1e8, "억원"),
        ("current_assets",     "유동자산",    1e8, "억원"),
        ("current_liabilities","유동부채",    1e8, "억원"),
        ("taxable_income",     "과세표준",    1e8, "억원"),
        ("provisional_payment","가지급금",    1e6, "백만원"),
        ("employees",          "임직원",      1,   "명"),
        ("rd_expense",         "R&D비용",    1e6, "백만원"),
    ]

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose=verbose)
        self.tools = [
            {
                "name": "calc_delta",
                "description": "이전 스냅샷과 현재 값의 차이를 계산하여 Delta 표를 반환합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "current_snapshot": {
                            "type": "object",
                            "description": "현재 주요 재무지표 딕셔너리",
                        },
                        "previous_snapshot": {
                            "type": "object",
                            "description": "이전 스냅샷 재무지표 딕셔너리 (없으면 빈 객체)",
                        },
                    },
                    "required": ["current_snapshot", "previous_snapshot"],
                },
            },
        ]

    # ── 툴 핸들러 ──────────────────────────────────────────────────────────

    def handle_tool(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "calc_delta":
            return self._calc_delta(
                tool_input.get("current_snapshot", {}),
                tool_input.get("previous_snapshot", {}),
            )
        return {"error": f"알 수 없는 툴: {tool_name}"}

    def _calc_delta(self, current: dict, previous: dict) -> dict:
        rows = []
        improvements, deteriorations, unchanged = [], [], []

        for key, label, unit, unit_label in self.KPI_KEYS:
            cur = current.get(key)
            prv = previous.get(key)
            if cur is None:
                continue
            cur_disp = f"{cur / unit:.1f}{unit_label}"
            if prv is None:
                rows.append({"지표": label, "이전": "N/A", "현재": cur_disp,
                             "Delta": "—", "방향": "신규"})
                continue

            delta_raw = cur - prv
            delta_pct = delta_raw / abs(prv) * 100 if prv else 0
            prv_disp  = f"{prv / unit:.1f}{unit_label}"
            sign      = "▲" if delta_raw > 0 else ("▼" if delta_raw < 0 else "─")
            delta_str = f"{sign} {abs(delta_raw)/unit:.1f}{unit_label} ({delta_pct:+.1f}%)"

            rows.append({"지표": label, "이전": prv_disp, "현재": cur_disp,
                         "Delta": delta_str, "방향": sign})

            # 부채·가지급금: 증가 = 악화
            if key in ("total_debt", "current_liabilities", "provisional_payment"):
                if delta_raw > 0:
                    deteriorations.append(f"{label} {delta_str}")
                elif delta_raw < 0:
                    improvements.append(f"{label} {delta_str}")
                else:
                    unchanged.append(label)
            else:
                if delta_raw > 0:
                    improvements.append(f"{label} {delta_str}")
                elif delta_raw < 0:
                    deteriorations.append(f"{label} {delta_str}")
                else:
                    unchanged.append(label)

        # 파생 지표
        derived = {}
        for snap, tag in [(current, "현재"), (previous, "이전")]:
            td = snap.get("total_debt", 0)
            te = snap.get("total_equity", 1)
            ca = snap.get("current_assets", 0)
            cl = snap.get("current_liabilities", 1)
            ni = snap.get("net_income", 0)
            derived[tag] = {
                "부채비율":   td / te * 100 if te else 999,
                "유동비율":   ca / cl * 100 if cl else 999,
                "이자보상배율": ni / (td * 0.05) if td else 99,
            }

        verdict = "개선" if len(improvements) > len(deteriorations) else \
                  ("악화" if len(deteriorations) > len(improvements) else "유지")

        return {
            "delta_table":    rows,
            "improvements":   improvements,
            "deteriorations": deteriorations,
            "unchanged":      unchanged,
            "derived":        derived,
            "verdict":        verdict,
            "has_previous":   bool(previous),
        }

    # ── 스냅샷 I/O ─────────────────────────────────────────────────────────

    @classmethod
    def _load_latest_snapshot(cls, company_name: str) -> dict:
        """output/snapshots/ 에서 가장 최근 스냅샷 로드."""
        os.makedirs(cls.SNAPSHOT_DIR, exist_ok=True)
        pattern = os.path.join(cls.SNAPSHOT_DIR, f"{company_name}_*.json")
        files   = sorted(glob.glob(pattern))
        if not files:
            return {}
        with open(files[-1], encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def _save_snapshot(cls, company_name: str, data: dict) -> str:
        """현재 COMPANY_DATA를 JSON 스냅샷으로 저장."""
        os.makedirs(cls.SNAPSHOT_DIR, exist_ok=True)
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(cls.SNAPSHOT_DIR, f"{company_name}_{ts}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    # ── 공개 인터페이스 ────────────────────────────────────────────────────

    def analyze(self, company_data: dict) -> str:
        """
        COMPANY_DATA를 받아 Delta 분석 보고서를 반환합니다.
        실행 후 현재 스냅샷을 output/snapshots/ 에 저장합니다.
        """
        company_name = company_data.get("company_name", "대상법인")

        previous = self._load_latest_snapshot(company_name)
        has_prev = bool(previous)

        # 현재 스냅샷 저장 (이번 실행 결과를 다음 비교에 활용)
        self._save_snapshot(company_name, company_data)

        current_disp = {k: company_data.get(k) for k, *_ in self.KPI_KEYS}
        previous_disp = {k: previous.get(k) for k, *_ in self.KPI_KEYS} if has_prev else {}

        # 파생 지표 계산
        td  = company_data.get("total_debt", 0)
        te  = company_data.get("total_equity", 1)
        ca  = company_data.get("current_assets", 0)
        cl  = company_data.get("current_liabilities", 1)
        ni  = company_data.get("net_income", 0)
        rev = company_data.get("revenue", 1)

        context = (
            f"[분석 대상] {company_name}\n"
            f"[현재 스냅샷] {json.dumps(current_disp, ensure_ascii=False)}\n"
            f"[이전 스냅샷] {'없음 (첫 실행)' if not has_prev else json.dumps(previous_disp, ensure_ascii=False)}\n\n"
            f"[현재 파생 지표]\n"
            f"  부채비율: {td/te*100:.0f}% | 유동비율: {ca/cl*100:.0f}% | "
            f"이자보상배율: {ni/(td*0.05) if td else 99:.1f}배 | "
            f"영업이익률: {ni/rev*100:.1f}%\n\n"
            + ("위 두 스냅샷을 비교하여 Delta 분석 보고서를 작성하십시오."
               if has_prev else
               "이전 스냅샷이 없습니다. 현재 지표를 기준선(Baseline)으로 설정하고 "
               "향후 모니터링 시 추적해야 할 핵심 KPI 목록과 경보 임계값을 제시하십시오.")
        )
        return self.run(context, reset=True)


# ═══════════════════════════════════════════════════════════════════════════
# ScenarioAgent
# ═══════════════════════════════════════════════════════════════════════════

_SCENARIO_SYS = """당신은 중소기업 절세·구조설계 시나리오 전문 컨설턴트입니다.
임원퇴직금, 가업승계(상속·증여), 자녀법인 3개 시나리오를 수치로 시뮬레이션합니다.

【출력 형식 — 반드시 준수】
## 3대 절세 시나리오 시뮬레이션

---

### 시나리오 A — 임원퇴직금 설계
| 항목 | 금액 | 산출 근거 |
...
**절세 효과:** ○○원 / **리스크:** ○○

---

### 시나리오 B — 가업상속공제 활용 승계
| 항목 | 금액 | 산출 근거 |
...
**절세 효과:** ○○원 / **리스크:** ○○

---

### 시나리오 C — 자녀법인 설립 활용
| 항목 | 금액 | 산출 근거 |
...
**절세 효과:** ○○원 / **리스크:** ○○

---

### 시나리오 비교 종합
| 시나리오 | 절세 효과 | 실행 난이도 | 권고 우선순위 |
...

### 최적 시나리오 권고
(1~2문장 결론)"""


class ScenarioAgent(BaseAgent):
    """임원퇴직금 / 가업승계 / 자녀법인 3개 시나리오 수치 시뮬레이션 에이전트."""

    name  = "ScenarioAgent"
    role  = "절세·구조설계 시나리오 시뮬레이션 전문가"
    model = MODEL
    system_prompt = _SCENARIO_SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose=verbose)
        self.tools = [
            {
                "name": "simulate_retirement_allowance",
                "description": "임원 퇴직금 한도·절세액을 계산합니다 (법인세법 §26).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "avg_salary_3yr":   {"type": "number", "description": "최종 3년 평균 급여(원)"},
                        "tenure_years":     {"type": "number", "description": "근속연수(년)"},
                        "multiplier":       {"type": "number", "description": "정관 배율 (미설정 시 1)"},
                        "tax_rate":         {"type": "number", "description": "법인세 실효세율 (0~1)"},
                    },
                    "required": ["avg_salary_3yr", "tenure_years", "multiplier", "tax_rate"],
                },
            },
            {
                "name": "simulate_succession",
                "description": "가업상속공제 적용 시 상속세를 계산합니다 (상증법 §18의2).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "business_value":   {"type": "number", "description": "가업 자산 가액(원)"},
                        "years_in_operation": {"type": "number", "description": "업력(년)"},
                        "total_estate":     {"type": "number", "description": "전체 상속재산(원)"},
                        "num_heirs":        {"type": "integer", "description": "상속인 수"},
                    },
                    "required": ["business_value", "years_in_operation", "total_estate", "num_heirs"],
                },
            },
            {
                "name": "simulate_child_company",
                "description": "자녀법인 설립을 통한 일감몰아주기·배당·주식 이전 절세 효과를 계산합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "transfer_revenue_ratio": {"type": "number",
                                                   "description": "자녀법인에 이전할 매출 비율(0~1)"},
                        "parent_revenue":         {"type": "number", "description": "모법인 연매출(원)"},
                        "child_net_margin":       {"type": "number",
                                                   "description": "자녀법인 예상 순이익률(0~1)"},
                        "parent_tax_rate":        {"type": "number",
                                                   "description": "모법인 법인세율(0~1)"},
                        "gift_tax_rate":          {"type": "number",
                                                   "description": "자녀 증여세 최고세율(0~1)"},
                        "stock_value_per_share":  {"type": "number",
                                                   "description": "모법인 1주당 평가액(원)"},
                        "shares_to_transfer":     {"type": "integer",
                                                   "description": "이전 대상 주식 수"},
                    },
                    "required": ["transfer_revenue_ratio", "parent_revenue", "child_net_margin",
                                 "parent_tax_rate", "gift_tax_rate",
                                 "stock_value_per_share", "shares_to_transfer"],
                },
            },
        ]

    # ── 툴 핸들러 ──────────────────────────────────────────────────────────

    def handle_tool(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "simulate_retirement_allowance":
            return self._sim_retirement(**tool_input)
        if tool_name == "simulate_succession":
            return self._sim_succession(**tool_input)
        if tool_name == "simulate_child_company":
            return self._sim_child_company(**tool_input)
        return {"error": f"알 수 없는 툴: {tool_name}"}

    def _sim_retirement(self, avg_salary_3yr: float, tenure_years: float,
                        multiplier: float, tax_rate: float) -> dict:
        """법인세법 §26 임원 퇴직금 한도 및 절세 계산."""
        limit = avg_salary_3yr / 10 * tenure_years * multiplier

        # 퇴직소득세 (퇴직소득 공제 후 세율 적용, 단순화)
        deduction = min(limit * 0.40, 12_000_000 * tenure_years)  # 근속연수 공제 근사
        taxable   = max(limit - deduction, 0)
        # 퇴직소득세율 누진 근사 (2024년 기준)
        if taxable <= 14_000_000:
            personal_tax = taxable * 0.06
        elif taxable <= 50_000_000:
            personal_tax = 840_000 + (taxable - 14_000_000) * 0.15
        elif taxable <= 88_000_000:
            personal_tax = 6_240_000 + (taxable - 50_000_000) * 0.24
        elif taxable <= 150_000_000:
            personal_tax = 15_360_000 + (taxable - 88_000_000) * 0.35
        else:
            personal_tax = 37_060_000 + (taxable - 150_000_000) * 0.38

        corp_tax_saving  = limit * tax_rate          # 법인세 절감
        net_saving       = corp_tax_saving - personal_tax

        return {
            "퇴직금_한도(원)":        round(limit),
            "법인세_절감액(원)":       round(corp_tax_saving),
            "퇴직소득세_추정(원)":     round(personal_tax),
            "순절세_효과(원)":         round(net_saving),
            "손금산입_가능_여부":       True,
            "근거_조문":              "법인세법 §26, 법인세법 시행령 §44",
            "주의사항":               "정관 퇴직금 규정 미비 시 배율 1 적용, 사전 정관 정비 필수",
        }

    def _sim_succession(self, business_value: float, years_in_operation: float,
                        total_estate: float, num_heirs: int) -> dict:
        """상증법 §18의2 가업상속공제 적용 시 상속세."""
        # 공제 한도: 업력별 (10년↑ 300억, 20년↑ 500억, 30년↑ 1000억)
        if years_in_operation >= 30:
            deduction_limit = 100_000_000_000
        elif years_in_operation >= 20:
            deduction_limit = 50_000_000_000
        else:
            deduction_limit = 30_000_000_000

        deduction_applied  = min(business_value, deduction_limit)
        taxable_estate     = max(total_estate - deduction_applied, 0)
        per_heir           = taxable_estate / num_heirs if num_heirs else taxable_estate

        # 상속세 누진세율 (2024년)
        def _inheritance_tax(base: float) -> float:
            if base <= 100_000_000:
                return base * 0.10
            elif base <= 500_000_000:
                return 10_000_000 + (base - 100_000_000) * 0.20
            elif base <= 1_000_000_000:
                return 90_000_000 + (base - 500_000_000) * 0.30
            elif base <= 3_000_000_000:
                return 240_000_000 + (base - 1_000_000_000) * 0.40
            else:
                return 1_040_000_000 + (base - 3_000_000_000) * 0.50

        tax_with_deduction    = _inheritance_tax(per_heir) * num_heirs
        tax_without_deduction = _inheritance_tax(total_estate / num_heirs) * num_heirs
        tax_saving            = tax_without_deduction - tax_with_deduction

        return {
            "가업자산_가액(원)":        round(business_value),
            "공제_한도(원)":            round(deduction_limit),
            "공제_적용액(원)":          round(deduction_applied),
            "공제_후_과세표준(원)":      round(taxable_estate),
            "공제_적용_상속세(원)":      round(tax_with_deduction),
            "공제_미적용_상속세(원)":    round(tax_without_deduction),
            "절세_효과(원)":            round(tax_saving),
            "업력_요건":               f"{years_in_operation:.0f}년 (10년 이상 요건 충족)" if years_in_operation >= 10 else "미충족",
            "근거_조문":               "상증법 §18의2, 조특법 §30의6",
            "사후_관리":               "상속 후 7년간 가업 유지·주식 처분 금지 의무",
        }

    def _sim_child_company(self, transfer_revenue_ratio: float, parent_revenue: float,
                           child_net_margin: float, parent_tax_rate: float,
                           gift_tax_rate: float, stock_value_per_share: float,
                           shares_to_transfer: int) -> dict:
        """자녀법인 설립 절세 시뮬레이션."""
        transferred_rev   = parent_revenue * transfer_revenue_ratio
        child_net_income  = transferred_rev * child_net_margin

        # 자녀법인 법인세 (중소기업 특례 22%)
        child_corp_tax_rate = 0.22 if child_net_income <= 200_000_000 else 0.22
        child_corp_tax      = child_net_income * child_corp_tax_rate

        # 모법인에서 유지했을 경우 세부담
        parent_tax_on_same  = transferred_rev * child_net_margin * parent_tax_rate
        corp_tax_saving     = parent_tax_on_same - child_corp_tax

        # 주식 이전 절세 — 자녀법인 주가 낮을 때 증여
        stock_transfer_value = stock_value_per_share * shares_to_transfer
        # 증여세 공제: 직계비속 5,000만원 공제
        gift_taxable   = max(stock_transfer_value - 50_000_000, 0)
        gift_tax_paid  = gift_taxable * gift_tax_rate

        # 일감몰아주기 증여세 리스크 (특수관계 법인 거래 비율 > 30%)
        illicit_risk_note = (
            "일감몰아주기 증여세 과세 대상 (상증법 §45의3): 수혜법인 세후소득 × 초과비율 × 주주 지분율"
            if transfer_revenue_ratio > 0.30 else
            "일감몰아주기 과세 기준선(30%) 이하 — 현재 과세 대상 아님"
        )

        return {
            "자녀법인_이전_매출(원)":    round(transferred_rev),
            "자녀법인_순이익_추정(원)":  round(child_net_income),
            "자녀법인_법인세(원)":       round(child_corp_tax),
            "모법인_동일소득_세부담(원)": round(parent_tax_on_same),
            "법인세_절감액(원)":         round(corp_tax_saving),
            "주식이전_평가액(원)":        round(stock_transfer_value),
            "증여세_추정(원)":           round(gift_tax_paid),
            "순절세_효과(원)":           round(corp_tax_saving - gift_tax_paid),
            "일감몰아주기_리스크":        illicit_risk_note,
            "근거_조문":                "상증법 §45의3, 법인세법 §52, 조특법 §7의4",
            "권고":                     "자녀법인 설립 전 일감몰아주기 과세 검토 및 독립거래 가격 설정 필수",
        }

    # ── 공개 인터페이스 ────────────────────────────────────────────────────

    def analyze(self, company_data: dict) -> str:
        """
        COMPANY_DATA를 받아 3개 시나리오 수치 시뮬레이션 보고서를 반환합니다.
        """
        n   = company_data.get("company_name", "대상법인")
        rev = company_data.get("revenue", 0)
        ni  = company_data.get("net_income", 0)
        ti  = company_data.get("taxable_income", 0)
        ta  = company_data.get("total_assets", 0)
        te  = company_data.get("total_equity", 0)
        bv  = company_data.get("business_value", 0)
        yrs = company_data.get("years_in_operation", 0)
        ceo = company_data.get("ceo_age", 55)
        pp  = company_data.get("provisional_payment", 0)
        nas = company_data.get("net_asset_per_share", 0)
        nis = company_data.get("net_income_per_share", 0)
        shr = company_data.get("shares_outstanding", 0)
        succ= company_data.get("successor_name", "자녀")

        # 법인세 실효세율 추정
        corp_tax_rate = 0.22 if ti <= 2_000_000_000 else 0.24

        # 임원퇴직금 가정: 대표 급여 연 1.2억 (5천만/월 × 1/4), 정관배율 3
        avg_salary = rev * 0.015  # 매출의 1.5% 근사

        # 주식 평가액 (보충적 평가)
        stock_val = nas * 0.4 + nis * 0.6 if (nas and nis) else nas

        query = (
            f"[분석 대상] {n} | 대표 {ceo}세 | 후계자: {succ}\n"
            f"[재무 현황] 매출: {rev:,.0f}원 | 순이익: {ni:,.0f}원 | "
            f"과세표준: {ti:,.0f}원 | 법인세율: {corp_tax_rate*100:.0f}%\n"
            f"[승계 현황] 가업자산: {bv:,.0f}원 | 업력: {yrs}년 | "
            f"주식평가액: {stock_val:,.0f}원/주 | 발행주식: {shr:,}주\n"
            f"[부채·현안] 가지급금: {pp:,.0f}원\n\n"
            f"시나리오 A — 임원퇴직금: 대표 근속 {yrs}년, 평균급여 {avg_salary:,.0f}원, "
            f"정관배율 3배 기준 한도·절세액을 산출하십시오.\n"
            f"시나리오 B — 가업상속공제: 가업자산 {bv:,.0f}원, 업력 {yrs}년, "
            f"전체 상속재산 {ta:,.0f}원 기준 공제 적용 시 절세액을 산출하십시오.\n"
            f"시나리오 C — 자녀법인 설립: 매출 20% 이전, 순이익률 15%, "
            f"주식 {shr//4:,}주 증여 기준 절세 효과와 일감몰아주기 리스크를 분석하십시오."
        )
        return self.run(query, reset=True)
