"""에이전트 패키지 — 전체 에이전트 임포트"""

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

# 검증 에이전트
from agents.verify_tax import VerifyTax, VerifyOps, VerifyStrategy, VerifyResult

# 하위 호환 (기존 verify_agent.py 사용 코드를 위해)
from agents.verify_agent import VerifyAgent

__all__ = [
    # base
    "BaseAgent", "MODEL", "MODEL_LIGHT",
    # core
    "TaxAgent", "StockAgent", "SuccessionAgent", "FinanceAgent",
    # extended
    "LegalAgent", "PatentAgent", "LaborAgent", "IndustryAgent",
    "WebResearchAgent", "PolicyFundingAgent", "CashFlowAgent",
    "CreditRatingAgent", "RealEstateAgent", "InsuranceAgent",
    "MAValuationAgent", "ESGRiskAgent",
    # verifiers
    "VerifyTax", "VerifyOps", "VerifyStrategy", "VerifyResult",
    "VerifyAgent",
]
