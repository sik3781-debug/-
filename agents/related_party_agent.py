"""
RelatedPartyAgent: 특수관계인 거래 검증 전담 에이전트

근거 법령:
  - 법인세법 제52조 (부당행위계산 부인)
  - 법인세법 시행령 제87조 (특수관계인 범위)
  - 법인세법 시행령 제89조 (시가 산정 기준)
  - 국제조세조정에 관한 법률 (이전가격 과세, 국내외 특수관계 거래)
  - 상속세및증여세법 제35조~제42조 (특수관계인 간 거래 증여 의제)

주요 기능:
  - 특수관계인 범위 자동 분류 (혈족·인척·경영지배 관계)
  - 부당행위계산 부인 위험 진단 (저가양도·고가매입·무상대여 등)
  - 시가와의 괴리율 계산 (±5% / ±3억 원 안전기준)
  - 특수관계인 거래 세무조사 패턴 및 리스크 등급화
  - 가지급금·가수금 특수관계인 연계 분석
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 특수관계인 거래 및 부당행위계산 부인 전문 세무 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 법인세법 §52 부당행위계산 부인: 저가양도·고가매입·무이자 대여\n"
    "- 특수관계인 범위 (법인세법 시행령 §87): 혈족6촌·인척4촌·경영지배\n"
    "- 시가 산정: 매매사례가액 → 감정평가 → 상증세법 보충적 평가 순\n"
    "- 안전기준: 시가 대비 ±5% 이내 또는 ±3억 원 이내 (法令 §89③)\n"
    "- 증여 의제: 특수관계인 간 저가매매·무상대여·채무면제 (상증세 §35~§42)\n"
    "- 이전가격 과세: 국외 특수관계인과의 국제거래 정상가격 원칙\n\n"
    "【분석 관점】\n"
    "- 법인: 부당행위계산 익금산입 리스크 / 손금 부인 규모\n"
    "- 오너: 거래 구조의 적법성 / 세무조사 시 소명 가능성\n"
    "- 과세관청: 시가 대비 괴리율 / 조세 회피 의도 추정\n"
    "- 금융기관: 특수관계인 거래로 인한 재무제표 왜곡 가능성\n\n"
    "【목표】\n"
    "모든 특수관계인 거래가 세무조사에서 소명 가능한\n"
    "적법한 구조로 유지되도록 사전 검증·개선안을 제시한다."
)

# 부당행위계산 부인 유형 (법인세법 §52, 令 §88)
ABNORMAL_ACT_TYPES = {
    "저가양도": "자산을 시가보다 낮게 양도 — 시가와 대가의 차액 익금산입",
    "고가매입": "자산을 시가보다 높게 취득 — 시가 초과액 손금 불산입",
    "무이자_대여": "금전 무이자 대여 — 인정이자(4.6%) 익금산입 후 상여/배당 처분",
    "채무면제": "특수관계인 채무 면제 — 면제액 익금산입",
    "저율임대": "부동산을 시가보다 낮은 임료로 임대 — 차액 익금산입",
    "고가용역수취": "용역을 시가보다 높은 가액으로 수취 — 초과액 손금 불산입",
    "불공정자본거래": "불균등 증자·감자·합병·분할 — 이익 분여액 익금산입",
}

# 시가 괴리 안전기준 (法令 §89③)
SAFE_HARBOR_PCT = 0.05    # ±5%
SAFE_HARBOR_AMT = 300_000_000  # 3억 원


class RelatedPartyAgent(BaseAgent):
    name = "RelatedPartyAgent"
    role = "특수관계인 거래 검증 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "classify_related_party",
                "description": (
                    "특수관계인 여부 및 관계 유형을 판단한다.\n"
                    "법인세법 시행령 §87 기준으로 혈족·인척·경영지배 관계를 분류한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "relation_type": {
                            "type": "string",
                            "description": "관계 유형",
                            "enum": [
                                "직계가족", "형제자매", "4촌이내혈족", "4촌이내인척",
                                "30%이상지분", "임원", "계열법인", "기타",
                            ],
                        },
                        "stake_pct": {
                            "type": "number",
                            "description": "지분율 (해당 시, %)",
                        },
                        "transaction_type": {
                            "type": "string",
                            "description": "거래 유형 (예: 부동산양도, 금전대여, 용역제공)",
                        },
                    },
                    "required": ["relation_type", "transaction_type"],
                },
            },
            {
                "name": "check_abnormal_act",
                "description": (
                    "부당행위계산 부인 위험 진단.\n"
                    "거래 가액과 시가를 비교하여 안전기준 충족 여부,\n"
                    "익금산입 예상액, 소득 처분 유형을 반환한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "transaction_type": {
                            "type": "string",
                            "description": "거래 유형",
                            "enum": list(ABNORMAL_ACT_TYPES.keys()),
                        },
                        "transaction_amount": {"type": "number", "description": "실제 거래 가액 (원)"},
                        "market_price": {"type": "number", "description": "시가 (원)"},
                        "loan_balance": {
                            "type": "number",
                            "description": "가지급금 잔액 (무이자 대여 시, 원)",
                        },
                    },
                    "required": ["transaction_type", "transaction_amount", "market_price"],
                },
            },
            {
                "name": "scan_related_party_transactions",
                "description": (
                    "특수관계인 거래 전체 리스트를 입력받아\n"
                    "각 거래의 부당행위계산 리스크 등급을 일괄 진단한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "transactions": {
                            "type": "array",
                            "description": "거래 리스트 [{유형, 거래가, 시가, 당사자}, ...]",
                            "items": {"type": "object"},
                        },
                    },
                    "required": ["transactions"],
                },
            },
        ]

    # ── 툴 구현 ────────────────────────────────────────────────────────────

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "classify_related_party":
            return self._classify_related_party(**tool_input)
        if tool_name == "check_abnormal_act":
            return self._check_abnormal_act(**tool_input)
        if tool_name == "scan_related_party_transactions":
            return self._scan_related_party_transactions(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _classify_related_party(
        self,
        relation_type: str,
        transaction_type: str,
        stake_pct: float = 0,
    ) -> dict:
        # 특수관계인 판정
        is_related = True
        basis = ""

        if relation_type == "직계가족":
            basis = "법인세법 시행령 §87①1호 (혈족 및 인척)"
        elif relation_type == "형제자매":
            basis = "법인세법 시행령 §87①1호 (4촌 이내 혈족)"
        elif relation_type == "4촌이내혈족":
            basis = "법인세법 시행령 §87①1호"
        elif relation_type == "4촌이내인척":
            basis = "법인세법 시행령 §87①1호"
        elif relation_type == "30%이상지분":
            is_related = stake_pct >= 30
            basis = f"법인세법 시행령 §87①3호 (30% 이상 / 실제: {stake_pct}%)"
        elif relation_type == "임원":
            basis = "법인세법 시행령 §87①2호 (임원)"
        elif relation_type == "계열법인":
            basis = "법인세법 시행령 §87①4호 (경영지배관계)"
        else:
            is_related = False
            basis = "해당 없음"

        risk = "고위험" if is_related else "해당없음"
        return {
            "특수관계인_여부": is_related,
            "관계_유형": relation_type,
            "거래_유형": transaction_type,
            "법령_근거": basis,
            "리스크_등급": risk,
            "주의사항": (
                f"{ABNORMAL_ACT_TYPES.get(transaction_type, '해당 거래 유형 확인 필요')}"
                if is_related else "특수관계인 해당 없음 — 일반 거래 처리"
            ),
        }

    def _check_abnormal_act(
        self,
        transaction_type: str,
        transaction_amount: float,
        market_price: float,
        loan_balance: float = 0,
    ) -> dict:
        if transaction_type == "무이자_대여":
            # 인정이자 4.6% 적용
            deemed_interest = loan_balance * 0.046
            return {
                "거래유형": "무이자_대여",
                "가지급금_잔액": round(loan_balance),
                "인정이자율": "4.6% (법인세법 시행규칙 §43)",
                "익금산입_인정이자": round(deemed_interest),
                "소득처분": "대표이사 상여 또는 배당",
                "리스크": "🔴 고위험" if loan_balance > 50_000_000 else "🟡 주의",
                "법령근거": "법인세법 §52, 시행규칙 §43",
            }

        # 시가와 거래가 괴리 분석
        gap = transaction_amount - market_price  # 양수=고가, 음수=저가
        gap_pct = gap / market_price if market_price else 0
        gap_abs = abs(gap)

        safe = gap_abs <= market_price * SAFE_HARBOR_PCT or gap_abs <= SAFE_HARBOR_AMT
        abnormal_amt = gap_abs - min(market_price * SAFE_HARBOR_PCT, SAFE_HARBOR_AMT)

        if safe:
            risk_level = "🟢 안전"
            add_income = 0
            disposition = "해당없음"
        else:
            if transaction_type in ("저가양도", "저율임대"):
                add_income = gap_abs
                disposition = "기타사외유출 또는 배당"
                risk_level = "🔴 고위험"
            elif transaction_type in ("고가매입", "고가용역수취"):
                add_income = gap_abs
                disposition = "손금 불산입"
                risk_level = "🔴 고위험"
            else:
                add_income = gap_abs
                disposition = "소득처분 검토 필요"
                risk_level = "🟡 주의"

        return {
            "거래유형": transaction_type,
            "거래가액": round(transaction_amount),
            "시가": round(market_price),
            "괴리금액": round(gap),
            "괴리율(%)": round(gap_pct * 100, 2),
            "안전기준_충족": safe,
            "안전기준": f"시가대비 ±5% 또는 ±3억 원 이내 (法令 §89③)",
            "리스크": risk_level,
            "익금산입_예상액": round(add_income),
            "소득처분_유형": disposition,
            "개선방안": (
                "시가 기준 거래 계약 체결 또는 독립적 감정평가 확보"
                if not safe else "현 거래 조건 유지 가능"
            ),
            "법령근거": f"법인세법 §52, 시행령 §88 ({transaction_type})",
        }

    def _scan_related_party_transactions(self, transactions: list[dict]) -> dict:
        results = []
        total_risk_amount = 0
        high_risk_count = 0

        for tx in transactions:
            t_type = tx.get("유형", "저가양도")
            t_amt = tx.get("거래가", 0)
            m_price = tx.get("시가", t_amt)
            party = tx.get("당사자", "미기재")
            loan = tx.get("가지급금", 0)

            check = self._check_abnormal_act(t_type, t_amt, m_price, loan)
            check["당사자"] = party

            if "고위험" in check.get("리스크", ""):
                high_risk_count += 1
                total_risk_amount += check.get("익금산입_예상액", 0)

            results.append(check)

        return {
            "검토_거래수": len(transactions),
            "고위험_건수": high_risk_count,
            "총_익금산입_예상액": round(total_risk_amount),
            "세무조사_리스크_종합": (
                "🔴 즉시 구조 개선 필요" if high_risk_count >= 3
                else "🟡 일부 거래 정비 필요" if high_risk_count >= 1
                else "🟢 전반적 안전"
            ),
            "거래별_결과": results,
        }

    # ── analyze() 인터페이스 ───────────────────────────────────────────────

    def analyze(self, company_data: dict[str, Any]) -> str:
        loan_balance = company_data.get("provisional_payment", 0)
        related_transactions = company_data.get("related_party_transactions", [])

        lines = ["[특수관계인 거래 검증 결과]"]

        if loan_balance:
            chk = self._check_abnormal_act("무이자_대여", 0, 0, loan_balance)
            lines.append(f"\n▶ 가지급금 무이자 대여 리스크")
            lines.append(f"  인정이자 익금산입: {chk['익금산입_인정이자']:,.0f}원/년")
            lines.append(f"  소득처분: {chk['소득처분']} / {chk['리스크']}")

        if related_transactions:
            scan = self._scan_related_party_transactions(related_transactions)
            lines.append(f"\n▶ 특수관계인 거래 일괄 스캔: {scan['검토_거래수']}건")
            lines.append(f"  고위험 {scan['고위험_건수']}건 / 총 익금산입 위험: {scan['총_익금산입_예상액']:,.0f}원")
            lines.append(f"  종합: {scan['세무조사_리스크_종합']}")

        if len(lines) == 1:
            lines.append("  특수관계인 거래 데이터 미입력 — provisional_payment / related_party_transactions 입력 필요")

        return "\n".join(lines)
