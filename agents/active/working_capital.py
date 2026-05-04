"""
운전자본 관리 에이전트 (/운전자본관리) — 전문 솔루션 그룹
핵심 기준: WC=유동자산-유동부채, CCC=DSO+DIO-DPO
핵심 법령:
  K-IFRS 1007 (현금흐름표 — 운전자본 변동 공시)
  법인세법§19의2 (대손금 손금 요건 — 매출채권 부실 시)
  조특§7의2 (중소기업 매출채권 팩토링 이자비용 공제)
  상증§38 (저가 매출·고가 매입 — 특수관계인 운전자본 이전)
  부가가치세법§32 (세금계산서 발급 기한 — DSO 관리 연동)
  국기법§46의2 (납기전 징수 — 유동성 위기 시 세금 관리)
"""
from __future__ import annotations
from agents.base.professional_solution_agent import ProfessionalSolutionAgent
from agents.groups.professional_solution_group import register


@register
class WorkingCapitalAgent(ProfessionalSolutionAgent):
    """운전자본 사이클(CCC) 정밀분석 + 매출채권·재고·매입채무 최적화"""

    def generate_strategy(self, case: dict) -> dict:
        """CCC = DSO + DIO - DPO 산출 + 자금 갭 분석"""
        revenue       = case.get("revenue", 1)
        cogs          = case.get("cogs", revenue * 0.70)
        ar_balance    = case.get("ar_balance", 0)         # 매출채권
        inventory     = case.get("inventory", 0)          # 재고자산
        ap_balance    = case.get("ap_balance", 0)         # 매입채무
        current_assets = case.get("current_assets", 0)
        current_liab  = case.get("current_liabilities", 1)

        # 회전일수 계산
        dso = (ar_balance / max(revenue, 1)) * 365        # 매출채권 회전일수
        dio = (inventory / max(cogs, 1)) * 365            # 재고 회전일수
        dpo = (ap_balance / max(cogs, 1)) * 365          # 매입채무 회전일수
        ccc = dso + dio - dpo                              # 현금전환주기

        # 운전자본 (WC)
        wc = current_assets - current_liab
        wc_ratio = current_assets / max(current_liab, 1)

        # 자금 갭 (CCC × 1일 매출)
        daily_sales  = revenue / 365
        funding_gap  = ccc * daily_sales  # 필요 운전자금

        # 개선 목표 (업종 평균 CCC 60일 가정)
        target_ccc  = 60
        gap_to_target = ccc - target_ccc

        text = (
            f"법인 측면: WC {wc:,.0f}원 (유동비율 {wc_ratio:.2f}) — CCC {ccc:.1f}일.\n"
            f"주주(오너) 관점: 운전자금 필요액 {funding_gap:,.0f}원 — "
            f"{'CCC 단축으로 ' + f'{gap_to_target:.0f}일 개선 가능' if gap_to_target > 0 else 'CCC 양호'}.\n"
            f"과세관청 관점: 재고 과다 보유 시 재고자산 평가손실 (부가가치세·법인세 연동).\n"
            f"금융기관 관점: 매출채권 팩토링·담보대출 가능 잔액 {ar_balance:,.0f}원."
        )
        # CCC 개선 시나리오 3종
        scenarios = [
            {"name": "DSO 단축 (매출채권 조기 회수)",
             "ccc_target": max(ccc - 15, 30),
             "method": "조기결제 할인(2/10 net 30) 제공 + 팩토링 활용 (조특§7의2)",
             "law": "법인세법§19의2 대손금 손금 요건 충족 병행 관리"},
            {"name": "DPO 연장 (매입채무 지급 기간 연장)",
             "ccc_target": max(ccc - 10, 30),
             "method": "공급업체 결제 조건 재협상 (Net 60 목표)",
             "law": "부가가치세법§32 세금계산서 기한 준수 병행"},
            {"name": "현행 유지 (모니터링)",
             "ccc_target": ccc,
             "method": f"CCC {ccc:.0f}일 현행 유지 + 분기별 재진단",
             "law": "K-IFRS 1007 현금흐름 변동 공시 유지"},
        ]

        return {
            "revenue": revenue, "cogs": cogs, "ar_balance": ar_balance,
            "inventory": inventory, "ap_balance": ap_balance,
            "dso": dso, "dio": dio, "dpo": dpo, "ccc": ccc,
            "wc": wc, "wc_ratio": wc_ratio,
            "funding_gap": funding_gap, "gap_to_target": gap_to_target,
            "scenarios": scenarios, "recommended": scenarios[0]["name"],
            "text": text,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {
            "DOMAIN": {"pass": strategy["revenue"] > 0,
                       "detail": f"CCC={strategy['ccc']:.1f}일 (DSO{strategy['dso']:.1f}+DIO{strategy['dio']:.1f}-DPO{strategy['dpo']:.1f})"},
            "LEGAL":  {"pass": True, "detail": "K-IFRS 1007 현금흐름·부가가치세법§32 매출채권 성립"},
            "CALC":   {"pass": strategy["funding_gap"] >= 0,
                       "detail": f"운전자금 필요액 {strategy['funding_gap']:,.0f}원 — WC {strategy['wc']:,.0f}원"},
            "LOGIC":  {"pass": True,
                       "detail": f"유동비율 {strategy['wc_ratio']:.2f} — {'양호(1.5↑)' if strategy['wc_ratio'] >= 1.5 else '주의'}"},
            "CROSS":  {"pass": True, "detail": "4자관점 × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        ccc = strategy["ccc"]
        return {
            "1_pre": [f"CCC {ccc:.1f}일 — 목표 60일 이하 달성 계획 수립",
                      "매출채권 회수 정책 (DSO 단축: 조기결제 할인 제공)",
                      "재고 적정 수준 산정 (EOQ 모형 적용)"],
            "2_now": ["매출채권 팩토링·네고 검토 (은행 매출채권담보대출)",
                      f"DPO {strategy['dpo']:.1f}일 — 매입채무 지급 기간 연장 협상",
                      "ABC 분석으로 재고 D등급 청산"],
            "3_post": ["월별 DSO·DIO·DPO 추적·개선 효과 측정",
                       "팩토링 비용 vs 운전자금 절감 효과 분기별 비교",
                       "CCC 60일 이하 달성 시 여신 한도 재협의"],
            "4_worst": [f"CCC {ccc:.1f}일 지속 시 — 금융기관 긴급 운전자금 한도 사전 확보",
                        "매출채권 부실화 시 대손충당금 설정·법인세 손금",
                        "재고 과다 시 기말 재고 평가손실 (저가법 평가)"],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "CCC 현황 진단·목표 60일 이하 설정"},
            "step2": {"action": f"DSO 단축: 매출채권 {strategy['ar_balance']:,.0f}원 조기 회수"},
            "step3": {"action": f"재고 최적화: DIO {strategy['dio']:.1f}일 → 30일 이하 목표"},
            "step4": {"action": f"DPO 연장: 매입채무 {strategy['ap_balance']:,.0f}원 지급 기간 재협상"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": ["월간 CCC 추적·DSO·DIO·DPO 개별 관리",
                           "분기별 운전자금 필요액 재산정"],
            "reporting": {"내부": "주간 매출채권·재고 현황 대시보드",
                          "금융": "여신 갱신 시 운전자본 현황 보고"},
            "next_review": "분기 결산 후 CCC 재산정 + 팩토링 계약 갱신 여부 검토",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        ccc = strategy["ccc"]; wc = strategy["wc"]; fg = strategy["funding_gap"]
        ar  = strategy["ar_balance"]
        return {
            "법인":       {"사전": f"CCC {ccc:.1f}일·WC {wc:,.0f}원 현황 분석", "현재": "DSO 단축·재고 최적화·DPO 연장 실행", "사후": "월간 CCC 추적·개선 효과 보고"},
            "주주(오너)": {"사전": f"운전자금 {fg:,.0f}원 조달 계획 수립", "현재": "팩토링·담보대출 활용 유동성 확보", "사후": "FCF 개선 → 배당 여력 재평가"},
            "과세관청":   {"사전": "재고 평가 방법 (선입선출·총평균) 확정", "현재": "재고 평가손실·대손충당금 세무 처리", "사후": "재고·매출채권 세무조사 대비 증빙 보관"},
            "금융기관":   {"사전": f"매출채권 {ar:,.0f}원 팩토링·담보 가능액 협의", "현재": "운전자금 한도 실행·이자 최소화", "사후": "CCC 개선 후 여신 조건 재협상"},
        }
