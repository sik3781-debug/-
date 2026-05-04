"""
DEPRECATED — agents/business_plan_agent.py
==========================================
v1.1.0 분기(2026-11-04)에서 본 파일 자동 삭제 예정.

정식 활성 에이전트는:
    agents.active.business_plan_agent.BusinessPlanAgent

본 파일은 후방 호환을 위해 유지되며, BusinessPlanAgent 호출은 정식 통합본으로
자동 라우팅됩니다. 구 LLM 기반 사업계획서 본문 생성 능력은 정식 통합본의
후속 narrative 메서드 (후속 세션 보강 예정)로 흡수됩니다.

복원이 필요한 경우 백업 브랜치 backup-quad-merge-* 에서 복원 가능.

작성: 2026-05-04 [LAPTOP] (PART7 통합)
"""
from __future__ import annotations

import warnings

from agents.active.business_plan_agent import BusinessPlanAgent  # 정식 통합본 re-export

warnings.warn(
    "agents.business_plan_agent.BusinessPlanAgent는 deprecated. "
    "agents.active.business_plan_agent.BusinessPlanAgent를 사용하세요. "
    "v1.1.0 (2026-11-04)에서 자동 삭제 예정.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["BusinessPlanAgent"]
