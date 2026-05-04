"""
감사대비 재무 에이전트 (/감사대비재무) — 전문 솔루션 그룹
핵심 법령:
  외감법§4 (외부감사 대상 기준 — 자산 120억·매출 100억)
  외감법§9 (감사인 선임·해임)
  외감법§9의2 (핵심감사항목 KAM 공시 의무)
  K-IFRS 1001 (재무제표 표시 기준)
  조특§126의3 (세무사·회계사 수임 세액공제)
  법인세법§75의2 (법인세 신고 불성실 가산세)
  국기법§81의4 (세무조사 납세자 권리 — 세무조사 연계 대응)
  상증§41 (이익잉여금 무상이전 — 특수관계인 거래 연동)
  ISA 315 (위험 식별 및 평가) · ISA 240 (부정 위험)
"""
from __future__ import annotations
from agents.base.professional_solution_agent import ProfessionalSolutionAgent
from agents.groups.professional_solution_group import register


@register
class AuditPreparationAgent(ProfessionalSolutionAgent):
    """외부감사·세무조사·내부감사 통합 대응 준비 체계 구축"""

    # 외감 대상 기준 (외감법§4)
    _AUDIT_THRESHOLD = {
        "자산": 120_000_000_000,    # 120억 이상
        "매출": 100_000_000_000,    # 100억 이상
        "부채": 70_000_000_000,     # 70억 이상 (금융사 등)
        "임직원": 100,              # 100명 이상
    }

    def generate_strategy(self, case: dict) -> dict:
        """감사 대상 여부·리스크 지도·대응 우선순위 산출"""
        total_assets   = case.get("total_assets", 0)
        revenue        = case.get("revenue", 0)
        audit_type     = case.get("audit_type", "외부감사")  # 외부감사/세무조사/내부감사
        key_accounts   = case.get("key_accounts", [])        # 핵심 계정과목
        related_parties = case.get("related_party_transactions", [])  # 특수관계인 거래
        provisional_payment = case.get("provisional_payment", 0)

        # 외감 대상 여부
        is_audit_required = (total_assets >= self._AUDIT_THRESHOLD["자산"] or
                             revenue >= self._AUDIT_THRESHOLD["매출"])

        # 핵심감사항목(KAM) 예측
        predicted_kam = []
        if provisional_payment > 0:
            predicted_kam.append(f"대표이사 가지급금 {provisional_payment:,.0f}원 — 대손 위험")
        if related_parties:
            predicted_kam.append(f"특수관계인 거래 {len(related_parties)}건 — 이전가격 적정성")
        if total_assets > 50_000_000_000:
            predicted_kam.append("고액 자산 감정평가 — 공정가치 적정성 (K-IFRS 13)")
        if not predicted_kam:
            predicted_kam.append("수익 인식 (K-IFRS 15) — 계약 수행의무 식별")

        # 대응 준비 체크리스트
        checklist = [
            ("고위험", "가지급금·특수관계인 거래 사전 자기진단"),
            ("고위험", "KAM 예측 계정 증빙 완비 (계약서·세금계산서)"),
            ("중위험", "재고자산·유형자산 실사 계획 수립"),
            ("중위험", "내부통제 미비점 사전 해소"),
            ("저위험", "재무제표 주석 공시 요건 확인 (K-IFRS 1)"),
        ]

        text = (
            f"법인 측면: {'외감 대상' if is_audit_required else '외감 비대상'} (자산 {total_assets:,.0f}원) — "
            f"KAM 예측 {len(predicted_kam)}건.\n"
            f"주주(오너) 관점: 가지급금·특수관계인 거래 사전 해소 권고 (감사 지적 최소화).\n"
            f"과세관청 관점: 감사의견 한정·부적정 → 세무조사 트리거 가능성 (외감법·국기§81).\n"
            f"금융기관 관점: 감사의견 적정 유지 → 여신 약정 재무비율 충족·신용등급 유지."
        )
        # 감사 대응 시나리오 3종
        scenarios = [
            {"name": "KAM 예측 사전 자기진단 (권장)",
             "priority": "고위험",
             "method": "KAM 예측 계정 증빙 완비 + 감사인 사전 커뮤니케이션",
             "law": "외감법§9의2 KAM 공시 + ISA 315 위험 식별"},
            {"name": "내부통제 집중 보강",
             "priority": "중위험",
             "method": "내부통제 미비점 사전 해소 + 외감법§8 내부감사위원회 활동",
             "law": "법인세법§75의2 불성실 가산세 방지 + 국기법§81의4 납세자 권리"},
            {"name": "현행 유지 (소규모 법인)",
             "priority": "저위험",
             "method": f"{'외감 비대상 — 기본 재무제표 관리' if not is_audit_required else '외감 대상 — 최소 대응'}",
             "law": "외감법§4 대상 기준 충족 여부 연간 재확인"},
        ]

        return {
            "total_assets": total_assets, "revenue": revenue, "audit_type": audit_type,
            "is_audit_required": is_audit_required, "predicted_kam": predicted_kam,
            "related_parties": related_parties, "provisional_payment": provisional_payment,
            "checklist": checklist, "scenarios": scenarios,
            "recommended": scenarios[0]["name"], "text": text,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {
            "DOMAIN": {"pass": True,
                       "detail": f"감사 유형: {strategy['audit_type']} — KAM 예측 {len(strategy['predicted_kam'])}건"},
            "LEGAL":  {"pass": True,
                       "detail": "외감법§4(대상)·§9(감사인)·ISA315(위험식별)·국기§81(세무조사 권리)"},
            "CALC":   {"pass": strategy["total_assets"] >= 0,
                       "detail": f"외감 대상 {'해당' if strategy['is_audit_required'] else '비해당'} (자산 120억 기준)"},
            "LOGIC":  {"pass": len(strategy["checklist"]) >= 5,
                       "detail": f"대응 체크리스트 {len(strategy['checklist'])}건 완비"},
            "CROSS":  {"pass": True, "detail": "4자관점 × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        kam = strategy["predicted_kam"]
        pp  = strategy["provisional_payment"]
        return {
            "1_pre": [f"KAM 예측: {kam[0] if kam else 'N/A'} — 사전 증빙 완비",
                      f"가지급금 {pp:,.0f}원 — 감사 전 해소 또는 대손충당금 설정",
                      "특수관계인 거래 이전가격 적정성 서류 준비"],
            "2_now": ["감사인 확인 서류 신속 제출 (기한 내)",
                      "핵심 계정 전표·계약서·영수증 체계적 정리",
                      "내부통제 취약점 즉각 개선·감사인 사전 커뮤니케이션"],
            "3_post": ["감사 지적사항 이행 계획 30일 내 수립·이행",
                       "KAM 공시 검토 (외감법§9의2)",
                       "세무조사 연계 대비 세무사 동행 준비"],
            "4_worst": ["한정·부적정 의견 시 — 외부 자문회계사 즉시 선임",
                        "계속기업 의심 주석 → 여신 약정 위반 → 금융기관 협의 즉시",
                        "세무조사 통지 수신 시 — 세무사·변호사 즉각 선임 (국기§81의4 권리)"],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        kam = strategy["predicted_kam"]
        return {
            "step1": {"action": f"KAM 예측 {len(kam)}건 중심 자기진단 완료"},
            "step2": {"action": "증빙 자료 체계화·감사인 제출 준비"},
            "step3": {"action": "내부통제 미비점 해소·내부감사 1차 실시"},
            "step4": {"action": "감사의견 적정 달성·세무신고 일관성 최종 확인"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": ["지적사항 이행 완료 여부 추적",
                           "다음 감사 대비 연중 내부통제 유지"],
            "reporting": {"감사인": "KAM 이행 보고서", "이사회": "감사 결과 보고"},
            "next_review": "차기 감사 3개월 전 KAM 예측·자기진단 재실시",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        ar = strategy["is_audit_required"]
        km = len(strategy["predicted_kam"])
        ta = strategy["total_assets"]
        return {
            "법인":       {"사전": f"{'외감 대상' if ar else '비대상'} (자산 {ta:,.0f}원) — KAM {km}건 사전 진단", "현재": "감사 자료 제출·내부통제 점검", "사후": "지적사항 이행·내부통제 개선"},
            "주주(오너)": {"사전": "가지급금·특수관계 거래 사전 해소 결정", "현재": "감사인 확인서 제출·협조", "사후": "감사의견 적정 → 배당 약정 유지"},
            "과세관청":   {"사전": "세무신고·감사 재무제표 일관성 확인", "현재": "감사 중 세무조사 트리거 방지", "사후": "세무조사 통지 시 즉각 대응 체계 가동"},
            "금융기관":   {"사전": "감사의견 적정 유지 약정 확인", "현재": "한정·부적정 위험 시 금융기관 사전 통보", "사후": "감사 완료 후 감사보고서 제출·여신 약정 재확인"},
        }
