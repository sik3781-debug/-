"""
VerifyTax: TaxAgent·FinanceAgent·StockAgent·SuccessionAgent 검증 에이전트
"""
from __future__ import annotations
import re
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 세무·회계·주식평가 분야 검증 전문가입니다.\n"
    "다음 에이전트 답변을 엄격히 검증하십시오: TaxAgent, FinanceAgent, StockAgent, SuccessionAgent\n\n"
    "【검증 항목】\n"
    "1. 법인세·소득세·상속증여세 법령 조문 정확성\n"
    "2. 세율·공제 한도 수치 최신 반영 여부\n"
    "3. 비상장주식 보충적 평가 산식 정확성 (상증법 시행령 제54조)\n"
    "4. 가업상속공제 요건·한도 정확성 (상증법 제18조의2)\n"
    "5. 재무비율 계산식 및 수치 오류\n"
    "6. 리스크 누락 여부\n\n"
    "【출력 형식 — 반드시 준수】\n"
    "SCORE: (0~100 정수)\n"
    "STATUS: (PASS / WARNING / FAIL)\n"
    "ISSUES:\n"
    "- (이슈 목록, 없으면 '이슈 없음')\n"
    "RECOMMENDATION:\n"
    "(보완 권고사항)"
)


class VerifyTax(BaseAgent):
    name = "VerifyTax"
    role = "세무·주식평가·재무 검증 전문가"
    system_prompt = _SYS

    def verify(self, query: str, response: str) -> "VerifyResult":
        prompt = (
            f"【검증 대상 에이전트】TaxAgent / FinanceAgent / StockAgent / SuccessionAgent\n\n"
            f"【원본 질의】\n{query}\n\n"
            f"【검증 대상 답변】\n{response[:3000]}\n\n"
            "위 답변을 세무·회계·주식평가 기준으로 검증하십시오."
        )
        raw = self.run(prompt, reset=True)
        return VerifyResult.parse(raw, self.name)


class VerifyOps(BaseAgent):
    name = "VerifyOps"
    role = "법률·노무·특허·부동산·보험 검증 전문가"
    system_prompt = (
        "당신은 상법·노동법·지식재산법·부동산법·보험법 검증 전문가입니다.\n"
        "다음 에이전트 답변을 검증하십시오: LegalAgent, LaborAgent, PatentAgent, RealEstateAgent, InsuranceAgent\n\n"
        "【검증 항목】\n"
        "1. 상법 절차·요건 정확성\n"
        "2. 노동법·근로기준법 조문 정확성\n"
        "3. R&D 세액공제 요건·한도\n"
        "4. 부동산 취득·양도세 계산 정확성\n"
        "5. 보험료 손금산입 요건\n"
        "6. 최신 판례·예규 반영 여부\n\n"
        "【출력 형식 — 반드시 준수】\n"
        "SCORE: (0~100 정수)\n"
        "STATUS: (PASS / WARNING / FAIL)\n"
        "ISSUES:\n"
        "- (이슈 목록, 없으면 '이슈 없음')\n"
        "RECOMMENDATION:\n"
        "(보완 권고사항)"
    )

    def verify(self, query: str, response: str) -> "VerifyResult":
        prompt = (
            f"【검증 대상 에이전트】LegalAgent / LaborAgent / PatentAgent / RealEstateAgent / InsuranceAgent\n\n"
            f"【원본 질의】\n{query}\n\n"
            f"【검증 대상 답변】\n{response[:3000]}\n\n"
            "위 답변을 법률·노무·특허·부동산·보험 기준으로 검증하십시오."
        )
        raw = self.run(prompt, reset=True)
        return VerifyResult.parse(raw, self.name)


class VerifyStrategy(BaseAgent):
    name = "VerifyStrategy"
    role = "경영전략·정책자금·ESG·M&A 검증 전문가"
    system_prompt = (
        "당신은 경영전략·정책자금·M&A·ESG·신용등급·현금흐름 검증 전문가입니다.\n"
        "다음 에이전트 답변을 검증하십시오: PolicyFundingAgent, CashFlowAgent, CreditRatingAgent, "
        "MAValuationAgent, ESGRiskAgent, IndustryAgent, WebResearchAgent\n\n"
        "【검증 항목】\n"
        "1. 정책자금 요건·금리·한도 정확성\n"
        "2. 현금흐름 계산식 및 수치 정확성\n"
        "3. 신용등급 모형 합리성\n"
        "4. DCF·PER·EV/EBITDA 계산 정확성\n"
        "5. ESG 법규·글로벌 기준 반영 여부\n"
        "6. 정보 출처의 신뢰성\n\n"
        "【출력 형식 — 반드시 준수】\n"
        "SCORE: (0~100 정수)\n"
        "STATUS: (PASS / WARNING / FAIL)\n"
        "ISSUES:\n"
        "- (이슈 목록, 없으면 '이슈 없음')\n"
        "RECOMMENDATION:\n"
        "(보완 권고사항)"
    )

    def verify(self, query: str, response: str) -> "VerifyResult":
        prompt = (
            f"【검증 대상 에이전트】PolicyFunding / CashFlow / CreditRating / MAValuation / ESG / Industry / WebResearch\n\n"
            f"【원본 질의】\n{query}\n\n"
            f"【검증 대상 답변】\n{response[:3000]}\n\n"
            "위 답변을 경영전략·정책자금·M&A·ESG·신용등급 기준으로 검증하십시오."
        )
        raw = self.run(prompt, reset=True)
        return VerifyResult.parse(raw, self.name)


# ──────────────────────────────────────────────────────────────────────────
# 공용 결과 클래스
# ──────────────────────────────────────────────────────────────────────────
class VerifyResult:
    def __init__(self, score: int, status: str, issues: list[str],
                 recommendation: str, raw: str, verifier: str) -> None:
        self.score = score
        self.status = status
        self.issues = issues
        self.recommendation = recommendation
        self.raw = raw
        self.verifier = verifier

    @classmethod
    def parse(cls, text: str, verifier: str = "Verifier") -> "VerifyResult":
        score = 70
        status = "WARNING"
        issues: list[str] = []
        recommendation = ""

        m = re.search(r"SCORE:\s*(\d+)", text)
        if m:
            score = int(m.group(1))
        m = re.search(r"STATUS:\s*(PASS|WARNING|FAIL)", text)
        if m:
            status = m.group(1)
        m = re.search(r"ISSUES:\s*\n(.*?)(?=RECOMMENDATION:|$)", text, re.DOTALL)
        if m:
            issues = [
                ln.lstrip("- ").strip()
                for ln in m.group(1).splitlines()
                if ln.strip() and ln.strip() != "이슈 없음"
            ]
        m = re.search(r"RECOMMENDATION:\s*\n?(.*)", text, re.DOTALL)
        if m:
            recommendation = m.group(1).strip()

        return cls(score, status, issues, recommendation, text, verifier)

    def summary(self) -> str:
        icon = {"PASS": "[OK]", "WARNING": "[!!]", "FAIL": "[NG]"}.get(self.status, "[?]")
        lines = [f"[{self.verifier}] {icon} {self.status} | 신뢰도: {self.score}/100"]
        if self.issues:
            lines.append("이슈:")
            for iss in self.issues[:3]:  # 상위 3개만 출력
                lines.append(f"  - {iss[:100]}")
            if len(self.issues) > 3:
                lines.append(f"  ... 외 {len(self.issues)-3}건")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"VerifyResult(verifier={self.verifier}, score={self.score}, status={self.status})"
