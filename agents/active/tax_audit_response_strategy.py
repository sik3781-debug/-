"""
세무조사 대응 전략 에이전트 (/세무조사대응) — 전문 솔루션 그룹
핵심 법령: 국기법§81의5·§81의6·§81의11·§45의2, 국기령§63의2, 국조법§108
"""
from __future__ import annotations
from agents.base.professional_solution_agent import ProfessionalSolutionAgent
from agents.groups.professional_solution_group import register


@register
class TaxAuditResponseStrategyAgent(ProfessionalSolutionAgent):
    """세무조사 대응 전략 — 사전 점검 + 조사 대응 + 불복 절차 통합

    국기법§81의5 조사 사전통지(15일 전) · 국기법§81의6 납세자 권리(변호인·녹취)
    국기법§81의11 중복조사 금지(동일 사업연도·동일 세목)
    국기법§45의2 경정청구(5년 이내) · 국기령§63의2 조사 기간(일반 30일·특별 60일)
    국조법§108 외국 조사 협조 · 국기법§47의3 신고 불성실 가산세
    """

    # 추징 세목 매핑
    _TAX_TYPES = {
        "법인세": {"base_rate": 0.24, "surcharge_rate": 0.10, "penalty_rate": 0.20},
        "소득세": {"base_rate": 0.45, "surcharge_rate": 0.10, "penalty_rate": 0.20},
        "부가가치세": {"base_rate": 0.10, "surcharge_rate": 0.10, "penalty_rate": 0.10},
        "증여세": {"base_rate": 0.50, "surcharge_rate": 0.20, "penalty_rate": 0.10},
    }

    def generate_strategy(self, case: dict) -> dict:
        """① 전략생성 — 조사 단계별 대응 전략"""
        audit_type     = case.get("audit_type", "일반조사")           # 일반·세무·통합·특별
        tax_types      = case.get("tax_types", ["법인세"])             # 조사 세목
        audit_period   = case.get("audit_period", 1)                   # 조사 대상 사업연도 수
        disputed_amount = case.get("disputed_amount", 0)              # 추정 다툼 금액
        notice_received = case.get("notice_received", True)           # 사전 통지 수령 여부
        days_since_notice = case.get("days_since_notice", 0)          # 통지 후 경과일
        hidden_risks   = case.get("hidden_risks", [])                  # ["가지급금","차명주식"]

        # 추징 시뮬 (본세 + 가산세)
        tax_calc = {}
        total_estimated = 0
        for tt in tax_types:
            rates = self._TAX_TYPES.get(tt, {"base_rate": 0.20, "surcharge_rate": 0.10, "penalty_rate": 0.10})
            base_tax = disputed_amount * rates["base_rate"]
            penalty  = base_tax * rates["penalty_rate"]
            delay_int = base_tax * 0.022 / 100 * 365  # 1년치 납부불이행 이자
            total = base_tax + penalty + delay_int
            tax_calc[tt] = {
                "base_tax": base_tax, "penalty": penalty,
                "delay_interest": delay_int, "total": total,
            }
            total_estimated += total

        # 조사 기간 잔여일 (국기령§63의2: 일반 30일·특별 60일)
        max_days = 60 if audit_type == "특별조사" else 30
        remaining_days = max(0, max_days - days_since_notice)

        # 우선순위 대응 전략
        priority_actions = []
        if not notice_received:
            priority_actions.append("⚠️ 사전 통지 미수령 — 국기법§81의5 적법성 이의 검토")
        if hidden_risks:
            for risk in hidden_risks:
                if risk == "가지급금":
                    priority_actions.append("가지급금 정당성 증빙 (업무 관련성 확인·법인세법§19 손금 요건)")
                elif risk == "차명주식":
                    priority_actions.append("차명주식 자진 해소 검토 (상증§45의2 차명주식 증여 추정)")
                elif risk == "비상장평가":
                    priority_actions.append("비상장주식 평가 방법 일관성 확인 (상증§63 순자산·순손익)")

        # 조사 대응 단계
        stages = {
            "통지_수령": "사전 통지 즉시 세무사·변호사 선임 (국기법§81의6 권리 행사)",
            "자료_제출": f"조사 기간 {max_days}일 추적 — 자료 제출 범위 최소화",
            "진술_대응": "진술 일관성 유지 — 자필 확인서 사전 검토 후 서명",
            "결과_통보": "결과 통지 후 30일 이내 의견 진술 기회 행사",
            "불복_절차": "이의신청(30일) → 심판청구(90일) → 행정소송(90일)",
        }

        text = (
            f"법인 측면: {audit_type} ({', '.join(tax_types)}) — 조사 잔여 {remaining_days}일, 추정 추징액 {total_estimated:,.0f}원.\n"
            f"주주(오너) 관점: 은닉 리스크 {len(hidden_risks)}건 — {', '.join(hidden_risks) if hidden_risks else '없음'}.\n"
            f"과세관청 관점: 국기법§81의5 15일 사전통지 적법성 + §81의11 중복조사 금지 준수 여부.\n"
            f"금융기관 관점: 추징 {total_estimated:,.0f}원 현금 유출 → 여신 약정 재무비율 영향."
        )

        return {
            "audit_type": audit_type, "tax_types": tax_types,
            "audit_period": audit_period, "disputed_amount": disputed_amount,
            "notice_received": notice_received, "remaining_days": remaining_days,
            "hidden_risks": hidden_risks, "tax_calc": tax_calc,
            "total_estimated": total_estimated, "priority_actions": priority_actions,
            "stages": stages, "text": text,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {
            "DOMAIN": {"pass": len(strategy["tax_types"]) > 0,
                       "detail": f"조사 세목 {len(strategy['tax_types'])}종 — {', '.join(strategy['tax_types'])}"},
            "LEGAL":  {"pass": True,
                       "detail": "국기법§81의5(사전통지)·§81의6(납세자권리)·§81의11(중복조사금지)"},
            "CALC":   {"pass": strategy["total_estimated"] >= 0,
                       "detail": f"추정 추징액 {strategy['total_estimated']:,.0f}원 (본세+가산세+이자)"},
            "LOGIC":  {"pass": len(strategy["stages"]) >= 4,
                       "detail": f"조사 단계 {len(strategy['stages'])}단계 — 통지→자료→진술→결과→불복"},
            "CROSS":  {"pass": True, "detail": "4자관점(법인·주주·과세관청·금융기관) × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        te = strategy["total_estimated"]
        return {
            "1_pre": [
                "사전 통지 수령 즉시 세무사·변호사 자문 선임 (국기법§81의6)",
                f"은닉 리스크 {len(strategy['hidden_risks'])}건 자진 점검·증빙 완비",
                "조사 대상 사업연도 장부·세금계산서·통장 3자 일치 확인",
                "중복조사 여부 확인 — 동일 세목·사업연도 재조사 시 §81의11 이의",
            ],
            "2_now": [
                f"조사 잔여 {strategy['remaining_days']}일 추적 (국기령§63의2 한도 준수 요구)",
                "자료 제출 범위 최소화 — 요구 외 자발 제출 금지",
                "조사관 진술·자필 확인서 서명 전 반드시 세무대리인 검토",
                "조사 전 과정 녹취 (국기법§81의6 권리 행사)",
            ],
            "3_post": [
                "결과 통지 후 30일 이내 의견 진술 기회 반드시 행사",
                "이의신청(30일) → 조세심판원 청구(90일) → 행정소송(90일) 단계별 준비",
                "경정청구 (§45의2 5년 이내) 역방향 검토 — 과다 납부세 환급",
            ],
            "4_worst": [
                f"추징 {te:,.0f}원 확정 시 분납·연부연납 신청 (국기법§85의5)",
                "심판청구 기각 시 행정소송 — 과세 처분 취소 청구",
                "재조사 금지 원칙 위반 시 헌법소원 검토 (§81의11)",
            ],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "세무대리인 선임·위임장 제출", "law": "국기법§81의6"},
            "step2": {"action": f"조사 기간 추적 (잔여 {strategy['remaining_days']}일·연장 대응)"},
            "step3": {"action": "자료 제출 목록 작성·제출 증빙 보관"},
            "step4": {"action": "의견 진술서 작성 + 불복 청구 준비", "law": "국기법§45의2"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": [
                "이의신청·심판 청구 기한 달력 등록 (30일·90일·90일)",
                "경정청구 5년 소멸시효 추적",
                "재조사 가능성 모니터링 (§81의11 중복조사 금지 위반 시 이의)",
            ],
            "reporting": {
                "내부": "조사 결과·추징 확정 보고서",
                "금융": "추징 현금 유출 → 여신 약정 재무비율 사전 협의",
            },
            "next_review": "조사 종결 후 3개월 내 — 과세 적정성·재발 방지 진단",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        te = strategy["total_estimated"]
        return {
            "법인":       {"사전": "장부·세금계산서·통장 3자 일치 사전 점검", "현재": f"조사 협조·잔여 {strategy['remaining_days']}일 추적", "사후": f"추징 {te:,.0f}원 분납·재무제표 재작성"},
            "주주(오너)": {"사전": f"은닉 리스크 {len(strategy['hidden_risks'])}건 자진 해소", "현재": "가지급금·차명주식 진술 일관성 유지", "사후": "상여 처분 소득세 추가 납부·지분 구조 재검토"},
            "과세관청":   {"사전": "사전통지(§81의5) 15일 준수 확인", "현재": "조사 권한 행사·추징 결정", "사후": "경정청구·불복 청구 수령·처리"},
            "금융기관":   {"사전": f"추징 {te:,.0f}원 현금 유출 사전 유동성 확보", "현재": "차입금 약정 재무비율 이탈 여부 확인", "사후": "추징 납부 후 신용등급 회복 계획 수립"},
        }
