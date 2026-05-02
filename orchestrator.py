"""
orchestrator.py
===============
53개 전문 에이전트 완전 병렬 실행 + 3개 검증 에이전트 병렬 검증 + ReportAgent 통합 보고

에이전트 구성:
  GROUP A (4): TaxAgent·StockAgent·SuccessionAgent·FinanceAgent
  GROUP B (5): LegalAgent·PatentAgent·LaborAgent·RealEstateAgent·InsuranceAgent
  GROUP C (7): IndustryAgent·WebResearchAgent·PolicyFundingAgent·CashFlowAgent·
               CreditRatingAgent·MAValuationAgent·ESGRiskAgent
  GROUP D (3): MonitorAgent·ScenarioAgent·BusinessPlanAgent (analyze() 인터페이스)
  GROUP E (3): ProvisionalPaymentAgent·NomineeStockAgent·ExecutivePayAgent (전담)
  GROUP F (5): GiftTaxAgent·InheritanceTaxAgent·VATAgent·RDTaxCreditAgent·InvestTaxCreditAgent
  GROUP G (6): FinancialForecastAgent·CostAnalysisAgent·SocialInsuranceAgent·
               PerformancePayAgent·DividendPolicyAgent·RelatedPartyAgent
  GROUP H (6): GlobalExpansionAgent·DXAgent·SubcontractAgent·
               IPOAgent·FranchiseAgent·DebtRestructuringAgent
  GROUP I (8): ComplianceAgent·ContractReviewAgent·WorkingCapitalAgent·PrivacyAgent·
               HRDAgent·SupplyChainAgent·TradeAgent·VentureCapitalAgent
  INFRA  (6): DataValidationAgent·QueryClassifierAgent·RiskScoreAgent·SummaryAgent·
               VerifyFinance·VerifyCompliance

실행 흐름:
  Phase 1 ── 53개 에이전트 배치 병렬 실행 (ThreadPoolExecutor max_workers=2, 그룹 간 sleep)
  Phase 2 ── 3개 검증 에이전트 병렬 검증
  Phase 3 ── ReportAgent 최종 통합 보고서 생성
  Phase 4 ── PPT 자동 변환 (report_to_ppt)
"""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

from agents.base_agent import BaseAgent, MODEL
from agents.consulting_agents import TaxAgent, StockAgent, SuccessionAgent, FinanceAgent

# ──────────────────────────────────────────────────────────────────────────
# 에이전트별 모델 매핑
# ──────────────────────────────────────────────────────────────────────────

MODEL_MAP: dict[str, str] = {
    "DataValidationAgent":  "claude-haiku-4-5-20251001",
    "TaxLawUpdateAgent":    "claude-haiku-4-5-20251001",
    "AutoFixAgent":         "claude-haiku-4-5-20251001",
    "MonitorAgent":         "claude-haiku-4-5-20251001",
    "TaxAgent":             "claude-sonnet-4-6",
    "FinancialAgent":       "claude-sonnet-4-6",
    "ScenarioAgent":        "claude-sonnet-4-6",
    "VerifyAgent":          "claude-sonnet-4-6",
    "Orchestrator":         "claude-opus-4-6",
}
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
from agents.business_plan_agent import BusinessPlanAgent
from agents.provisional_payment_agent import ProvisionalPaymentAgent
from agents.nominee_stock_agent import NomineeStockAgent
from agents.executive_pay_agent import ExecutivePayAgent
from agents.gift_tax_agent import GiftTaxAgent
from agents.inheritance_tax_agent import InheritanceTaxAgent
from agents.vat_agent import VATAgent
from agents.rd_tax_credit_agent import RDTaxCreditAgent
from agents.invest_tax_credit_agent import InvestTaxCreditAgent
from agents.global_expansion_agent import GlobalExpansionAgent
from agents.dx_agent import DXAgent
from agents.subcontract_agent import SubcontractAgent
from agents.ipo_agent import IPOAgent
from agents.franchise_agent import FranchiseAgent
from agents.debt_restructuring_agent import DebtRestructuringAgent
from agents.financial_forecast_agent import FinancialForecastAgent
from agents.cost_analysis_agent import CostAnalysisAgent
from agents.social_insurance_agent import SocialInsuranceAgent
from agents.performance_pay_agent import PerformancePayAgent
from agents.dividend_policy_agent import DividendPolicyAgent
from agents.related_party_agent import RelatedPartyAgent
# GROUP I — 컴플라이언스·지원 전담 에이전트
from agents.compliance_agent import ComplianceAgent
from agents.contract_review_agent import ContractReviewAgent
from agents.working_capital_agent import WorkingCapitalAgent
from agents.privacy_agent import PrivacyAgent
from agents.hrd_agent import HRDAgent
from agents.supply_chain_agent import SupplyChainAgent
from agents.trade_agent import TradeAgent
from agents.venture_capital_agent import VentureCapitalAgent
# 6단계 인프라·검증 에이전트
from agents.verify_finance import VerifyFinance
from agents.verify_compliance import VerifyCompliance
from agents.data_validation_agent import DataValidationAgent
from agents.query_classifier_agent import QueryClassifierAgent
from agents.risk_score_agent import RiskScoreAgent
from agents.summary_agent import SummaryAgent
from agents.verify_tax import VerifyTax, VerifyOps, VerifyStrategy, VerifyResult
from agents.all_agents import MonitorAgent, ScenarioAgent
from report_to_ppt import build_ppt

