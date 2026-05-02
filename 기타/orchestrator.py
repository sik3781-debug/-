"""
orchestrator.py
===============
16개 전문 에이전트 완전 병렬 실행 + 3개 검증 에이전트 병렬 검증 + ReportAgent 통합 보고

실행 흐름:
  Phase 1 ── 16개 에이전트 병렬 실행 (ThreadPoolExecutor max_workers=2, 배치)
  Phase 2 ── 3개 검증 에이전트 병렬 검증
  Phase 3 ── ReportAgent 최종 통합 보고서 생성
  Phase 4 ── PPT 자동 변환 (report_to_ppt)
"""

from __future__ import annotations

import sys
import time
import math
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout
from dataclasses import dataclass, field
from typing import Any

from agents.base_agent import BaseAgent, MODEL
from agents.consulting_agents import TaxAgent, StockAgent, SuccessionAgent, FinanceAgent
from agents.legal_agent import LegalAgent
from agents.patent_agent import PatentAgent
from agents.labor_agent import LaborAgent
from agents.industry_agent import IndustryAgent
from agents.web_research_agent import WebResearchAgent
from agents.policy_funding_agent import PolicyFundingAgent
from agents.cash_flow_agent import CashFlowAgent
from agents.credit_rating_agent import CreditRatingAgent
from agents.real_estate_agent import RealEstateAgent
from agents.insurance_agent import InsuranceAgent
from agents.ma_valuation_agent import MAValuationAgent
from agents.esg_risk_agent import ESGRiskAgent
from agents.verify_tax import VerifyTax, VerifyOps, VerifyStrategy, VerifyResult
from agents.all_agents import (
    MonitorAgent, ScenarioAgent,
    DataValidationAgent, TaxLawUpdateAgent, AutoFixAgent,
)
from report_to_ppt import build_ppt

MAX_WORKERS_PHASE1 = 4   # Phase 1 전문 에이전트 병렬도
MAX_WORKERS_PHASE2 = 3   # Phase 2 검증 에이전트 병렬도
AGENT_TIMEOUT    = 180   # 에이전트 1개당 최대 대기 시간(초)
BATCH_BASE_SLEEP =  8    # 배치 간 기본 대기 시간(초) — 지수 백오프 기준

# ──────────────────────────────────────────────────────────────────────────
# 유틸리티
# ──────────────────────────────────────────────────────────────────────────

def _batch_sleep(attempt: int, base: float = BATCH_BASE_SLEEP) -> None:
    """배치 간 지수 백오프 대기. attempt=0 → base초, attempt=1 → base*2초, …"""
    delay = base * math.pow(2, attempt)
    delay = min(delay, 60.0)  # 최대 60초 캡
    print(f"  [배치 대기] {delay:.0f}초 (시도 #{attempt + 1})")
    time.sleep(delay)


# ──────────────────────────────────────────────────────────────────────────
# 쿼리 빌더 — COMPANY_DATA → 에이전트별 맞춤 질의
# ──────────────────────────────────────────────────────────────────────────

