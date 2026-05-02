"""
workflows/solution_pipeline.py
================================
4단계 컨설팅 솔루션 파이프라인

1단계: 문제 진단 (현황 파악)
2단계: 옵션 분석 (3가지 시나리오 비교)
3단계: 추천 (최적 방안 + 근거)
4단계: 실행 계획 (월별 로드맵 + 필요 증빙)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ──────────────────────────────────────────────────────────────
# 데이터 클래스
# ──────────────────────────────────────────────────────────────
@dataclass
class Stage1Diagnosis:
    """1단계: 문제 진단"""
    agent: str
    issues: list[str]
    risk_level: str   # HIGH / MEDIUM / LOW
    quantified: dict  # {"절세가능액": 0, "리스크금액": 0, ...}


@dataclass
class Stage2Options:
    """2단계: 옵션 분석 (최소 3개)"""
    scenarios: list[dict]  # [{"name": str, "tax_burden": int, "risk": str, ...}]

    def best_scenario(self) -> dict:
        return min(self.scenarios, key=lambda s: s.get("tax_burden", 999_999_999))


@dataclass
class Stage3Recommendation:
    """3단계: 추천"""
    recommended_scenario: dict
    rationale: str
    legal_basis: list[str]      # 근거 조문
    expected_saving: int         # 절세액 (원)
    risk_after: str              # HIGH/MEDIUM/LOW (개선 후)


@dataclass
class Stage4ActionPlan:
    """4단계: 실행 계획"""
    steps: list[dict]   # [{"month": 1, "action": str, "documents": list}]
    total_months: int
    checkpoints: list[str]  # 이정표


@dataclass
class SolutionPipelineResult:
    """전체 파이프라인 결과"""
    stage1: Stage1Diagnosis
    stage2: Stage2Options
    stage3: Stage3Recommendation
    stage4: Stage4ActionPlan
    agent: str
    perspective_4: dict   # {"법인": str, "주주": str, "과세관청": str, "금융기관": str}

    def to_dict(self) -> dict:
        return {
            "stage1_diagnosis":     vars(self.stage1),
            "stage2_options":       vars(self.stage2),
            "stage3_recommendation": vars(self.stage3),
            "stage4_action_plan":   vars(self.stage4),
            "agent":                self.agent,
            "perspective_4":        self.perspective_4,
        }

    def summary(self) -> str:
        s = self.stage3
        return (
            f"[{self.agent}] 추천: {s.recommended_scenario.get('name','—')}\n"
            f"  예상 절세: {s.expected_saving:,}원 / 근거: {'; '.join(s.legal_basis)}\n"
            f"  실행: {self.stage4.total_months}개월 / "
            f"4자관점: {' | '.join(f'{k}={v[:20]}' for k,v in self.perspective_4.items())}"
        )


# ──────────────────────────────────────────────────────────────
# 파이프라인 실행기
# ──────────────────────────────────────────────────────────────
class SolutionPipeline:
    """
    사용 예:
        pipeline = SolutionPipeline(agent_output_text, agent_name, company_data)
        result = pipeline.run()
        print(result.summary())
    """

    def __init__(self, agent_output: str, agent_name: str,
                 company_data: dict | None = None):
        self.output       = agent_output
        self.agent_name   = agent_name
        self.company_data = company_data or {}

    def run(self) -> SolutionPipelineResult:
        s1 = self._stage1_diagnose()
        s2 = self._stage2_options(s1)
        s3 = self._stage3_recommend(s2)
        s4 = self._stage4_action(s3)
        p4 = self._perspective_4(s1, s3)
        return SolutionPipelineResult(s1, s2, s3, s4, self.agent_name, p4)

    # ── 각 단계 ─────────────────────────────────────────────

    def _stage1_diagnose(self) -> Stage1Diagnosis:
        import re
        issues: list[str] = []
        quantified: dict  = {}

        # 이슈 키워드 추출
        for kw in ["위험", "문제", "미비", "부족", "초과", "리스크"]:
            for m in re.finditer(rf'.{{0,30}}{kw}.{{0,30}}', self.output):
                snippet = m.group().strip()
                if snippet not in issues:
                    issues.append(snippet)

        # 금액 추출
        for m in re.finditer(r'(\d[\d,]*)\s*(억원|원|만원)', self.output):
            quantified[f"금액_{len(quantified)+1}"] = int(m.group(1).replace(',',''))

        # 리스크 수준 추정
        high_kw = ["세무조사", "형사", "가산세", "추징", "제척"]
        risk = "HIGH" if any(k in self.output for k in high_kw) else "MEDIUM"

        return Stage1Diagnosis(
            agent=self.agent_name,
            issues=issues[:5],
            risk_level=risk,
            quantified=quantified,
        )

    def _stage2_options(self, s1: Stage1Diagnosis) -> Stage2Options:
        # 에이전트별 기본 시나리오 3종 생성
        base_scenarios = [
            {"name": "보수적", "description": "최소 변경 → 안전 우선", "risk": "LOW",  "tax_burden": 999},
            {"name": "중도",   "description": "균형 최적화",           "risk": "MED",  "tax_burden": 700},
            {"name": "적극적", "description": "절세 극대화",           "risk": "HIGH", "tax_burden": 400},
        ]
        # 출력 텍스트에서 숫자 있으면 세부담 수치 추출
        import re
        amounts = [int(m.group(1).replace(',',''))
                   for m in re.finditer(r'(\d[\d,]+)\s*(억원|만원|원)', self.output)]
        if len(amounts) >= 3:
            for i, s in enumerate(base_scenarios):
                s["tax_burden"] = amounts[i] if i < len(amounts) else s["tax_burden"]

        return Stage2Options(scenarios=base_scenarios)

    def _stage3_recommend(self, s2: Stage2Options) -> Stage3Recommendation:
        best = s2.best_scenario()
        # 출력에서 법조문 추출
        import re
        articles = re.findall(r'(?:법|상증|소|조특|시령)\s*§\s*\d+', self.output)
        if not articles:
            articles = ["[보정필요: 법령 근거 명시]"]

        return Stage3Recommendation(
            recommended_scenario=best,
            rationale=f"{best['name']} 시나리오: 세부담 최소화 + 적법성 확보",
            legal_basis=articles[:3],
            expected_saving=abs(999 - best.get("tax_burden", 700)) * 1_000_000,
            risk_after="LOW" if best["name"] == "보수적" else "MED",
        )

    def _stage4_action(self, s3: Stage3Recommendation) -> Stage4ActionPlan:
        return Stage4ActionPlan(
            steps=[
                {"month": 1, "action": "현황 진단 + 전문가 협의",      "documents": ["재무제표", "세무신고서"]},
                {"month": 2, "action": "전략 선택 + 법무 검토",         "documents": ["이사회 의사록"]},
                {"month": 3, "action": "실행 착수",                     "documents": ["계약서", "증빙자료"]},
                {"month": 6, "action": "중간 점검 + 진도 확인",         "documents": ["중간 보고서"]},
                {"month": 12, "action": "결과 검증 + 세무신고 반영",    "documents": ["최종 보고서"]},
            ],
            total_months=12,
            checkpoints=["3개월: 착수 확인", "6개월: 중간 점검", "12개월: 완료"],
        )

    def _perspective_4(self, s1: Stage1Diagnosis, s3: Stage3Recommendation) -> dict:
        return {
            "법인":    f"세무리스크 {s1.risk_level} → 절세 {s3.expected_saving//100000000}억원",
            "주주":    "가처분소득 극대화 방안 포함",
            "과세관청": f"근거법령: {'; '.join(s3.legal_basis[:2])}",
            "금융기관": "재무구조 영향 모니터링 필요",
        }