MAX_WORKERS = 2


def extract_context(output: str) -> dict:
    lines = [l.strip() for l in output.split('\n') if l.strip()]
    return {
        "summary": ' '.join(lines[:3]),
        "key_metrics": [l for l in lines if any(c.isdigit() for c in l)][:10],
        "flags": [l for l in lines if any(
            kw in l for kw in ['위험', '주의', 'RISK', 'WARNING', 'FAIL', '오류']
        )]
    }


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
    # GROUP E 전담 에이전트 전용 데이터
    nominee_shares  = data.get("nominee_shares", 0)                   # 차명주식 주수
    nom_acq_year    = data.get("nominee_share_acquisition_year", 2010) # 차명주식 취득연도
    nom_face_val    = data.get("nominee_face_value", 5_000)            # 차명주식 액면가(원/주)
    ceo_salary      = data.get("ceo_salary", 0)                        # 대표이사 연봉
    ceo_tenure      = data.get("ceo_tenure", 10)                       # 대표이사 근속연수(년)
    has_retire_rule = data.get("retirement_pay_provision", False)      # 퇴직금 규정 유무

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
        # GROUP E — 가지급금·차명주식·임원보수 전담 에이전트
        "ProvisionalPaymentAgent": (
            f"{brief}\n\n"
            f"[가지급금 현황] 잔액 {pp:,.0f}원 | 인정이자율 4.6% 기준 연간 인정이자 "
            f"{pp * 0.046:,.0f}원 | 상여처분 시 대표이사 소득세 추가 부담 발생.\n\n"
            f"① 인정이자 정량 산출 (법인세법 시행규칙 §43)\n"
            f"② 급여증액·배당·직접상환·DES·자본감소 5가지 해소 방법별 법인+개인 합산 세부담 비교\n"
            f"③ 최적 해소 방법 추천 및 월별 단계적 실행 로드맵, 필요 증빙 서류를 제시하시오."
        ),
        "NomineeStockAgent": (
            f"{brief}\n\n"
            f"[차명주식 현황] 차명주식 {nominee_shares:,}주 | 액면가 {nom_face_val:,}원/주 | "
            f"취득연도 {nom_acq_year}년 | 1주당 현재 평가액 {nas:,.0f}원.\n\n"
            f"① 명의신탁 증여의제 과세위험 정량화 (상증세법 §45의2, 가산세 포함)\n"
            f"② 부과제척기간 분석 (일반 10년 / 부정행위 15년) — {nom_acq_year}년 취득 기준\n"
            f"③ 명의개서·증여·매매·자기주식취득 4가지 해소 방법별 세부담 비교\n"
            f"④ 과점주주 간주취득세 리스크 (지방세법 §7⑤) 주의사항을 포함하여 "
            f"최적 해소 전략과 실행 로드맵을 제시하시오."
        ),
        "ExecutivePayAgent": (
            f"{brief}\n\n"
            f"[임원 보수 현황] 대표이사 연봉 {ceo_salary:,.0f}원 | 근속연수 {ceo_tenure}년 | "
            f"퇴직금 규정 {'有' if has_retire_rule else '無'} | 대표이사 나이 {ceo_age}세.\n\n"
            f"① 임원 퇴직금 손금산입 한도 산출 (법인세법 시행령 §44②: 3년 평균급여 × 1/10 × 근속연수)\n"
            f"② 퇴직소득세 완전 계산 (근속연수공제 + 환산급여공제 적용)\n"
            f"③ 급여·배당·퇴직금 3가지 시나리오 세후 가처분소득 비교 → 최적 보수 믹스 추천\n"
            f"④ 퇴직금 규정 정비 방안과 중간정산 활용 타이밍을 제시하시오."
        ),
        # GROUP F — 세금·절세 전담 에이전트 (analyze() 인터페이스)
        "GiftTaxAgent":         "__USE_ANALYZE__",
        "InheritanceTaxAgent":  "__USE_ANALYZE__",
        "VATAgent":             "__USE_ANALYZE__",
        "RDTaxCreditAgent":     "__USE_ANALYZE__",
        "InvestTaxCreditAgent": "__USE_ANALYZE__",
        # GROUP H — 전략·성장 특화 에이전트 (analyze() 인터페이스)
        "GlobalExpansionAgent":    "__USE_ANALYZE__",
        "DXAgent":                 "__USE_ANALYZE__",
        "SubcontractAgent":        "__USE_ANALYZE__",
        "IPOAgent":                "__USE_ANALYZE__",
        "FranchiseAgent":          "__USE_ANALYZE__",
        "DebtRestructuringAgent":  "__USE_ANALYZE__",
        # GROUP G — 재무·HR 특화 에이전트 (analyze() 인터페이스)
        "FinancialForecastAgent": "__USE_ANALYZE__",
        "CostAnalysisAgent":      "__USE_ANALYZE__",
        "SocialInsuranceAgent":   "__USE_ANALYZE__",
        "PerformancePayAgent":    "__USE_ANALYZE__",
        "DividendPolicyAgent":    "__USE_ANALYZE__",
        "RelatedPartyAgent":      "__USE_ANALYZE__",
        # GROUP I — 컴플라이언스·지원 전담 에이전트 (analyze() 인터페이스)
        "ComplianceAgent":       "__USE_ANALYZE__",
        "ContractReviewAgent":   "__USE_ANALYZE__",
        "WorkingCapitalAgent":   "__USE_ANALYZE__",
        "PrivacyAgent":          "__USE_ANALYZE__",
        "HRDAgent":              "__USE_ANALYZE__",
        "SupplyChainAgent":      "__USE_ANALYZE__",
        "TradeAgent":            "__USE_ANALYZE__",
        "VentureCapitalAgent":   "__USE_ANALYZE__",
        # 인프라·검증 에이전트 (analyze() 인터페이스)
        "DataValidationAgent":   "__USE_ANALYZE__",
        "QueryClassifierAgent":  "__USE_ANALYZE__",
        "RiskScoreAgent":        "__USE_ANALYZE__",
        "SummaryAgent":          "__USE_ANALYZE__",
        "VerifyFinance":         "__USE_ANALYZE__",
        "VerifyCompliance":      "__USE_ANALYZE__",
        # GROUP D — analyze(company_data) 인터페이스 사용 (쿼리는 내부 생성)
        "MonitorAgent":      "__USE_ANALYZE__",
        "ScenarioAgent":     "__USE_ANALYZE__",
        # 사업계획서 전담 — analyze(company_data) 인터페이스 (유형 자동 판단 후 초안 작성)
        "BusinessPlanAgent": "__USE_ANALYZE__",
    }