def build_queries(data: dict) -> dict[str, str]:
    """COMPANY_DATA를 받아 각 에이전트에 최적화된 질의문을 생성한다."""
    n = data.get("company_name", "대상법인")
    ind = data.get("industry", "제조업")
    rev = data.get("revenue", 0)
    emp = data.get("employees", 0)
    ti = data.get("taxable_income", 0)
    ta = data.get("total_assets", 0)
    te = data.get("total_equity", 0)
    td = data.get("total_debt", 0)
    ca = data.get("current_assets", 0)
    cl = data.get("current_liabilities", 0)
    ni = data.get("net_income", 0)
    yrs = data.get("years_in_operation", 0)
    rd = data.get("rd_expense", 0)
    pat = data.get("patents", 0)
    pp = data.get("provisional_payment", 0)
    nas = data.get("net_asset_per_share", 0)
    nis = data.get("net_income_per_share", 0)
    bv = data.get("business_value", 0)
    ceo_age = data.get("ceo_age", 55)
    re_val = data.get("real_estate", {}).get("value", 0)
    re_type = data.get("real_estate", {}).get("type", "공장")
    customers = data.get("main_customers", [])
    concerns = "\n".join(f"- {c}" for c in data.get("concerns", []))

    brief = (
        f"[기업개요] {n} | 업종: {ind} | 업력: {yrs}년 | 임직원: {emp}명 | "
        f"연매출: {rev:,.0f}원 | 과세표준: {ti:,.0f}원\n"
        f"[재무현황] 총자산 {ta:,.0f}원 | 자기자본 {te:,.0f}원 | 총부채 {td:,.0f}원 | "
        f"유동자산 {ca:,.0f}원 | 유동부채 {cl:,.0f}원 | 순이익 {ni:,.0f}원\n"
        f"[주요현안] {concerns}"
    )

    debt_ratio = td / te * 100 if te else 999
    current_ratio = ca / cl * 100 if cl else 999
    operating_margin = ni / rev * 100 if rev else 0
    interest_coverage = ni / (td * 0.05) if td else 99
    ebitda = ni * 1.3  # 단순 추정

    return {
        "TaxAgent": (
            f"{brief}\n\n"
            f"과세표준 {ti:,.0f}원 기준 법인세 절세 전략 3가지와 "
            f"가지급금 {pp:,.0f}원 해결 방안을 제시하시오."
        ),
        "StockAgent": (
            f"{brief}\n\n"
            f"1주당 순자산가치 {nas:,.0f}원, 순손익가치 {nis:,.0f}원 (일반법인). "
            f"비상장주식 보충적 평가와 주식 이동 전략, 차명주식 해소 방안을 분석하시오."
        ),
        "SuccessionAgent": (
            f"{brief}\n\n"
            f"업력 {yrs}년, 가업자산 {bv:,.0f}원, 대표 {ceo_age}세. "
            f"가업상속공제 요건·한도와 자녀법인 활용 사전 승계 전략을 제시하시오."
        ),
        "FinanceAgent": (
            f"{brief}\n\n"
            f"부채비율 {debt_ratio:.0f}%, 유동비율 {current_ratio:.0f}%. "
            f"재무구조 종합 진단과 3단계 개선 로드맵을 제시하시오."
        ),
        "LegalAgent": (
            f"{brief}\n\n"
            f"법인 운영 중 상법 절차 위반 리스크, 특수관계인 거래 공정거래법 리스크, "
            f"차명주식 명의신탁 형사 리스크를 진단하고 해소 방안을 제시하시오."
        ),
        "PatentAgent": (
            f"{brief}\n\n"
            f"보유 특허 {pat}건, R&D 지출 {rd:,.0f}원. "
            f"R&D 세액공제 최적화 전략, 기술보증기금 활용, 특허권 법인 이전 방안을 제시하시오."
        ),
        "LaborAgent": (
            f"{brief}\n\n"
            f"임직원 {emp}명, 업종: {ind}. "
            f"통상임금 적정성, 퇴직금 적립 현황, 4대보험 두루누리 활용, "
            f"중대재해처벌법 대응 현황을 진단하시오."
        ),
        "IndustryAgent": (
            f"업종: {ind}, 매출: {rev:,.0f}원, 임직원: {emp}명. "
            f"동종업계 재무 벤치마크(부채비율·영업이익률·ROE)와 "
            f"최근 세무조사 트렌드를 분석하시오."
        ),
        "WebResearchAgent": (
            f"기업명: {n}, 업종: {ind}, 주요 고객사: {', '.join(customers)}. "
            f"해당 기업 및 업계 최신 동향, 특허청 정보, 주요 고객사 공급망 요건을 조사하시오."
        ),
        "PolicyFundingAgent": (
            f"{brief}\n\n"
            f"현재 부채비율 {debt_ratio:.0f}%, 임직원 {emp}명, 업종: {ind}. "
            f"신청 가능한 정책자금, 바우처, 기업인증 혜택을 금리·한도와 함께 제시하시오."
        ),
        "CashFlowAgent": (
            f"{brief}\n\n"
            f"월 평균 매출 {rev/12:,.0f}원, 유동비율 {current_ratio:.0f}%. "
            f"12개월 현금흐름 시뮬레이션과 흑자도산 리스크 진단, 운전자본 개선 방안을 제시하시오."
        ),
        "CreditRatingAgent": (
            f"{brief}\n\n"
            f"부채비율 {debt_ratio:.0f}%, 유동비율 {current_ratio:.0f}%, "
            f"영업이익률 {operating_margin:.1f}%, 이자보상배율 {interest_coverage:.1f}배. "
            f"현재 신용등급 추정과 등급 상승을 통한 금리 절감 전략을 제시하시오."
        ),
        "RealEstateAgent": (
            f"{brief}\n\n"
            f"{re_type} 자산 {re_val:,.0f}원. "
            f"법인 vs 개인 보유 세금 비교, 공장 매각 최적화 전략, 임대차 리스크를 분석하시오."
        ),
        "InsuranceAgent": (
            f"{brief}\n\n"
            f"대표이사 {ceo_age}세, 승계 계획 미비. "
            f"CEO 유고 리스크 헷지, 임원 퇴직금 재원 보험 설계, D&O 보험 필요성을 진단하시오."
        ),
        "MAValuationAgent": (
            f"{brief}\n\n"
            f"당기순이익 {ni:,.0f}원, EBITDA 추정 {ebitda:,.0f}원, 총부채 {td:,.0f}원. "
            f"DCF·PER·EV/EBITDA 세 가지 방법론으로 기업가치를 산출하고 "
            f"외부 매각·투자유치 시 적정 가치 범위를 제시하시오."
        ),
        "ESGRiskAgent": (
            f"{brief}\n\n"
            f"임직원 {emp}명, 업종: {ind}, 주요 고객사: {', '.join(customers)}. "
            f"E·S·G 항목별 리스크 점수와 우선 개선 과제, EU CBAM 대응 전략을 제시하시오."
        ),
        # GROUP D — analyze(company_data) 인터페이스 사용 (쿼리는 내부 생성)
        "MonitorAgent":           "__USE_ANALYZE__",
        "ScenarioAgent":          "__USE_ANALYZE__",
        # GROUP E — 신규 에이전트 (analyze 인터페이스, 실행 시점은 오케스트레이터가 제어)
        "DataValidationAgent":    "__USE_ANALYZE__",
        "TaxLawUpdateAgent":      "__USE_ANALYZE__",
        "AutoFixAgent":           "__USE_ANALYZE__",
    }


