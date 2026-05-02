"""
GiftTaxAgent: 증여세 시뮬레이션 전담 에이전트

근거 법령:
  - 상속세및증여세법 §53 (증여재산공제)
  - 상속세및증여세법 §53의2 (혼인·출산공제)
  - 상속세및증여세법 §56 (세율)
  - 상속세및증여세법 §57 (세대생략 할증)

주요 기능:
  - 증여재산공제 자동 적용 (배우자 6억 / 성년 5천만 / 미성년 2천만 / 기타 1천만)
  - 혼인·출산공제 (+1억, 합산 최대 1억)
  - 세대생략 할증 30% (수증자가 자녀의 자녀인 경우)
  - 10년 합산 과세 추적
  - 증여 분산 최적화 시뮬레이션
"""

from __future__ import annotations
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 상속세및증여세법 전문 세무 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 증여세 계산 (상증세법 §53~§58)\n"
    "- 증여재산공제 및 혼인·출산공제 (§53, §53의2)\n"
    "- 세대생략 증여 할증과세 (§57: 30% 할증)\n"
    "- 10년 합산 과세 전략적 활용\n"
    "- 비상장주식·부동산·금전 증여 비교\n"
    "- 최적 증여 분산 전략 (수증자·시기·자산유형)\n\n"
    "【분석 기준】\n"
    "- 법인 / 주주(오너) / 과세관청 3자 관점 교차 분석\n"
    "- 최신 개정 세법 반영 (2026년 귀속 기준)\n"
    "- 면책 문구 없이 단정적 전문가 언어 사용\n\n"
    "【목표】\n"
    "오너 가족의 증여세 부담을 법적 범위 내에서 최소화하고,\n"
    "10년 단위 증여 계획 수립을 통해 가업승계 비용을 사전에 절감한다."
)