# ──────────────────────────────────────────────────────────────────────────
# 에이전트 등록 테이블
# ──────────────────────────────────────────────────────────────────────────

def _build_agent_map(verbose: bool) -> dict[str, BaseAgent]:
    def _agent(name: str, cls) -> BaseAgent:
        a = cls(verbose=verbose)
        if name in MODEL_MAP:
            a.model = MODEL_MAP[name]
        return a

    return {
        # GROUP A~C — 기존 16개 전문 에이전트
        "TaxAgent":           _agent("TaxAgent",           TaxAgent),
        "StockAgent":         _agent("StockAgent",         StockAgent),
        "SuccessionAgent":    _agent("SuccessionAgent",    SuccessionAgent),
        "FinanceAgent":       _agent("FinanceAgent",       FinanceAgent),
        "LegalAgent":         _agent("LegalAgent",         LegalAgent),
        "PatentAgent":        _agent("PatentAgent",        PatentAgent),
        "LaborAgent":         _agent("LaborAgent",         LaborAgent),
        "IndustryAgent":      _agent("IndustryAgent",      IndustryAgent),
        "WebResearchAgent":   _agent("WebResearchAgent",   WebResearchAgent),
        "PolicyFundingAgent": _agent("PolicyFundingAgent", PolicyFundingAgent),
        "CashFlowAgent":      _agent("CashFlowAgent",      CashFlowAgent),
        "CreditRatingAgent":  _agent("CreditRatingAgent",  CreditRatingAgent),
        "RealEstateAgent":    _agent("RealEstateAgent",    RealEstateAgent),
        "InsuranceAgent":     _agent("InsuranceAgent",     InsuranceAgent),
        "MAValuationAgent":   _agent("MAValuationAgent",   MAValuationAgent),
        "ESGRiskAgent":             _agent("ESGRiskAgent",             ESGRiskAgent),
        "BusinessPlanAgent":        _agent("BusinessPlanAgent",        BusinessPlanAgent),
        # GROUP E — 전담 에이전트 (가지급금·차명주식·임원보수)
        "ProvisionalPaymentAgent":  _agent("ProvisionalPaymentAgent",  ProvisionalPaymentAgent),
        "NomineeStockAgent":        _agent("NomineeStockAgent",        NomineeStockAgent),
        "ExecutivePayAgent":        _agent("ExecutivePayAgent",        ExecutivePayAgent),
        # GROUP F — 세금·절세 전담 (증여세·상속세·VAT·R&D공제·투자공제)
        "GiftTaxAgent":             _agent("GiftTaxAgent",             GiftTaxAgent),
        "InheritanceTaxAgent":      _agent("InheritanceTaxAgent",      InheritanceTaxAgent),
        "VATAgent":                 _agent("VATAgent",                 VATAgent),
        "RDTaxCreditAgent":         _agent("RDTaxCreditAgent",         RDTaxCreditAgent),
        "InvestTaxCreditAgent":     _agent("InvestTaxCreditAgent",     InvestTaxCreditAgent),
        # GROUP G — 재무·HR 특화 (재무예측·원가·4대보험·성과급·배당·특수관계)
        "FinancialForecastAgent":   _agent("FinancialForecastAgent",   FinancialForecastAgent),
        "CostAnalysisAgent":        _agent("CostAnalysisAgent",        CostAnalysisAgent),
        "SocialInsuranceAgent":     _agent("SocialInsuranceAgent",     SocialInsuranceAgent),
        "PerformancePayAgent":      _agent("PerformancePayAgent",      PerformancePayAgent),
        "DividendPolicyAgent":      _agent("DividendPolicyAgent",      DividendPolicyAgent),
        "RelatedPartyAgent":        _agent("RelatedPartyAgent",        RelatedPartyAgent),
        # GROUP H — 전략·성장 특화 (해외진출·DX·하도급·IPO·프랜차이즈·부채)
        "GlobalExpansionAgent":   _agent("GlobalExpansionAgent",   GlobalExpansionAgent),
        "DXAgent":                _agent("DXAgent",                DXAgent),
        "SubcontractAgent":       _agent("SubcontractAgent",       SubcontractAgent),
        "IPOAgent":               _agent("IPOAgent",               IPOAgent),
        "FranchiseAgent":         _agent("FranchiseAgent",         FranchiseAgent),
        "DebtRestructuringAgent": _agent("DebtRestructuringAgent", DebtRestructuringAgent),
        # GROUP I — 컴플라이언스·지원 전담 에이전트
        "ComplianceAgent":       _agent("ComplianceAgent",       ComplianceAgent),
        "ContractReviewAgent":   _agent("ContractReviewAgent",   ContractReviewAgent),
        "WorkingCapitalAgent":   _agent("WorkingCapitalAgent",   WorkingCapitalAgent),
        "PrivacyAgent":          _agent("PrivacyAgent",          PrivacyAgent),
        "HRDAgent":              _agent("HRDAgent",              HRDAgent),
        "SupplyChainAgent":      _agent("SupplyChainAgent",      SupplyChainAgent),
        "TradeAgent":            _agent("TradeAgent",            TradeAgent),
        "VentureCapitalAgent":   _agent("VentureCapitalAgent",   VentureCapitalAgent),
        # 인프라·검증 에이전트
        "DataValidationAgent":   _agent("DataValidationAgent",   DataValidationAgent),
        "QueryClassifierAgent":  _agent("QueryClassifierAgent",  QueryClassifierAgent),
        "RiskScoreAgent":        _agent("RiskScoreAgent",        RiskScoreAgent),
        "SummaryAgent":          _agent("SummaryAgent",          SummaryAgent),
        "VerifyFinance":         _agent("VerifyFinance",         VerifyFinance),
        "VerifyCompliance":      _agent("VerifyCompliance",      VerifyCompliance),
        # GROUP D — Delta 모니터링 + 시나리오 시뮬레이션
        "MonitorAgent":       _agent("MonitorAgent",       MonitorAgent),
        "ScenarioAgent":      _agent("ScenarioAgent",      ScenarioAgent),
    }