# ──────────────────────────────────────────────────────────────────────────
# 에이전트 등록 테이블
# ──────────────────────────────────────────────────────────────────────────

def _build_agent_map(verbose: bool) -> dict[str, BaseAgent]:
    return {
        # GROUP A~C — 기존 16개 전문 에이전트
        "TaxAgent":         TaxAgent(verbose=verbose),
        "StockAgent":       StockAgent(verbose=verbose),
        "SuccessionAgent":  SuccessionAgent(verbose=verbose),
        "FinanceAgent":     FinanceAgent(verbose=verbose),
        "LegalAgent":       LegalAgent(verbose=verbose),
        "PatentAgent":      PatentAgent(verbose=verbose),
        "LaborAgent":       LaborAgent(verbose=verbose),
        "IndustryAgent":    IndustryAgent(verbose=verbose),
        "WebResearchAgent": WebResearchAgent(verbose=verbose),
        "PolicyFundingAgent": PolicyFundingAgent(verbose=verbose),
        "CashFlowAgent":    CashFlowAgent(verbose=verbose),
        "CreditRatingAgent": CreditRatingAgent(verbose=verbose),
        "RealEstateAgent":  RealEstateAgent(verbose=verbose),
        "InsuranceAgent":   InsuranceAgent(verbose=verbose),
        "MAValuationAgent": MAValuationAgent(verbose=verbose),
        "ESGRiskAgent":     ESGRiskAgent(verbose=verbose),
        # GROUP D — Delta 모니터링 + 시나리오 시뮬레이션
        "MonitorAgent":     MonitorAgent(verbose=verbose),
        "ScenarioAgent":    ScenarioAgent(verbose=verbose),
        # GROUP E — 유효성검사 / 세법업데이트 / AutoFix (오케스트레이터 직접 제어)
        "DataValidationAgent": DataValidationAgent(verbose=verbose),
        "TaxLawUpdateAgent":   TaxLawUpdateAgent(verbose=verbose),
        "AutoFixAgent":        AutoFixAgent(verbose=verbose),
    }


