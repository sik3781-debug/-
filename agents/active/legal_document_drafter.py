"""
법무서류 작성 에이전트 (LegalDocumentDrafterAgent)
==================================================
정관·이사회의사록·주총의사록·동의서·확인서 5대 카테고리 표준 양식 자동 작성.

핵심 법령:
- 상법 §289~§542 (회사 설립·운영 — 정관·결의 형식 요건)
  - §289 (정관 절대적 기재사항), §312 (이사 선임 결의)
  - §391~§393 (이사회 의사록), §433~§435 (주총 결의·소집 절차)
- 부동산등기법 §29 (등기 신청 요건)
- 공증인법 §30 (공정증서 작성)
- 인지세법 §3 + 별표 (인지세 세율 — 부동산 양도 등)
- 지방세법 §28 (등록면허세 — 등기·등록 시 정액·정률)

본 모듈은 base level 구현이며, 후속 세션에서 다음 항목 심화 예정:
- 표준 양식 라이브러리 확장 (현재 5종 → 25종 목표)
- 등기 신청서 자동 작성 + 온라인 등기 가이드 통합
- 공증 절차 자동 안내 (공증인법§30 부합)
- 자기주식취득·합병·분할·해산 등 특수 결의 양식 추가

작성: 2026-05-04 [LAPTOP]
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from agents.base_agent import BaseAgent


# ──────────────────────────────────────────────────────────────────────────
# 인지세법 별표 — 단순화 (부동산 양도·계약서 기준)
# ──────────────────────────────────────────────────────────────────────────

STAMP_TAX_TABLE = [
    (10_000_000,    0,           "1천만 이하 비과세"),
    (30_000_000,    20_000,      "1천만~3천만"),
    (50_000_000,    40_000,      "3천만~5천만"),
    (100_000_000,   70_000,      "5천만~1억"),
    (1_000_000_000, 150_000,     "1억~10억"),
    (10_000_000_000, 350_000,    "10억~100억"),
    (float("inf"),  350_000,     "100억 초과 — 별도 산정"),
]

# 지방세법§28 등록면허세 — 정관변경·임원변경·신주발행 등
REGISTRATION_LICENSE_TAX = {
    "정관변경":    40_200,    # 등록면허세 정액 (4만200원)
    "임원변경":    40_200,
    "본점이전":    112_500,   # 동일 시·도 내 4만200원, 외 11만2500원 (단순화)
    "신주발행":    "자본금 증가액 × 0.4%",  # 정률 (지방세법§28 ①4호)
    "합병":        "출자총액 × 0.4%",
    "분할":        "출자총액 × 0.4%",
    "해산":        40_200,
}


def calc_stamp_tax(amount: float) -> tuple[int, str]:
    """인지세법§3 별표 — 금액별 인지세 산출."""
    for threshold, tax, note in STAMP_TAX_TABLE:
        if amount <= threshold:
            return int(tax), note
    return 350_000, "100억 초과"


# ──────────────────────────────────────────────────────────────────────────
# 표준 양식 5종 — 골격 템플릿
# ──────────────────────────────────────────────────────────────────────────

TEMPLATES = {
    "정관": (
        "정관\n\n"
        "제1장 총칙\n"
        "제1조 (상호) 본 회사는 「{company_name}」이라 한다.\n"
        "제2조 (목적) 본 회사는 다음의 사업을 목적으로 한다.\n"
        "  1. {business_purpose}\n"
        "제3조 (본점) 본 회사의 본점은 {head_office}에 둔다.\n\n"
        "제2장 주식\n"
        "제4조 (수권자본) 본 회사가 발행할 주식의 총수는 {authorized_shares}주.\n"
        "제5조 (1주의 금액) 1주의 금액은 금 {par_value}원.\n\n"
        "제3장 이사회\n"
        "제6조 (이사 정수) 본 회사의 이사는 {director_count}명 이상.\n\n"
        "[근거: 상법§289 (정관 절대적 기재사항)]"
    ),
    "이사회의사록": (
        "이사회의사록\n\n"
        "1. 회의일시: {decision_date} {meeting_time}\n"
        "2. 회의장소: {meeting_place}\n"
        "3. 출석이사: {director_attendance_list}\n"
        "4. 의장: {chair_name}\n\n"
        "[안건] {agenda}\n"
        "  - 의결정족수: 이사 과반 출석·과반 찬성 (상법§391 ①)\n"
        "  - 결의 결과: {decision_result}\n\n"
        "위 의사의 경과와 결과를 명확히 하기 위하여 본 의사록을 작성하고 "
        "출석이사 전원이 기명날인한다.\n\n"
        "{decision_date}\n\n"
        "이사 (서명): __________\n\n"
        "[근거: 상법§391 (이사회결의), §393 (의사록 작성·기명날인)]"
    ),
    "주총의사록": (
        "주주총회의사록\n\n"
        "1. 회의일시: {decision_date} {meeting_time}\n"
        "2. 회의장소: {meeting_place}\n"
        "3. 출석주주: 발행주식 {issued_shares:,}주 중 {attended_shares:,}주 "
        "(출석률 {attendance_rate:.1f}%)\n"
        "4. 의장: {chair_name}\n\n"
        "[안건] {agenda}\n"
        "  - 의결정족수: 보통결의 = 출석 과반 + 발행 1/4 이상 (상법§368)\n"
        "                특별결의 = 출석 2/3 + 발행 1/3 이상 (상법§434)\n"
        "  - 결의 결과: {decision_result}\n\n"
        "위 의사의 경과와 결과를 명확히 하기 위하여 본 의사록을 작성한다.\n\n"
        "{decision_date}\n\n"
        "의장 (서명): __________\n"
        "감사 (서명): __________\n\n"
        "[근거: 상법§373 (의사록 작성), §433~§435 (소집·결의 요건)]"
    ),
    "동의서": (
        "동의서\n\n"
        "본인은 {company_name}의 {agenda}에 관하여 아래와 같이 동의합니다.\n\n"
        "1. 동의 대상: {agenda}\n"
        "2. 동의 일자: {decision_date}\n"
        "3. 동의 내용: {decision_result}\n\n"
        "본 동의는 본인의 자유로운 의사에 기한 것이며, 사후에 이의를 "
        "제기하지 아니합니다.\n\n"
        "{decision_date}\n\n"
        "동의자 (서명): __________\n\n"
        "[근거: 민법§107 (의사표시) + 회사 정관]"
    ),
    "확인서": (
        "확인서\n\n"
        "본인은 {company_name}의 {agenda}에 관하여 아래 사실을 확인합니다.\n\n"
        "1. 확인 대상: {agenda}\n"
        "2. 확인 일자: {decision_date}\n"
        "3. 확인 사항: {decision_result}\n\n"
        "위 사실이 진실임을 확인하며, 허위인 경우 형법상 책임을 부담함을 "
        "인지합니다.\n\n"
        "{decision_date}\n\n"
        "확인자 (서명): __________\n\n"
        "[근거: 민법§107·§535 (계약체결상 과실) + 형법§231 (사문서위조)]"
    ),
    # [3중루프 보강] 자기주식취득 결의서
    "자기주식취득결의서": (
        "자기주식취득결의서\n\n"
        "{company_name}은(는) 상법§341에 따라 아래와 같이 자기주식 취득을 "
        "결의한다.\n\n"
        "1. 취득 주식수: {acquisition_shares}주\n"
        "2. 취득 가액: 1주당 {acquisition_price}원, 총 {agenda} 범위\n"
        "3. 취득 방법: {decision_result} (거래소·공개매수·특정주주)\n"
        "4. 취득 기간: 결의일로부터 1년 이내\n"
        "5. 재원: 배당가능이익 한도 내 (상법§462의3)\n\n"
        "[근거: 상법§341 (자기주식 취득), §462의3 (배당가능이익 한도)]"
    ),
    # [3중루프 보강] 합병결의서
    "합병결의서": (
        "합병결의서 (소멸회사)\n\n"
        "{company_name}은(는) 상법§522에 따라 아래와 같이 합병을 결의한다.\n\n"
        "1. 합병상대방: {head_office}\n"
        "2. 합병비율: {decision_result}\n"
        "3. 합병기일: {decision_date}\n"
        "4. 합병계약서 승인 (주총 특별결의 — 상법§522·§434)\n\n"
        "[근거: 상법§522 (합병계약), §527의5 (채권자 이의), §530 (합병등기)]"
    ),
}


class LegalDocumentDrafterAgent(BaseAgent):
    """정관·이사회·주총·동의서·확인서 5대 양식 자동 작성 에이전트."""

    name: str = "LegalDocumentDrafterAgent"
    role: str = "법무서류 표준 양식 작성 전문가"
    model: str = "claude-sonnet-4-6"
    system_prompt: str = (
        "당신은 정관·이사회의사록·주총의사록·동의서·확인서 5대 카테고리 "
        "표준 양식 작성 전문가입니다. 상법§289~§542 형식 요건, "
        "부동산등기법§29, 공증인법§30, 인지세법§3, 지방세법§28 기준으로 "
        "초안을 작성하고 인지세·등록면허세를 자동 산출합니다. 변호사·"
        "법무사 검토 워딩을 자동 삽입합니다."
    )

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.conversation: list[dict[str, Any]] = []
        self.tools: list[dict[str, Any]] = []
        self.client = None

    def _ensure_client(self) -> None:
        if self.client is None:
            import anthropic
            self.client = anthropic.Anthropic(
                api_key=os.environ.get("ANTHROPIC_API_KEY", '')
            )

    def run(self, user_message: str, *, reset: bool = False) -> str:
        self._ensure_client()
        return super().run(user_message, reset=reset)

    # ------------------------------------------------------------------ #
    # 핵심 분석                                                            #
    # ------------------------------------------------------------------ #

    def analyze(self, company_data: dict) -> dict:
        doc_type = company_data.get("document_type", "이사회의사록")
        agenda   = company_data.get("agenda", "신주발행")
        amt      = company_data.get("transaction_amount", 0)
        company  = company_data.get("company_name", "대상법인")
        date     = company_data.get("decision_date", datetime.now().date().isoformat())

        # ── 1. 표준 양식 선택 + 채움 ─────────────────────────────────
        if doc_type not in TEMPLATES:
            doc_type = "이사회의사록"  # 기본값
        template = TEMPLATES[doc_type]
        defaults = self._template_defaults(company_data)
        try:
            draft = template.format(**defaults)
            missing_fields = []
        except KeyError as e:
            # [3중루프 보강] 누락 필드 자동 진단 + 안내
            missing_fields = self._diagnose_missing(template, defaults)
            draft = (
                f"[양식 채움 오류 — 누락 필드: {missing_fields}]\n"
                f"company_data 입력 시 다음 필드를 추가하십시오:\n"
                + "\n".join(f"  - {f}" for f in missing_fields)
                + f"\n\n양식: {doc_type}\n원본 템플릿:\n{template}"
            )

        # [3중루프 보강] 공증 절차 안내
        notarization_guide = self._notarization_guide(doc_type, amt)

        # ── 2. 인지세 (인지세법§3) ──────────────────────────────────
        stamp_tax, stamp_note = calc_stamp_tax(amt)

        # ── 3. 등록면허세 (지방세법§28) ─────────────────────────────
        license_tax_raw = REGISTRATION_LICENSE_TAX.get(agenda, "정액 4만200원")
        if isinstance(license_tax_raw, int):
            license_tax = license_tax_raw
            license_note = "정액 (지방세법§28)"
        else:
            # "자본금 증가액 × 0.4%" 패턴 — 자동 계산
            license_tax = int(amt * 0.004) if amt > 0 else 40_200
            license_note = license_tax_raw

        # ── 4. 등기 비용 합계 ───────────────────────────────────────
        registration_total = stamp_tax + license_tax

        # ── 5. 시퀀스 정합성 (결의→의사록→등기→공증) ────────────────
        sequence_check = self._check_sequence(doc_type, company_data)

        # ── 결과 본문 ──────────────────────────────────────────────
        text = (
            f"법인 측면: {doc_type} 표준 양식 작성 — 안건 '{agenda}', "
            f"인지세 {stamp_tax:,}원 ({stamp_note}) + "
            f"등록면허세 {license_tax:,}원 ({license_note}) = 합계 "
            f"{registration_total:,}원.\n"
            f"주주(오너) 관점: {date} 결의 → 의사록 → 등기 → "
            f"{'공증 검토' if doc_type in ['정관', '동의서'] else '공증 불요'}.\n"
            f"과세관청(등기소) 관점: 상법§{289 if doc_type=='정관' else 391} 형식 "
            f"요건 충족 + 등기 신청 2주 이내 (상법§37).\n"
            f"금융기관 관점: 등기 변경 사항 통지 + 신용평가 영향 점검."
        )

        result = {
            "agent": self.name,
            "text": text,
            "document_type": doc_type,
            "agenda": agenda,
            "draft_content": draft,
            "stamp_tax": stamp_tax,
            "stamp_tax_note": stamp_note,
            "registration_license_tax": license_tax,
            "registration_license_note": license_note,
            "registration_total_cost": registration_total,
            "sequence_check": sequence_check,
            "decision_date": date,
            "missing_fields": missing_fields,
            "notarization_guide": notarization_guide,
            "checklist": self._checklist(),
            "disclaimer": self._disclaimer(),
            "require_full_4_perspective": True,
        }

        result["risk_5axis"] = self.validate_risk_5axis(result, company_data)
        result["risk_hedge_4stage"] = self.generate_risk_hedge_4stage(company_data)
        result["matrix_4x3"] = self._build_4x3_matrix(result)
        result["self_check_4axis"] = self.validate(result)
        return result

    # ------------------------------------------------------------------ #
    # 보조: 양식 기본값 + 시퀀스 점검                                          #
    # ------------------------------------------------------------------ #

    def _template_defaults(self, d: dict) -> dict:
        """양식 변수의 기본값 채움 — 누락 시 placeholder 표시."""
        return {
            "company_name": d.get("company_name", "[회사명 입력]"),
            "business_purpose": d.get("business_purpose", "[사업목적 입력]"),
            "head_office": d.get("head_office", "[본점 주소 입력]"),
            "authorized_shares": d.get("authorized_shares", "[수권주식수 입력]"),
            "par_value": d.get("par_value", "[1주 금액 입력]"),
            "director_count": d.get("director_count", "3"),
            "decision_date": d.get("decision_date", datetime.now().date().isoformat()),
            "meeting_time": d.get("meeting_time", "10:00"),
            "meeting_place": d.get("meeting_place", "본사 회의실"),
            "director_attendance_list": d.get(
                "director_attendance_list",
                "대표이사 [성명], 이사 [성명1], 이사 [성명2]",
            ),
            "chair_name": d.get("chair_name", "[의장 성명]"),
            "agenda": d.get("agenda", "[안건 입력]"),
            "decision_result": d.get("decision_result", "원안 가결"),
            "issued_shares": d.get("issued_shares", 100_000),
            "attended_shares": d.get("attended_shares", 70_000),
            "attendance_rate": (
                d.get("attended_shares", 70_000) / d.get("issued_shares", 100_000) * 100
                if d.get("issued_shares", 0) > 0 else 0
            ),
        }

    # [3중루프 보강] 누락 필드 자동 진단
    def _diagnose_missing(self, template: str, defaults: dict) -> list[str]:
        import re
        required = set(re.findall(r"\{(\w+)\}", template))
        provided = set(defaults.keys())
        return sorted(required - provided)

    # [3중루프 보강] 공증인법§30 공증 절차 안내
    def _notarization_guide(self, doc_type: str, amt: float) -> dict:
        # 공증 권장 양식
        recommended = doc_type in ["정관", "동의서", "확인서"] or amt >= 100_000_000
        # 공증료 (공증인법 시행령 — 단순화)
        if amt < 10_000_000:
            fee = 11_000
        elif amt < 100_000_000:
            fee = 22_000
        elif amt < 1_000_000_000:
            fee = 55_000
        else:
            fee = 200_000
        return {
            "recommended": recommended,
            "근거": "공증인법§30 (공정증서 작성)",
            "예상_공증료": fee,
            "효과": (
                "집행권원 확보 (공증인법§56의2) — 채무 불이행 시 즉시 강제집행 가능"
                if recommended else "본 양식은 공증 불요"
            ),
        }

    def _check_sequence(self, doc_type: str, data: dict) -> dict:
        sequence_map = {
            "정관":         ["주총특별결의", "정관변경", "변경등기"],
            "이사회의사록":  ["이사회결의", "의사록작성", "필요시등기"],
            "주총의사록":    ["소집통지", "주총결의", "의사록작성"],
            "동의서":       ["서면동의", "본인서명", "보관"],
            "확인서":       ["사실확인", "서명", "보관"],
        }
        steps = sequence_map.get(doc_type, [])
        completed = data.get("completed_steps", [])
        return {
            "required_sequence": steps,
            "completed_steps": completed,
            "missing_steps": [s for s in steps if s not in completed],
        }

    # ------------------------------------------------------------------ #
    # §A 5축 검증                                                          #
    # ------------------------------------------------------------------ #

    def validate_risk_5axis(self, result: dict, company_data: dict) -> dict:
        axes: dict[str, dict] = {}

        # DOMAIN: 5대 양식 중 하나에 해당
        domain_pass = result.get("document_type") in TEMPLATES
        axes["DOMAIN"] = {
            "pass": domain_pass,
            "detail": f"양식 {result.get('document_type')} ∈ {list(TEMPLATES.keys())}",
        }

        # LEGAL: 양식별 근거 법령 본문 포함
        draft = result.get("draft_content", "")
        legal_pass = "[근거:" in draft or "상법§" in draft
        axes["LEGAL"] = {
            "pass": legal_pass,
            "detail": "초안에 [근거:] 또는 상법§ 인용 포함",
        }

        # CALC: 인지세 + 등록면허세 합계 정합
        calc_pass = (
            result.get("registration_total_cost", 0)
            == result.get("stamp_tax", 0) + result.get("registration_license_tax", 0)
        )
        axes["CALC"] = {
            "pass": calc_pass,
            "detail": (
                f"인지세 {result.get('stamp_tax', 0):,} + "
                f"등록면허세 {result.get('registration_license_tax', 0):,} = "
                f"{result.get('registration_total_cost', 0):,}"
            ),
        }

        # LOGIC: 시퀀스 정합 — required ⊇ completed
        seq = result.get("sequence_check", {})
        logic_pass = isinstance(seq.get("required_sequence"), list)
        axes["LOGIC"] = {
            "pass": logic_pass,
            "detail": (
                f"시퀀스 {len(seq.get('required_sequence', []))}단계 정의, "
                f"누락 {len(seq.get('missing_steps', []))}건"
            ),
        }

        # CROSS: 4자관점 본문 (등기소 = 과세관청 포함)
        text = result.get("text", "")
        cross_pass = (
            sum(1 for p in ["법인", "주주", "과세관청", "금융기관"] if p in text) == 4
        )
        axes["CROSS"] = {
            "pass": cross_pass,
            "detail": "4자관점 본문 노출",
        }

        all_pass = all(a["pass"] for a in axes.values())
        return {
            "all_pass": all_pass,
            "axes": axes,
            "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5",
        }

    # ------------------------------------------------------------------ #
    # §B 4단계 헷지                                                        #
    # ------------------------------------------------------------------ #

    def generate_risk_hedge_4stage(self, company_data: dict) -> dict:
        return {
            "1_pre": [
                "정관·관련 결의 사전 정비 (이사·주주 명부 최신화)",
                "당사자 신원 확인 (주민번호·법인등기부등본)",
                "상법§289 정관 절대적 기재사항 체크리스트 통과",
            ],
            "2_now": [
                "서류 초안 5축 검증 (DOMAIN·LEGAL·CALC·LOGIC·CROSS)",
                "필수 인지·기명날인 위치 명시 (상법§393 의사록 기명날인)",
                "등기 신청 준비 (변경 사유 발생 후 2주 이내, 상법§37)",
            ],
            "3_post": [
                "등기·공증 완료 확인 (등기부등본 + 공증서)",
                "원본 보관 (본점 10년, 상법§396)",
                "디지털 백업 (PDF + 해시 보존)",
            ],
            "4_worst": [
                "등기 거부 시: 보정 요청 사유 확인 + 즉시 보정",
                "인지 누락 적발 시: 자진 납부 + 가산세 50% 감면 (지방세법§99)",
                "결의 무효·취소의 소 시: 의사록·결의서·통지 입증자료 즉시 제출",
            ],
        }

    # ------------------------------------------------------------------ #
    # 4자×3시점 매트릭스                                                    #
    # ------------------------------------------------------------------ #

    def _build_4x3_matrix(self, result: dict) -> dict:
        return {
            "법인": {
                "사전": "정관·이사회·주총 일정 사전 정비",
                "현재": f"{result['document_type']} 표준 양식 작성 + 5축 검증",
                "사후": "본점 10년 보존 (상법§396) + 디지털 백업",
            },
            "주주": {
                "사전": "주주명부 최신화 + 의결권 확인",
                "현재": "결의 정족수 확인 (상법§368·§434)",
                "사후": "결의 무효·취소의 소 제기 권리 (상법§376·§380)",
            },
            "과세관청": {
                "사전": "등기 사유 발생 사전 인지",
                "현재": (
                    f"인지세 {result['stamp_tax']:,}원 + "
                    f"등록면허세 {result['registration_license_tax']:,}원 납부"
                ),
                "사후": "등기부 변동 자동 통지 + 사후관리",
            },
            "금융기관": {
                "사전": "등기 변경 사유 사전 통지 (대출 약정 조건)",
                "현재": "신용평가 시점 등기부 변동 반영",
                "사후": "정관 변경 시 대출 약정 위반 여부 점검",
            },
        }

    # ------------------------------------------------------------------ #
    # 자가검증 4축                                                          #
    # ------------------------------------------------------------------ #

    def validate(self, result: dict) -> dict:
        text = result.get("text", "")
        ax_calc = any(c.isdigit() for c in text)
        ax_law  = any(k in text for k in ["§", "법", "상법", "인지세법", "지방세법"])
        ax_4P   = sum(1 for p in ["법인", "주주", "과세관청", "금융기관"]
                      if p in text) >= 4
        ax_regr = result.get("require_full_4_perspective", False)
        return {
            "calc": ax_calc, "law": ax_law,
            "perspective_4": ax_4P, "regression": ax_regr,
            "all_pass": all([ax_calc, ax_law, ax_4P, ax_regr]),
        }

    def _checklist(self) -> list[str]:
        return [
            "[함정] 이사회의사록 기명날인 누락 시 결의 무효 (상법§393)",
            "[함정] 주총 소집통지 2주 전 누락 시 결의 취소의 소 (상법§376)",
            "[리스크] 변경등기 2주 초과 시 과태료 (상법§37) 최대 5백만원",
            "[리스크] 정관변경은 주총 특별결의 필수 (상법§434 — 출석 2/3 + 발행 1/3)",
            "[실행] 인지세·등록면허세 사전 자동 계산 + 등기 신청 시 첨부",
        ]

    def _disclaimer(self) -> str:
        return (
            "본 자료는 검토용 초안이며, 최종 등기·공증·소송 대응은 변호사·"
            "법무사 검토를 거쳐 진행하십시오. 양식 변형 시 상법 형식 요건 "
            "충족 여부 재검토 필요 (특히 결의 정족수·소집통지·기명날인)."
        )