# ──────────────────────────────────────────────────────────────────────────
# 검증 그룹 매핑
# ──────────────────────────────────────────────────────────────────────────

VERIFY_GROUPS = {
    # GROUP A+E+F+G(세무): 세무·절세·전담 에이전트 — 세법 정합성·계산값 교차검증
    "VerifyTax":      ["TaxAgent", "FinanceAgent", "StockAgent", "SuccessionAgent",
                       "ProvisionalPaymentAgent", "NomineeStockAgent", "ExecutivePayAgent",
                       "GiftTaxAgent", "InheritanceTaxAgent", "VATAgent",
                       "RDTaxCreditAgent", "InvestTaxCreditAgent",
                       "DividendPolicyAgent", "RelatedPartyAgent"],
    # GROUP B+G(HR): 법무·노무·특허·부동산·보험·HR — 법령 준수 및 리스크 검증
    "VerifyOps":      ["LegalAgent", "LaborAgent", "PatentAgent", "RealEstateAgent", "InsuranceAgent",
                       "SocialInsuranceAgent", "PerformancePayAgent", "SubcontractAgent", "FranchiseAgent",
                       "ComplianceAgent", "ContractReviewAgent", "PrivacyAgent", "HRDAgent", "SupplyChainAgent"],
    # GROUP C+D+BP+G(재무): 정책·현금흐름·신용·M&A·ESG·업종·웹조사·사업계획·재무예측·원가 — 전략 실현가능성 검증
    "VerifyStrategy": ["PolicyFundingAgent", "CashFlowAgent", "CreditRatingAgent",
                       "MAValuationAgent", "ESGRiskAgent", "IndustryAgent", "WebResearchAgent",
                       "BusinessPlanAgent", "FinancialForecastAgent", "CostAnalysisAgent",
                       "GlobalExpansionAgent", "DXAgent", "IPOAgent", "DebtRestructuringAgent",
                       "TradeAgent", "VentureCapitalAgent", "WorkingCapitalAgent",
                       "VerifyFinance", "VerifyCompliance", "RiskScoreAgent", "SummaryAgent"],
}