class GiftTaxAgent(BaseAgent):
    name = "GiftTaxAgent"
    role = "증여세 시뮬레이션 전담 전문가"
    system_prompt = _SYS

    # ── 공제 한도표 (상증세법 §53, §53의2 / 2026년 기준) ─────────────────
    DEDUCTIONS = {
        "배우자":         600_000_000,   # 6억 (10년 합산)
        "직계존비속_성년": 50_000_000,    # 5천만 (10년 합산)
        "직계존비속_미성년": 20_000_000,  # 2천만 (10년 합산)
        "기타친족":       10_000_000,    # 1천만 (10년 합산)
    }
    MARRIAGE_BIRTH_DEDUCTION = 100_000_000  # 혼인·출산공제 합산 최대 1억

    # ── 증여세율표 (상증세법 §56) ─────────────────────────────────────────
    @staticmethod
    def _calc_gift_tax(taxable: float) -> float:
        """과세표준 → 산출세액 (상증세법 §56)."""
        if taxable <= 0:
            return 0.0
        elif taxable <= 100_000_000:          # 1억 이하: 10%
            return taxable * 0.10
        elif taxable <= 500_000_000:          # 5억 이하: 20% (누진공제 1천만)
            return taxable * 0.20 - 10_000_000
        elif taxable <= 1_000_000_000:        # 10억 이하: 30% (누진공제 6천만)
            return taxable * 0.30 - 60_000_000
        elif taxable <= 3_000_000_000:        # 30억 이하: 40% (누진공제 1.6억)
            return taxable * 0.40 - 160_000_000
        else:                                  # 30억 초과: 50% (누진공제 4.6억)
            return taxable * 0.50 - 460_000_000

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_gift_tax",
                "description": (
                    "증여세를 정확히 계산합니다. "
                    "증여재산공제·혼인출산공제·세대생략 할증을 자동 적용합니다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "gift_amount": {
                            "type": "number",
                            "description": "금번 증여 금액 (원)",
                        },
                        "donee_type": {
                            "type": "string",
                            "enum": ["배우자", "직계존비속_성년", "직계존비속_미성년", "기타친족"],
                            "description": "수증자 관계",
                        },
                        "prior_gifts_10yr": {
                            "type": "number",
                            "description": "최근 10년간 동일 수증자에게 기증여한 금액 합계 (원, 없으면 0)",
                        },
                        "is_generation_skip": {
                            "type": "boolean",
                            "description": "세대생략 여부 (수증자가 손자·증손자 등인 경우 True)",
                        },
                        "marriage_birth_used": {
                            "type": "number",
                            "description": "혼인·출산공제 기사용액 (원, 없으면 0). 합산 최대 1억.",
                        },
                        "apply_marriage_birth": {
                            "type": "boolean",
                            "description": "혼인·출산공제 추가 적용 여부",
                        },
                    },
                    "required": ["gift_amount", "donee_type"],
                },
            },
            {
                "name": "optimize_gift_split",
                "description": (
                    "증여액을 수증자·시기별로 분산하여 총 증여세를 최소화하는 "
                    "최적 플랜을 시뮬레이션합니다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "total_gift_target": {
                            "type": "number",
                            "description": "총 증여 목표 금액 (원)",
                        },
                        "donees": {
                            "type": "array",
                            "description": "수증자 목록",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name":           {"type": "string"},
                                    "type":           {"type": "string",
                                                       "enum": ["배우자", "직계존비속_성년",
                                                                "직계존비속_미성년", "기타친족"]},
                                    "prior_10yr":     {"type": "number"},
                                    "is_gen_skip":    {"type": "boolean"},
                                },
                                "required": ["name", "type"],
                            },
                        },
                        "years":  {"type": "integer", "description": "분산 기간 (년, 최대 30)"},
                    },
                    "required": ["total_gift_target", "donees"],
                },
            },
            {
                "name": "compare_gift_assets",
                "description": (
                    "금전·비상장주식·부동산 세 가지 자산유형별 증여세 부담을 비교합니다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "market_value": {
                            "type": "number",
                            "description": "자산 시가 (원)",
                        },
                        "stock_book_value": {
                            "type": "number",
                            "description": "비상장주식 보충적 평가액 (원, 시가 없는 경우)",
                        },
                        "real_estate_standard": {
                            "type": "number",
                            "description": "부동산 기준시가 (원)",
                        },
                        "donee_type": {
                            "type": "string",
                            "enum": ["배우자", "직계존비속_성년", "직계존비속_미성년", "기타친족"],
                        },
                        "prior_gifts_10yr": {"type": "number"},
                    },
                    "required": ["market_value", "donee_type"],
                },
            },
        ]

    # ── 툴 핸들러 ──────────────────────────────────────────────────────────

    def handle_tool(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "calc_gift_tax":
            return self._calc_gift_tax_tool(**tool_input)
        if tool_name == "optimize_gift_split":
            return self._optimize_gift_split(**tool_input)
        if tool_name == "compare_gift_assets":
            return self._compare_gift_assets(**tool_input)
        return {"error": f"알 수 없는 툴: {tool_name}"}

    # ── 핵심 계산 로직 ────────────────────────────────────────────────────

    def _calc_gift_tax_tool(
        self,
        gift_amount: float,
        donee_type: str,
        prior_gifts_10yr: float = 0,
        is_generation_skip: bool = False,
        marriage_birth_used: float = 0,
        apply_marriage_birth: bool = False,
    ) -> dict:
        """증여세 정밀 계산."""
        base_deduction = self.DEDUCTIONS.get(donee_type, 10_000_000)

        # 10년 합산 잔여 공제액
        remaining_deduction = max(base_deduction - prior_gifts_10yr, 0)

        # 혼인·출산공제 (합산 최대 1억)
        mb_deduction = 0
        if apply_marriage_birth:
            mb_deduction = max(
                min(self.MARRIAGE_BIRTH_DEDUCTION - marriage_birth_used,
                    self.MARRIAGE_BIRTH_DEDUCTION),
                0
            )

        total_deduction = remaining_deduction + mb_deduction

        # 과세표준 = 금번 증여 + 기증여 합산 - 총공제
        cumulative = gift_amount + prior_gifts_10yr
        taxable = max(cumulative - base_deduction - mb_deduction, 0)

        # 이미 납부한 세액 차감 (합산 과세 시 기납부세액 공제)
        prior_taxable = max(prior_gifts_10yr - base_deduction, 0)
        prior_tax = self._calc_gift_tax(prior_taxable)

        gross_tax = self._calc_gift_tax(taxable)
        net_tax   = max(gross_tax - prior_tax, 0)

        # 세대생략 할증 (상증세법 §57: 30%)
        surcharge = net_tax * 0.30 if is_generation_skip else 0
        final_tax = net_tax + surcharge

        # 신고세액공제 3% (기한 내 신고 시)
        filing_discount = final_tax * 0.03
        tax_after_discount = final_tax - filing_discount

        return {
            "증여금액(원)":            round(gift_amount),
            "수증자_관계":             donee_type,
            "기본_증여재산공제(원)":    round(base_deduction),
            "10년_기증여액(원)":        round(prior_gifts_10yr),
            "잔여_공제액(원)":          round(remaining_deduction),
            "혼인출산공제(원)":         round(mb_deduction),
            "과세표준(원)":             round(taxable),
            "산출세액(원)":             round(gross_tax),
            "기납부세액_차감(원)":      round(prior_tax),
            "차감_납부세액(원)":        round(net_tax),
            "세대생략_할증(30%)(원)":   round(surcharge),
            "최종_결정세액(원)":        round(final_tax),
            "신고세액공제_3%(원)":      round(filing_discount),
            "기한내신고_납부세액(원)":  round(tax_after_discount),
            "실효세율(%)":              round(tax_after_discount / gift_amount * 100, 2) if gift_amount else 0,
            "근거_법령":               "상증세법 §53(증여재산공제) §53의2(혼인출산공제) §56(세율) §57(세대생략)",
        }

    def _optimize_gift_split(
        self,
        total_gift_target: float,
        donees: list[dict],
        years: int = 10,
    ) -> dict:
        """수증자·기간 분산 최적화 플랜."""
        years = min(max(years, 1), 30)
        plans = []
        total_tax = 0.0
        total_deduction = 0.0

        for d in donees:
            dtype = d.get("type", "직계존비속_성년")
            prior = d.get("prior_10yr", 0)
            gen_skip = d.get("is_gen_skip", False)

            base_ded = self.DEDUCTIONS.get(dtype, 10_000_000)
            remaining = max(base_ded - prior, 0)

            # 10년 주기 반복 횟수
            cycles = max(years // 10, 1)
            # 1회당 배정 금액 = 잔여공제를 최대한 활용
            per_cycle = remaining  # 공제 한도 내 무세 증여

            taxable_amt  = max(total_gift_target / len(donees) - per_cycle * cycles, 0)
            cycle_tax    = self._calc_gift_tax(taxable_amt)
            if gen_skip:
                cycle_tax *= 1.30

            plans.append({
                "수증자":            d.get("name", dtype),
                "관계":              dtype,
                "세대생략":          gen_skip,
                "10년_공제_잔액(원)": round(remaining),
                "무세_증여가능(원)":  round(per_cycle * cycles),
                "배정_증여금액(원)":  round(total_gift_target / len(donees)),
                "예상_증여세(원)":   round(cycle_tax),
            })
            total_tax += cycle_tax
            total_deduction += remaining

        return {
            "총_증여목표(원)":       round(total_gift_target),
            "분산_기간(년)":         years,
            "수증자_수":             len(donees),
            "수증자별_플랜":         plans,
            "총_예상증여세(원)":     round(total_tax),
            "총_활용공제액(원)":     round(total_deduction),
            "절세_효과(원)":         round(total_deduction * 0.10),  # 최소 10% 기준
            "전략_요약": (
                f"{len(donees)}명 수증자·{years}년 분산 시 총 증여세 {total_tax:,.0f}원. "
                f"공제 잔액 {total_deduction:,.0f}원을 무세 구간으로 활용."
            ),
        }

    def _compare_gift_assets(
        self,
        market_value: float,
        donee_type: str,
        prior_gifts_10yr: float = 0,
        stock_book_value: float = 0,
        real_estate_standard: float = 0,
    ) -> dict:
        """자산유형별 증여세 비교."""
        # 평가액 결정
        cash_val   = market_value
        stock_val  = stock_book_value if stock_book_value else market_value * 0.70  # 비상장 할인 가정
        re_val     = real_estate_standard if real_estate_standard else market_value * 0.65

        results = {}
        for label, val in [("금전", cash_val), ("비상장주식(보충적평가)", stock_val), ("부동산(기준시가)", re_val)]:
            r = self._calc_gift_tax_tool(
                gift_amount=val,
                donee_type=donee_type,
                prior_gifts_10yr=prior_gifts_10yr,
            )
            results[label] = {
                "증여평가액(원)":        round(val),
                "증여세(원)":           r["기한내신고_납부세액(원)"],
                "실효세율(%)":          r["실효세율(%)"],
                "시가_대비_평가율(%)":   round(val / market_value * 100, 1) if market_value else 0,
            }

        best = min(results, key=lambda k: results[k]["증여세(원)"])
        return {
            "자산유형별_비교":  results,
            "최적_증여자산":   best,
            "절세금액(원)":    round(
                max(v["증여세(원)"] for v in results.values()) -
                min(v["증여세(원)"] for v in results.values())
            ),
            "주의사항": (
                "비상장주식 평가는 보충적 평가액(순손익·순자산 가중평균) 기준. "
                "부동산은 시가 확인 후 보충적으로 기준시가 적용(상증세법 §60)."
            ),
        }

    # ── 공개 인터페이스 ────────────────────────────────────────────────────

    def analyze(self, company_data: dict) -> str:
        """COMPANY_DATA 기반 증여세 분석 쿼리 자동 생성."""
        n        = company_data.get("company_name", "대상법인")
        ceo_age  = company_data.get("ceo_age", 55)
        bv       = company_data.get("business_value", 0)
        nas      = company_data.get("net_asset_per_share", 0)
        children = company_data.get("children_count", 2)
        te       = company_data.get("total_equity", 0)

        query = (
            f"[분석 대상] {n} | 대표 {ceo_age}세 | 자녀 {children}명\n"
            f"[주식 현황] 기업가치 {bv:,.0f}원 | 1주당 평가액 {nas:,.0f}원 | 자기자본 {te:,.0f}원\n\n"
            f"① 성년 자녀 {children}명에게 비상장주식 분산 증여 시 최적 증여 계획 수립\n"
            f"② 10년 합산 공제(1인당 5천만) 활용 무세 구간 최대화 전략\n"
            f"③ 혼인·출산공제(+1억) 활용 타이밍 분석\n"
            f"④ 세대생략 증여(손자녀) 유불리 비교 — 할증 30% vs 절세 효과\n"
            f"⑤ 금전·비상장주식·부동산 자산유형별 증여세 비교 및 최적 자산 추천"
        )
        return self.run(query, reset=True)
