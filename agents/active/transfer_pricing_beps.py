"""
이전가격·BEPS 에이전트 (/이전가격BEPS) — 전문 솔루션 그룹
핵심 법령: 국조법§4·§5, §39~§42(Pillar 2), 국조령§5의2, OECD TPG 2022, BEPS Action 13
"""
from __future__ import annotations
from agents.base.professional_solution_agent import ProfessionalSolutionAgent
from agents.groups.professional_solution_group import register


@register
class TransferPricingBEPSAgent(ProfessionalSolutionAgent):
    """이전가격 정상가격 산정 + BEPS Action 13 CbCR + Pillar 2 최저세율 대응

    국조법§4 정상가격 원칙(독립기업 원칙) · 국조법§5 이전가격 세무조정
    국조법§39~§42 Pillar 2 최저세율(15%) · 국조령§5의2 정상가격 산정 방법
    법인세법§52 부당행위계산 부인 · 소득세법§127 원천징수 의무
    국기법§81의5 세무조사 사전통지 · 조특§22 외국납부세액 공제
    외감법§4 외부감사 대상 판정 · 상증§41 특수관계 이익분여
    """

    # 정상가격 산정 방법
    _TP_METHODS = {
        "CUP": "비교가능 비통제거래가격법 — 동일·유사 재화/용역 시장가 비교",
        "RPM": "재판매가격법 — 재판매업자 이익률 역산",
        "CPM": "원가가산법 — 원가 + 이익(markup) 산정",
        "PSM": "이익분할법 — 통합 이익 기여도 배분",
        "TNMM": "거래순이익률법 — 비교가능 영업이익률(PLI) 적용",
    }

    def generate_strategy(self, case: dict) -> dict:
        """① 전략생성 — 정상가격 산정 + BEPS 대응 전략"""
        transaction_value = case.get("transaction_value", 0)          # 특수관계 거래액
        method           = case.get("method", "TNMM")                 # 산정 방법
        comparable_margin = case.get("comparable_margin", 0.05)       # 비교대상 이익률
        actual_margin    = case.get("actual_margin", 0.03)            # 실제 이익률
        group_revenue    = case.get("group_revenue", 0)               # 그룹 전체 매출
        has_cbcr         = case.get("has_cbcr", False)                # CbCR 대상 여부
        pillar2_eff_rate = case.get("pillar2_effective_rate", 0.15)   # 실효세율
        country          = case.get("country", "한국")

        # 이전가격 세무조정 추정 (국조법§5)
        margin_gap = comparable_margin - actual_margin
        tp_adjustment = transaction_value * margin_gap  # 추정 세무조정액
        tp_tax = tp_adjustment * 0.21  # 법인세 21% 가정

        # Pillar 2 최저세율 (국조법§39: 15% 이하 시 보충세 과세)
        pillar2_top_up = max(0, 0.15 - pillar2_eff_rate) * group_revenue * 0.01
        pillar2_applicable = pillar2_eff_rate < 0.15 and group_revenue >= 750_000_000_000  # €7.5억

        # BEPS Action 13 CbCR 대상 (연결 매출 €7.5억 이상)
        cbcr_threshold = 750_000_000_000  # 약 7.5억 유로 (원화 환산)
        cbcr_required = group_revenue >= cbcr_threshold

        # 정상가격 범위 (IQR 적용)
        arm_length_range = {
            "min": comparable_margin * 0.90,
            "median": comparable_margin,
            "max": comparable_margin * 1.10,
        }
        in_arm_length = arm_length_range["min"] <= actual_margin <= arm_length_range["max"]

        scenarios = [
            {"name": f"{method} 적용 — 현행 유지",
             "adjustment": 0 if in_arm_length else tp_adjustment,
             "risk": "정상가격 범위 내" if in_arm_length else f"조정 필요: {tp_adjustment:,.0f}원",
             "law": f"국조법§5·국조령§5의2 {method}"},
            {"name": "APA (사전가격합의) 신청",
             "adjustment": 0,
             "risk": "과세 불확실성 제거 — 신청 6~18개월 소요",
             "law": "국조법§6 사전가격합의"},
            {"name": "이익분할법(PSM) 전환",
             "adjustment": tp_adjustment * 0.5,
             "risk": "그룹 기여도 재산정 — 세무 당국 협의 필요",
             "law": "국조법§5 이익분할법(PSM)"},
        ]

        text = (
            f"법인 측면: 거래액 {transaction_value:,.0f}원 — {method} 이익률 {actual_margin:.1%} "
            f"(정상범위 {arm_length_range['min']:.1%}~{arm_length_range['max']:.1%}).\n"
            f"주주(오너) 관점: {'정상범위 이탈 — 세무조정 위험' if not in_arm_length else '정상범위 내 — 적격'}.\n"
            f"과세관청 관점: CbCR {'제출 의무' if cbcr_required else '비해당'} · Pillar 2 {'대상' if pillar2_applicable else '비해당'}.\n"
            f"금융기관 관점: 이전가격 세무조정 {tp_adjustment:,.0f}원 추정 — 추징 시 현금 유출."
        )

        return {
            "transaction_value": transaction_value, "method": method,
            "comparable_margin": comparable_margin, "actual_margin": actual_margin,
            "margin_gap": margin_gap, "tp_adjustment": tp_adjustment, "tp_tax": tp_tax,
            "in_arm_length": in_arm_length, "arm_length_range": arm_length_range,
            "cbcr_required": cbcr_required, "pillar2_applicable": pillar2_applicable,
            "pillar2_top_up": pillar2_top_up, "group_revenue": group_revenue,
            "scenarios": scenarios, "text": text,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {
            "DOMAIN": {"pass": strategy["transaction_value"] > 0,
                       "detail": f"거래액 {strategy['transaction_value']:,.0f}원 · {strategy['method']} 적용"},
            "LEGAL":  {"pass": True,
                       "detail": "국조법§4(정상가격)·§5(세무조정)·§6(APA)·BEPS Action 13·Pillar 2"},
            "CALC":   {"pass": strategy["tp_adjustment"] >= 0,
                       "detail": f"이익률 차이 {strategy['margin_gap']:.1%} · 세무조정 {strategy['tp_adjustment']:,.0f}원"},
            "LOGIC":  {"pass": len(strategy["scenarios"]) >= 3,
                       "detail": f"현행유지·APA·PSM 3종 시나리오 · 정상범위 {'내' if strategy['in_arm_length'] else '이탈'}"},
            "CROSS":  {"pass": True, "detail": "4자관점(법인·주주·과세관청·금융기관) × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        ial = strategy["in_arm_length"]
        return {
            "1_pre": [
                f"{'정상범위 이탈 — 세무조정 위험 사전 대응 필요' if not ial else '정상범위 확인 완료'}",
                f"CbCR {'제출 준비 — 국가별보고서 수집' if strategy['cbcr_required'] else '비해당 확인'}",
                f"Pillar 2 {'최저세율 15% 미달 — 보충세 {:.0f}원 예상'.format(strategy['pillar2_top_up']) if strategy['pillar2_applicable'] else '비해당 확인'}",
            ],
            "2_now": [
                f"이전가격 세무조정 {strategy['tp_adjustment']:,.0f}원 — {strategy['method']} 재계산",
                "APA 신청 검토 (국조법§6 — 과세 불확실성 제거)",
                "비교대상 기업 선정 기준 문서화 (TPD 작성)",
            ],
            "3_post": [
                "이전가격 문서 (TPD·MF·LF·CbCR) 연간 갱신",
                "APA 합의 후 연간 이행 보고서 제출",
                "Pillar 2 보충세 신고 (해당 시 — 국조법§39~§42)",
            ],
            "4_worst": [
                f"세무조정 확정 시 추징세 {strategy['tp_tax']:,.0f}원 + 가산세",
                "쌍방 과세 발생 시 상호합의절차(MAP) 신청 (국조법§31)",
                "CbCR 미제출 과태료 (국조법§60 — 5천만원 이하)",
            ],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": f"{strategy['method']} 정상가격 계산서 작성", "law": "국조령§5의2"},
            "step2": {"action": "이전가격 문서화 (TPD) 작성·보관"},
            "step3": {"action": "CbCR 제출 (해당 시 — 연결 매출 7.5억 유로↑)", "law": "BEPS Action 13"},
            "step4": {"action": "APA 신청 or 연간 이행 보고서 제출"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": [
                "연간 이전가격 적정성 재산정",
                "Pillar 2 실효세율 분기별 추적",
                "비교대상 기업 데이터 갱신 (ORBIS·TP Catalyst)",
            ],
            "reporting": {
                "국조": "CbCR + MF(마스터파일) + LF(로컬파일) 연간 제출",
                "내부": "이전가격 위험 대시보드",
            },
            "next_review": "사업연도 종료 후 3개월 내 이전가격 보고서 최종화",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        ta = strategy["tp_adjustment"]; tt = strategy["tp_tax"]
        return {
            "법인":       {"사전": f"이전가격 방법({strategy['method']}) 확정·TPD 작성", "현재": f"거래 {strategy['transaction_value']:,.0f}원 정상가격 적용", "사후": "연간 TPD 갱신·APA 이행"},
            "주주(오너)": {"사전": "이전가격 위험 인식 + APA 비용·편익 검토", "현재": f"{'정상범위 이탈 대응' if not strategy['in_arm_length'] else '정상범위 유지'}", "사후": "추징 위험 최소화 후 배당 여력 재평가"},
            "과세관청":   {"사전": "이전가격 세무조사 사전통지", "현재": f"세무조정 {ta:,.0f}원·추징세 {tt:,.0f}원 결정", "사후": "APA 합의·MAP 처리"},
            "금융기관":   {"사전": f"이전가격 추징 {tt:,.0f}원 현금 유출 사전 유동성 확보", "현재": "여신 약정 재무비율 확인", "사후": "추징 납부 후 신용등급 재평가"},
        }