# GROUP_D — Delta 모니터링 + 시나리오 시뮬레이션 (Phase 1 마지막 배치)
GROUP_D = ["MonitorAgent", "ScenarioAgent"]


# ──────────────────────────────────────────────────────────────────────────
# ReportAgent
# ──────────────────────────────────────────────────────────────────────────

class ReportAgent(BaseAgent):
    name = "ReportAgent"
    role = "최종 통합 보고서 작성 전문가"
    system_prompt = (
        "당신은 중소기업 경영컨설팅 통합 보고서 작성 전문가입니다.\n"
        "53개 전문 에이전트의 분석 결과와 3개 검증 결과를 종합하여 "
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
        # 요약 입력 구성 (토큰 절약) — extract_context() 로 핵심만 전달
        summaries = []
        for name, result in agent_results.items():
            ctx = extract_context(result)
            summaries.append(
                f"[{name}]\n"
                f"summary: {ctx['summary']}\n"
                f"key_metrics: {'; '.join(ctx['key_metrics'])}\n"
                f"flags: {'; '.join(ctx['flags'])}"
            )

        verify_summary = "\n".join(
            f"[{k}] {v.status} {v.score}/100" for k, v in verify_results.items()
        )

        prompt = (
            f"분석 대상 기업: {company_name}\n\n"
            f"=== 에이전트 분석 요약 ===\n"
            + "\n\n".join(summaries[:8])  # 토큰 절약을 위해 8개만
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
    ppt_path: str = ""
    total_time: float = 0.0

    def print_summary(self) -> None:
        sep = "=" * 72
        thin = "-" * 72
        print(f"\n{sep}")
        print(f"  종합 컨설팅 결과 — {self.company_name}")
        print(f"  실행 시간: {self.total_time:.1f}초  |  에이전트: {len(self.agent_results)}개 완료")
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
        print(sep)


class Orchestrator:
    """22개 에이전트(GROUP A~E) + 3개 검증 + 1개 리포트 통합 실행기."""

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
        print(f"  중소기업 컨설팅 에이전트 시스템 v4")
        print(f"  대상: {company_name}  |  에이전트: 39개(GROUP A~H) + 검증 3개")
        print(f"{'='*72}\n")

        # ── Phase 1: 22개 에이전트 배치 병렬 실행 (MAX_WORKERS=2, 그룹 간 sleep) ──
        print("[Phase 1] 39개 전문 에이전트 배치 실행 중 (그룹당 4개, sleep 10초)...")
        agents = _build_agent_map(self.verbose)
        queries = build_queries(company_data)

        agent_results: dict[str, str] = {}
        agent_errors: dict[str, str] = {}

        # 에이전트를 4개씩 4그룹으로 분할
        agent_items = [(name, agent) for name, agent in agents.items() if name in queries]
        group_size = 4
        groups = [agent_items[i:i+group_size] for i in range(0, len(agent_items), group_size)]
        done_count = 0
        total_agents = len(agent_items)

        for g_idx, group in enumerate(groups):
            if g_idx > 0:
                print(f"  [sleep 10초] 그룹 {g_idx}/{len(groups)} 대기 중...")
                time.sleep(10)
            print(f"  --- 그룹 {g_idx+1}/{len(groups)} 실행 ({len(group)}개 에이전트) ---")
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
                futures = {
                    ex.submit(self._run_agent_safe, agent, queries[name], company_data): name
                    for name, agent in group
                }
                for future in as_completed(futures):
                    name = futures[future]
                    result, err = future.result()
                    done_count += 1
                    if err:
                        agent_errors[name] = err
                        print(f"  [{done_count:02d}/{total_agents}] {name} — 오류: {err[:60]}")
                    else:
                        agent_results[name] = result
                        print(f"  [{done_count:02d}/{total_agents}] {name} — 완료 ({len(result)}자)")

        phase1_time = time.time() - start
        print(f"\n[Phase 1 완료] {len(agent_results)}개 성공 / {len(agent_errors)}개 실패 ({phase1_time:.1f}초)\n")

        # ── Phase 2: 검증 에이전트 3개 병렬 실행 ───────────────────────
        print("[Phase 2] 검증 에이전트 3개 병렬 실행 중...")
        verify_model = MODEL_MAP.get("VerifyAgent", MODEL)
        verifiers = {
            "VerifyTax":      VerifyTax(verbose=self.verbose),
            "VerifyOps":      VerifyOps(verbose=self.verbose),
            "VerifyStrategy": VerifyStrategy(verbose=self.verbose),
        }
        for v in verifiers.values():
            v.model = verify_model

        def run_verify(vname: str, verifier) -> tuple[str, VerifyResult]:
            group = VERIFY_GROUPS[vname]
            combined_q = f"기업: {company_name}\n업종: {company_data.get('industry', '')}"
            combined_r = "\n\n".join(
                "[{n}]\n{ctx}".format(
                    n=n,
                    ctx="\n".join([
                        f"summary: {ctx['summary']}",
                        f"key_metrics: {'; '.join(ctx['key_metrics'])}",
                        f"flags: {'; '.join(ctx['flags'])}",
                    ])
                )
                for n in group
                if n in agent_results
                for ctx in [extract_context(agent_results[n])]
            )
            try:
                vr = verifier.verify(combined_q, combined_r)
            except Exception as e:
                vr = VerifyResult(60, "WARNING", [str(e)], "오류 발생", "", vname)
            return vname, vr

        verify_results: dict[str, VerifyResult] = {}
        with ThreadPoolExecutor(max_workers=3) as ex:
            futs = {ex.submit(run_verify, vn, v): vn for vn, v in verifiers.items()}
            for f in as_completed(futs):
                vname, vr = f.result()
                verify_results[vname] = vr
                icon = {"PASS": "[OK]", "WARNING": "[!!]", "FAIL": "[NG]"}.get(vr.status, "[?]")
                print(f"  {vname}: {icon} {vr.status} {vr.score}/100")

        phase2_time = time.time() - start - phase1_time
        print(f"\n[Phase 2 완료] ({phase2_time:.1f}초)\n")

        # ── Phase 3: ReportAgent 최종 통합 ──────────────────────────────
        print("[Phase 3] ReportAgent 통합 보고서 작성 중...")
        try:
            reporter = ReportAgent(verbose=self.verbose)
            reporter.model = MODEL_MAP.get("Orchestrator", MODEL)
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
            ppt_path=ppt_path,
            total_time=total_time,
        )
