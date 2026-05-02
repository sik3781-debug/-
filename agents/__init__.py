"""에이전트 패키지 전체 에이전트 임포트"""

from agents.base_agent import BaseAgent, MODEL, MODEL_LIGHT

# 기존 컨설팅 에이전트
from agents.consulting_agents import TaxAgent, StockAgent, SuccessionAgent, FinanceAgent

# 신규 전문 에이전트
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

# GROUP E 전담 에이전트 (가지급금·차명주식·임원보수)
from agents.provisional_payment_agent import ProvisionalPaymentAgent
from agents.nominee_stock_agent import NomineeStockAgent
from agents.executive_pay_agent import ExecutivePayAgent

# 2단계 세금·절세 전담 에이전트
from agents.gift_tax_agent import GiftTaxAgent
from agents.inheritance_tax_agent import InheritanceTaxAgent
from agents.vat_agent import VATAgent
from agents.rd_tax_credit_agent import RDTaxCreditAgent
from agents.invest_tax_credit_agent import InvestTaxCreditAgent

# 4단계 전략·성장 특화 에이전트
from agents.global_expansion_agent import GlobalExpansionAgent
from agents.dx_agent import DXAgent
from agents.subcontract_agent import SubcontractAgent
from agents.ipo_agent import IPOAgent
from agents.franchise_agent import FranchiseAgent
from agents.debt_restructuring_agent import DebtRestructuringAgent

# 3단계 재무·HR 특화 에이전트
from agents.financial_forecast_agent import FinancialForecastAgent
from agents.cost_analysis_agent import CostAnalysisAgent
from agents.social_insurance_agent import SocialInsuranceAgent
from agents.performance_pay_agent import PerformancePayAgent
from agents.dividend_policy_agent import DividendPolicyAgent
from agents.related_party_agent import RelatedPartyAgent

# GROUP D Delta 모니터링 시나리오 시뮬레이션
from agents.all_agents import MonitorAgent, ScenarioAgent

# 검증 에이전트
from agents.verify_tax import VerifyTax, VerifyOps, VerifyStrategy, VerifyResult

# 5단계 컴플라이언스·지원 전담 에이전트 (GROUP I)
from agents.compliance_agent import ComplianceAgent
from agents.contract_review_agent import ContractReviewAgent
from agents.working_capital_agent import WorkingCapitalAgent
from agents.privacy_agent import PrivacyAgent
from agents.hrd_agent import HRDAgent
from agents.supply_chain_agent import SupplyChainAgent
from agents.trade_agent import TradeAgent
from agents.venture_capital_agent import VentureCapitalAgent

# 6단계 인프라·검증 에이전트 (최종)
from agents.verify_finance import VerifyFinance
from agents.verify_compliance import VerifyCompliance
from agents.data_validation_agent import DataValidationAgent
from agents.query_classifier_agent import QueryClassifierAgent
from agents.risk_score_agent import RiskScoreAgent
from agents.summary_agent import SummaryAgent

# 하위 호환 (기존 verify_agent.py 사용 코드를 위해)
from agents.verify_agent import VerifyAgent

__all__ = [
    "BaseAgent", "MODEL", "MODEL_LIGHT",
    "TaxAgent", "StockAgent", "SuccessionAgent", "FinanceAgent",
    "LegalAgent", "PatentAgent", "LaborAgent", "IndustryAgent",
    "WebResearchAgent", "PolicyFundingAgent", "CashFlowAgent",
    "CreditRatingAgent", "RealEstateAgent", "InsuranceAgent",
    "MAValuationAgent", "ESGRiskAgent", "BusinessPlanAgent",
    "ProvisionalPaymentAgent", "NomineeStockAgent", "ExecutivePayAgent",
    "GiftTaxAgent", "InheritanceTaxAgent", "VATAgent",
    "RDTaxCreditAgent", "InvestTaxCreditAgent",
    "GlobalExpansionAgent", "DXAgent", "SubcontractAgent",
    "IPOAgent", "FranchiseAgent", "DebtRestructuringAgent",
    "FinancialForecastAgent", "CostAnalysisAgent", "SocialInsuranceAgent",
    "PerformancePayAgent", "DividendPolicyAgent", "RelatedPartyAgent",
    "MonitorAgent", "ScenarioAgent",
    "VerifyTax", "VerifyOps", "VerifyStrategy", "VerifyResult",
    "VerifyAgent",
    "ComplianceAgent", "ContractReviewAgent", "WorkingCapitalAgent",
    "PrivacyAgent", "HRDAgent", "SupplyChainAgent",
    "TradeAgent", "VentureCapitalAgent",
    "VerifyFinance", "VerifyCompliance",
    "DataValidationAgent", "QueryClassifierAgent",
    "RiskScoreAgent", "SummaryAgent",
]