# ──────────────────────────────────────────────────────────────────────────
# 검증 그룹 매핑
# ──────────────────────────────────────────────────────────────────────────

VERIFY_GROUPS = {
    "VerifyTax":      ["TaxAgent", "FinanceAgent", "StockAgent", "SuccessionAgent"],
    "VerifyOps":      ["LegalAgent", "LaborAgent", "PatentAgent", "RealEstateAgent", "InsuranceAgent"],
    "VerifyStrategy": ["PolicyFundingAgent", "CashFlowAgent", "CreditRatingAgent",
                       "MAValuationAgent", "ESGRiskAgent", "IndustryAgent", "WebResearchAgent"],
}

# GROUP_D — Delta 모니터링 + 시나리오 시뮬레이션 (Phase 1 마지막 배치)
GROUP_D = ["MonitorAgent", "ScenarioAgent"]

# GROUP_E — 신규 제어 에이전트 (오케스트레이터가 실행 시점 직접 제어)
#   DataValidationAgent : Phase 1 시작 전 (분석 최우선)
#   TaxLawUpdateAgent   : Phase 2 첫 번째
#   AutoFixAgent        : Phase 3 검증 직후


# ──────────────────────────────────────────────────────────────────────────
# ReportAgent
# ──────────────────────────────────────────────────────────────────────────

class ReportAgent(BaseAgent):
    name = "ReportAgent"
    role = "최종 통합 보고서 작성 전문가"
    system_prompt = (
        "당신은 중소기업 경영컨설팅 통합 보고서 작성 전문가입니다.\n"
        "16개 전문 에이전트의 분석 결과와 3개 검증 결과를 종합하여 "
        "경영진 보고용 핵심 요약 보고서를 작성하십시오.\n\n"
        "【보고서 구조】\n"
        "1. 경영 현황 종합 진단 (신호등: RED/YELLOW/GREEN)\n"
        "2. 최우선 해결과제 TOP 5 (즉시 실행)\n"
        "3. 중기 전략 방향 (3~12개월)\n"
        "4. 예상 절세·절감 효과 총계\n"
        "5. 리스크 요약 (법률·세무·재무·운영)\n\n"
        "임원 보고용으로 간결하게 작성하십시오. 각 항목 3줄 이내."
    )

    def generate_report(self, company_name: str,
                        agent_results: dict[str, str],
                        verify_results: dict[str, VerifyResult]) -> str:
        # 요약 입력 구성 (토큰 절약)
        # 에이전트당 400자로 압축하여 전체 포함 (토큰 균형)
        summaries = []
        for name, result in agent_results.items():
            summaries.append(f"[{name}]\n{result[:400]}")

        verify_summary = "\n".join(
            f"[{k}] {v.status} {v.score}/100" for k, v in verify_results.items()
        )

        prompt = (
            f"분석 대상 기업: {company_name}\n\n"
            f"=== 에이전트 분석 요약 ({len(summaries)}개 전체) ===\n"
            + "\n\n".join(summaries)
            + f"\n\n=== 검증 결과 ===\n{verify_summary}\n\n"
            "위 내용을 종합하여 경영진 보고용 통합 보고서를 작성하십시오."
        )
        return self.run(prompt, reset=True)


