"""전문 솔루션 그룹 표준 베이스 — 4단계 워크플로우 강제
Anthropic SDK에 의존하지 않는 순수 Python ABC.
기존 active/ 에이전트와 호환 가능.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class ProfessionalSolutionAgent(ABC):
    """
    전문영역 에이전트 표준 베이스.
    4단계 업무 프로세스: 전략생성→리스크점검&헷지→과정관리→사후관리.
    """

    classification: str = "전문영역"
    group: str = "전문 솔루션 그룹"
    workflow: str = "4단계: 전략생성→리스크점검&헷지→과정관리→사후관리"
    lawyer_disclaimer: str = (
        "본 자료는 검토용 초안이며, 최종 등기·공증·소송 대응은 변호사·법무사 검토 필수"
    )

    @abstractmethod
    def generate_strategy(self, case: dict) -> dict:
        """① 전략생성 — 도메인 분석 + 솔루션 도출"""

    @abstractmethod
    def validate_risk_5axis(self, strategy: dict) -> dict:
        """② 리스크점검 — DOMAIN·LEGAL·CALC·LOGIC·CROSS 5축"""

    @abstractmethod
    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        """② 리스크 헷지방안 — 1_pre·2_now·3_post·4_worst"""

    @abstractmethod
    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        """③ 과정관리 — 거래·계약·신고·증빙 절차"""

    @abstractmethod
    def post_management(self, strategy: dict, process: dict) -> dict:
        """④ 사후관리 — 사후관리 일정·정기점검·재검토 트리거"""

    def _build_4party_3time_matrix(self, strategy: dict, risks: dict,
                                   hedges: dict, process: dict, post: dict) -> dict:
        """4자관점(법인·주주·과세관청·금융기관) × 3시점(Pre·Now·Post) = 12셀 기본 구조"""
        return {
            "법인":       {"사전": "", "현재": "", "사후": ""},
            "주주(오너)": {"사전": "", "현재": "", "사후": ""},
            "과세관청":   {"사전": "", "현재": "", "사후": ""},
            "금융기관":   {"사전": "", "현재": "", "사후": ""},
        }

    def _generate_checklist(self, strategy: dict, risks: dict) -> list[str]:
        """실행 체크리스트 기본 구조 (서브클래스에서 오버라이드 권장)"""
        items = ["이행 검토 완료", "법령 근거 확인", "4자관점 검토"]
        if not risks.get("all_pass"):
            items.append("⚠️ 5축 검증 미통과 항목 재확인 필요")
        return items

    def analyze(self, case: dict) -> dict:
        """4단계 통합 실행 — 전문 솔루션 그룹 표준 진입점"""
        strategy = self.generate_strategy(case)
        risks    = self.validate_risk_5axis(strategy)
        hedges   = self.generate_risk_hedge_4stage(strategy)
        process  = self.manage_execution(strategy, hedges)
        post     = self.post_management(strategy, process)
        matrix   = self._build_4party_3time_matrix(strategy, risks, hedges, process, post)
        return {
            "classification":  self.classification,
            "group":           self.group,
            "workflow":        self.workflow,
            "domain":          self.__class__.__name__,
            "strategy":        strategy,
            "risks":           risks,
            "hedges":          hedges,
            "process":         process,
            "post":            post,
            "matrix_12cells":  matrix,
            "checklist":       self._generate_checklist(strategy, risks),
            "lawyer_disclaimer": self.lawyer_disclaimer,
        }
