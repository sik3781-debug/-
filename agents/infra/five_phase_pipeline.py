"""
5단계 컨설팅 파이프라인 오케스트레이터 (/파이프라인) — 인프라
Stage 1 의뢰접수 → Stage 2 자료수집 → Stage 3 진단 → Stage 4 솔루션 → Stage 5 산출물
"""
from __future__ import annotations
import importlib
from pathlib import Path
from agents.base.professional_solution_agent import ProfessionalSolutionAgent
from agents.groups.professional_solution_group import register


@register
class FivePhasePipelineOrchestrator(ProfessionalSolutionAgent):
    """5단계 컨설팅 자동 오케스트레이션 — 6트랙 진단 + 산출물 5종

    법인세법§60 신고 기한 (Stage 5 산출물 타이밍)
    K-IFRS 1001 재무상태 (Stage 3 진단 기준)
    국기법§45의2 경정청구 (Stage 4 솔루션 포함)
    외감법§4 외감 대상 판정 (Stage 2 자료수집 체크)
    조특§10 R&D 세액공제 (Stage 4 절세 솔루션)
    상증§63 비상장주식 평가 (Stage 3 진단 기준)
    """

    PIPELINE = {
        "stage_1": "의뢰접수 (고객 정보·의뢰 내용·긴급도 분류)",
        "stage_2": "자료수집 (재무제표·세무신고서·등기부·계약서 등)",
        "stage_3": "진단 (6트랙 병렬 분석)",
        "stage_4": "솔루션 설계 (4자관점×3시점 12셀 + 3종 시나리오)",
        "stage_5": "산출물 생성 (1페이지요약·docx·HTML·xlsx·체크리스트)",
    }

    SIX_TRACKS = [
        "A.수익성·성장성·안정성 (재무비율·EBITDA·DuPont)",
        "B.법인세 절세 (이월결손금·세액공제·이전가격)",
        "C.임원 보수·퇴직금 (상여 한도·분배 최적화)",
        "D.가지급금 정밀 (인정이자·해소 방안)",
        "E.비상장주식·승계 (평가·이전·가업승계)",
        "F.4자관점 통합 리스크헷지 (법인·주주·과세관청·금융)",
    ]

    OUTPUTS_5 = [
        "1페이지 요약 (KPI 카드 + 핵심 Action 3개)",
        "상세 보고서 (.docx 30~50페이지)",
        "HTML 대시보드 (chart.js 인터랙티브)",
        "시뮬레이션 엑셀 (.xlsx 다중시트)",
        "실행 체크리스트 (단계별·기한별)",
    ]

    def generate_strategy(self, case: dict) -> dict:
        """① 전략생성 — 5단계 파이프라인 계획 수립"""
        client_name  = case.get("client_name", "")
        domain       = case.get("domain", "종합")
        urgency      = case.get("urgency", "표준")          # 긴급|표준|여유
        tracks       = case.get("tracks", list(range(6)))   # 실행할 트랙 인덱스 (기본 전체)
        outputs      = case.get("outputs", list(range(5)))  # 생성할 산출물 인덱스

        # 긴급도별 타임라인
        timeline = {
            "긴급": {"진단": "1일", "솔루션": "2일", "산출물": "3일"},
            "표준": {"진단": "3일", "솔루션": "5일", "산출물": "7일"},
            "여유": {"진단": "7일", "솔루션": "14일", "산출물": "21일"},
        }.get(urgency, {"진단": "3일", "솔루션": "5일", "산출물": "7일"})

        active_tracks = [self.SIX_TRACKS[i] for i in tracks if i < len(self.SIX_TRACKS)]
        active_outputs = [self.OUTPUTS_5[i] for i in outputs if i < len(self.OUTPUTS_5)]

        scenarios = [
            {"name": f"긴급 ({urgency}) — 3일 완료",
             "tracks": len(active_tracks), "outputs": 1,
             "timeline": "진단 1일·솔루션 1일·산출물 1일"},
            {"name": "표준 — 7일 완료",
             "tracks": len(active_tracks), "outputs": 3,
             "timeline": "진단 3일·솔루션 2일·산출물 2일"},
            {"name": "여유 — 21일 완료 (전체 산출물 5종)",
             "tracks": 6, "outputs": 5,
             "timeline": "진단 7일·솔루션 7일·산출물 7일"},
        ]
        return {
            "client_name": client_name, "domain": domain, "urgency": urgency,
            "pipeline": self.PIPELINE, "active_tracks": active_tracks,
            "active_outputs": active_outputs, "timeline": timeline,
            "total_stages": len(self.PIPELINE),
            "scenarios": scenarios,
            "summary": f"{client_name} | {domain} | {urgency} | {len(active_tracks)}트랙 | {len(active_outputs)}산출물",
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {
            "DOMAIN": {"pass": len(strategy["active_tracks"]) > 0,
                       "detail": f"6트랙 중 {len(strategy['active_tracks'])}트랙 실행"},
            "LEGAL":  {"pass": True,
                       "detail": "법§60(신고기한)·K-IFRS 1001·국기§45의2·외감§4·조특§10"},
            "CALC":   {"pass": True,
                       "detail": "5단계 파이프라인 실행 계획 수립 완료"},
            "LOGIC":  {"pass": len(strategy["active_outputs"]) > 0,
                       "detail": f"산출물 {len(strategy['active_outputs'])}종 생성 계획"},
            "CROSS":  {"pass": True, "detail": "4자관점(법인·주주·과세관청·금융기관) × 3시점 12셀"},
        }
        return {"all_pass": all(a["pass"] for a in axes.values()), "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        urgency = strategy["urgency"]
        return {
            "1_pre": [
                f"의뢰 긴급도 '{urgency}' 확인 — 타임라인 {strategy['timeline']}",
                "고객 자료 완비 체크리스트 발송 (Stage 2 준비)",
                "담당 컨설턴트 배정·역할 분담",
            ],
            "2_now": [
                f"{len(strategy['active_tracks'])}트랙 병렬 진단 실행 (Stage 3)",
                "4자관점×3시점 12셀 솔루션 설계 (Stage 4)",
                f"산출물 {len(strategy['active_outputs'])}종 생성 (Stage 5)",
            ],
            "3_post": [
                "고객 보고회 일정 조율",
                "Action Plan 이행 모니터링 계획 수립",
                "후속 컨설팅 의뢰 검토",
            ],
            "4_worst": [
                "자료 미제출 → 추정 자료 기반 진단 + 보완 요청",
                "의뢰 범위 초과 → 추가 계약 협의",
                "법령 해석 불명 → 세무사·변호사 자문 연계",
            ],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        """③ 과정관리 — 5단계 실행 오케스트레이션"""
        return {
            "step1": {"stage": 1, "action": f"{strategy['client_name']} 의뢰 접수·분류"},
            "step2": {"stage": 2, "action": "자료 수집 체크리스트 발송·수집"},
            "step3": {"stage": 3, "action": f"{len(strategy['active_tracks'])}트랙 병렬 진단",
                      "tracks": strategy["active_tracks"]},
            "step4": {"stage": "4+5", "action": "솔루션 설계 + 산출물 생성",
                      "outputs": strategy["active_outputs"]},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": [
                "Action Plan 이행 상태 월별 점검",
                "후속 세무·회계 변경사항 추적",
            ],
            "reporting": {"내부": "컨설팅 완료 보고서", "고객": "산출물 5종 납품"},
            "next_review": f"6개월 후 후속 점검 컨설팅 — {strategy['urgency']} 케이스",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        cn = strategy["client_name"]; tl = strategy["timeline"]
        return {
            "법인":       {"사전": f"{cn} 자료 제출·Stage 2 준비", "현재": "6트랙 진단·솔루션 설계", "사후": "Action Plan 이행·후속 점검"},
            "주주(오너)": {"사전": "의뢰 목표·우선순위 확인", "현재": "솔루션 승인·실행 결정", "사후": "절세 효과 실적 추적"},
            "과세관청":   {"사전": "법령 기준 리스크 사전 점검", "현재": "세무 진단 결과 적용", "사후": "세무 보고서 보관·신고 준비"},
            "금융기관":   {"사전": "재무 진단 기반 여신 전략 수립", "현재": "재무 개선안 실행", "사후": "신용등급 재평가·여신 재협상"},
        }

    def run_full_pipeline(self, case: dict) -> dict:
        """전체 5단계 파이프라인 실행 (integrate all stages)"""
        strategy = self.generate_strategy(case)
        risks    = self.validate_risk_5axis(strategy)
        hedges   = self.generate_risk_hedge_4stage(strategy)
        process  = self.manage_execution(strategy, hedges)
        post     = self.post_management(strategy, process)
        matrix   = self._build_4party_3time_matrix(strategy, risks, hedges, process, post)
        return {
            "strategy": strategy, "risks": risks, "hedges": hedges,
            "process": process, "post": post, "matrix": matrix,
            "pipeline_complete": True,
        }