# ──────────────────────────────────────────────────────────────────────────
# 메인 오케스트레이터
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class OrchestratorResult:
    company_name: str
    agent_results: dict[str, str] = field(default_factory=dict)
    agent_errors: dict[str, str] = field(default_factory=dict)
    verify_results: dict[str, VerifyResult] = field(default_factory=dict)
    final_report: str = ""
    elapsed_seconds: float = 0.0
    ppt_path: str = ""  # Phase 4 생성된 PPT 파일 경로

    def print_summary(self) -> None:
        sep = "=" * 72
        thin = "-" * 72
        print(f"\n{sep}")
        print(f"  종합 컨설팅 결과 — {self.company_name}")
        print(f"  실행 시간: {self.elapsed_seconds:.1f}초  |  에이전트: {len(self.agent_results)}개 완료 (DataValidation·TaxLawUpdate·AutoFix 포함)")
        print(sep)

        for name, result in self.agent_results.items():
            print(f"\n{'#'*72}")
            print(f"# [{name}]")
            print(thin)
            print(result[:2000])
            if len(result) > 2000:
                print(f"  ... (총 {len(result)}자, 일부 생략)")

        if self.agent_errors:
            print(f"\n{thin}")
            print("[ 실행 오류 에이전트 ]")
            for name, err in self.agent_errors.items():
                print(f"  {name}: {err[:100]}")

        print(f"\n{sep}")
        print("[ 검증 결과 요약 ]")
        print(f"{'검증기':<20} {'상태':<10} {'점수':>8}")
        print(thin)
        for vname, vr in self.verify_results.items():
            icon = {"PASS": "[OK]", "WARNING": "[!!]", "FAIL": "[NG]"}.get(vr.status, "[?]")
            print(f"{vname:<20} {icon} {vr.status:<6} {vr.score:>5}/100")

        print(f"\n{sep}")
        print("[ 최종 통합 보고서 ]")
        print(thin)
        print(self.final_report)

        if self.ppt_path:
            print(f"\n{thin}")
            print(f"[ PPT 저장 경로 ]  {self.ppt_path}")
        print(sep)


class Orchestrator:
    """16개 에이전트 + 3개 검증 + 1개 리포트 통합 실행기."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose

    def _run_agent_safe(self, agent: BaseAgent, query: str,
                        company_data: dict | None = None) -> tuple[str, str | None]:
        """에이전트 실행 (오류 격리).
        query == '__USE_ANALYZE__' 이면 agent.analyze(company_data) 호출."""
        try:
            if query == "__USE_ANALYZE__" and hasattr(agent, "analyze") and company_data:
                result = agent.analyze(company_data)
            else:
                result = agent.run(query, reset=True)
            return result, None
        except Exception as e:
            return "", str(e)

    def run(self, company_data: dict) -> OrchestratorResult:
        company_name = company_data.get("company_name", "대상법인")
        start = time.time()

        print(f"\n{'='*72}")
        print(f"  중소기업 컨설팅 에이전트 시스템 v3")
        print(f"  대상: {company_name}  |  에이전트: 21개(GROUP E 포함) + 검증 3개 + AutoFix")
        print(f"{'='*72}\n")

        agents  = _build_agent_map(self.verbose)
        queries = build_queries(company_data)

        agent_results: dict[str, str] = {}
        agent_errors:  dict[str, str] = {}

        # ── Phase 0: DataValidationAgent — 분석 시작 전 입력값 검증 ──────
        print("[Phase 0] DataValidationAgent — COMPANY_DATA 유효성 검사 중...")
        val_agent = agents["DataValidationAgent"]
        val_result, val_err = self._run_agent_safe(val_agent, "__USE_ANALYZE__", company_data)
        if val_err:
            agent_errors["DataValidationAgent"] = val_err
            print(f"  [DataValidationAgent] 오류: {val_err[:80]}")
        else:
            agent_results["DataValidationAgent"] = val_result
            # 오류 판정 포함 여부 확인 (경고 시에도 계속 진행)
            is_blocked = "오류로 중단 권고" in val_result
            status_mark = "[중단 권고]" if is_blocked else "[정상/경고]"
            print(f"  [DataValidationAgent] {status_mark} 완료 ({len(val_result)}자)")
            if is_blocked:
                print("  ※ 입력 데이터에 치명적 오류가 있습니다. 수정 후 재실행을 권고합니다.")
                print("  ※ 계속 진행하려면 아래 분석을 참고하십시오.\n")
        print()

        # ── Phase 1: 에이전트 배치 병렬 실행 ────────────────────────────
        # GROUP E (DataValidation / TaxLawUpdate / AutoFix)는 오케스트레이터가 직접 제어
        # GROUP D (Monitor / Scenario)는 A~C 완료 후 명시적 마지막 배치로 실행
        PHASE1_EXCLUDE = {"DataValidationAgent", "TaxLawUpdateAgent", "AutoFixAgent"}
        print("[Phase 1] 전문 에이전트 배치 실행 중 (그룹당 4개, GROUP_D 명시적 마지막 배치)...")

        # GROUP A~C: 16개 전문 에이전트 (GROUP_D 제외)
        group_ac_items = [
            (name, agent)
            for name, agent in agents.items()
            if name in queries and name not in PHASE1_EXCLUDE and name not in GROUP_D
        ]
        # GROUP D: MonitorAgent / ScenarioAgent — A~C 완료 후 실행
        group_d_items = [
            (name, agents[name])
            for name in GROUP_D
            if name in agents and name in queries
        ]

        group_size   = 4
        groups_ac    = [group_ac_items[i:i+group_size] for i in range(0, len(group_ac_items), group_size)]
        all_groups   = groups_ac + ([group_d_items] if group_d_items else [])
        done_count   = 0
        total_agents = len(group_ac_items) + len(group_d_items)

        for g_idx, group in enumerate(all_groups):
            is_group_d = (g_idx == len(all_groups) - 1 and group_d_items)
            label = "GROUP D" if is_group_d else f"그룹 {g_idx + 1}/{len(all_groups)}"
            if g_idx > 0:
                _batch_sleep(attempt=g_idx - 1)
            print(f"  --- [{label}] 실행 ({len(group)}개 에이전트) ---")
            with ThreadPoolExecutor(max_workers=MAX_WORKERS_PHASE1) as ex:
                futures = {
                    ex.submit(self._run_agent_safe, agent, queries[name], company_data): name
                    for name, agent in group
                }
                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        result, err = future.result(timeout=AGENT_TIMEOUT)
                    except FuturesTimeout:
                        result, err = "", f"타임아웃 ({AGENT_TIMEOUT}초 초과)"
                    done_count += 1
                    if err:
                        agent_errors[name] = err
                        print(f"  [{done_count:02d}/{total_agents}] {name} — 오류: {err[:80]}")
                    else:
                        agent_results[name] = result
                        print(f"  [{done_count:02d}/{total_agents}] {name} — 완료 ({len(result)}자)")

        phase1_time = time.time() - start
        print(f"\n[Phase 1 완료] {len(agent_results)}개 성공 / {len(agent_errors)}개 실패 ({phase1_time:.1f}초)\n")

        # ── Phase 2: TaxLawUpdateAgent (첫 번째) + 검증 에이전트 3개 병렬 ─
        print("[Phase 2-A] TaxLawUpdateAgent — 최신 세법 개정사항 검색 중...")
        tax_update_agent = agents["TaxLawUpdateAgent"]
        tax_update_result, tax_update_err = self._run_agent_safe(
            tax_update_agent, "__USE_ANALYZE__", company_data
        )
        if tax_update_err:
            agent_errors["TaxLawUpdateAgent"] = tax_update_err
            print(f"  [TaxLawUpdateAgent] 오류: {tax_update_err[:80]}")
        else:
            agent_results["TaxLawUpdateAgent"] = tax_update_result
            print(f"  [TaxLawUpdateAgent] 완료 ({len(tax_update_result)}자)")
            # 세법 업데이트 결과를 TaxAgent 분석 결과에 컨텍스트로 병합
            # → VerifyTax 및 ReportAgent가 최신 개정사항을 반영하여 검증·보고
            if "TaxAgent" in agent_results and tax_update_result.strip():
                agent_results["TaxAgent"] = (
                    agent_results["TaxAgent"]
                    + "\n\n【최신 세법 개정사항 (TaxLawUpdateAgent)】\n"
                    + tax_update_result[:1000]
                )
                print("  [TaxLawUpdateAgent] 세법 업데이트 → TaxAgent 컨텍스트 병합 완료")
        print()

        print("[Phase 2-B] 검증 에이전트 3개 병렬 실행 중...")
        verifiers = {
            "VerifyTax":      VerifyTax(verbose=self.verbose),
            "VerifyOps":      VerifyOps(verbose=self.verbose),
            "VerifyStrategy": VerifyStrategy(verbose=self.verbose),
        }

        def run_verify(vname: str, verifier) -> tuple[str, VerifyResult]:
            group = VERIFY_GROUPS[vname]
            combined_q = f"기업: {company_name}\n업종: {company_data.get('industry', '')}"
            combined_r = "\n\n".join(
                f"[{n}]\n{agent_results.get(n, '결과 없음')[:600]}"
                for n in group if n in agent_results
            )
            try:
                vr = verifier.verify(combined_q, combined_r)
            except Exception as e:
                vr = VerifyResult(60, "WARNING", [str(e)], "오류 발생", "", vname)
            return vname, vr

        verify_results: dict[str, VerifyResult] = {}
        with ThreadPoolExecutor(max_workers=MAX_WORKERS_PHASE2) as ex:
            futs = {ex.submit(run_verify, vn, v): vn for vn, v in verifiers.items()}
            for f in as_completed(futs):
                try:
                    vname, vr = f.result(timeout=AGENT_TIMEOUT)
                except FuturesTimeout:
                    vname = futs[f]
                    vr = VerifyResult(50, "WARNING", [f"타임아웃 ({AGENT_TIMEOUT}초 초과)"], "타임아웃으로 검증 미완료", "", vname)
                verify_results[vname] = vr
                icon = {"PASS": "[OK]", "WARNING": "[!!]", "FAIL": "[NG]"}.get(vr.status, "[?]")
                print(f"  {vname}: {icon} {vr.status} {vr.score}/100")

        phase2_time = time.time() - start - phase1_time
        print(f"\n[Phase 2 완료] ({phase2_time:.1f}초)\n")

        # ── Phase 3-A: AutoFixAgent — FAIL 항목 분석·재실행 루프 ─────────
        print("[Phase 3-A] AutoFixAgent — 검증 FAIL 항목 분석 및 재실행 중...")
        autofix_agent: AutoFixAgent = agents["AutoFixAgent"]

        def _agent_runner(agent_name: str, query: str, cdata: dict) -> str:
            """AutoFixAgent가 요청하는 에이전트 재실행 헬퍼."""
            target_agent = agents.get(agent_name)
            if target_agent is None:
                return ""
            result, err = self._run_agent_safe(target_agent, query, cdata)
            return result if not err else ""

        updated_results, fix_log = autofix_agent.run_autofix(
            verify_results=verify_results,
            agent_results=agent_results,
            company_data=company_data,
            agent_runner=_agent_runner,
            queries=queries,
        )
        agent_results = updated_results
        for log_line in fix_log:
            print(f"  {log_line}")
        agent_results["AutoFixAgent"] = "\n".join(fix_log)
        print()

        # ── Phase 3-B: ReportAgent 최종 통합 ─────────────────────────────
        print("[Phase 3-B] ReportAgent 통합 보고서 작성 중...")
        try:
            reporter = ReportAgent(verbose=self.verbose)
            final_report = reporter.generate_report(company_name, agent_results, verify_results)
        except Exception as e:
            final_report = f"[보고서 생성 오류] {str(e)}"

        total_time = time.time() - start
        print(f"[Phase 3 완료] 총 실행 시간: {total_time:.1f}초\n")

        # ── Phase 4: PPT 자동 생성 ──────────────────────────────────────
        print("[Phase 4] PPT 보고서 자동 생성 중...")
        ppt_path = ""
        try:
            import os
            output_dir = os.path.join(os.path.dirname(__file__), "output")
            verify_summary = "\n".join(
                f"{k}: {v.status} {v.score}/100" for k, v in verify_results.items()
            )
            ppt_path = build_ppt(
                company_name  = company_name,
                agent_results = agent_results,
                final_text    = final_report,
                verify_text   = verify_summary,
                output_dir    = output_dir,
            )
            print(f"[Phase 4 완료] {ppt_path}\n")
        except Exception as e:
            print(f"[Phase 4 오류] PPT 생성 실패: {e}\n")

        return OrchestratorResult(
            company_name=company_name,
            agent_results=agent_results,
            agent_errors=agent_errors,
            verify_results=verify_results,
            final_report=final_report,
            elapsed_seconds=total_time,
            ppt_path=ppt_path,
        )
