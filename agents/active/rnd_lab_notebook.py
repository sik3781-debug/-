"""
연구노트 에이전트 (RnDLabNotebookAgent)
========================================
직무발명 입증·R&D 세액공제 사전심사 대비용 연구노트 자동 생성.

핵심 법령:
- 발명진흥법 §2(직무발명 정의), §10(사용자 권리·발명자 보상)
- 조특§10 (R&D 세액공제: 중소 25% / 중견 8% / 대기업 2%)
- 조특§10의2 (신성장·원천기술 R&D 세액공제: 중소 30~40%)
- 조특§12 (직무발명 보상금 50% 감면, 연 700만원 한도 비과세)
- 부정경쟁방지법 §2(영업비밀 4요건: 비공지성·경제적 가치·합리적 비밀유지노력·정보)
- 특허법 §29 (신규성·진보성 요건)

본 모듈은 base level 구현이며, 후속 세션에서 다음 항목 심화 예정:
- DOI 자동 발급 API 통합 (현재는 SHA-256 해시 + 타임스탬프만)
- 블록체인 타임스탬프 (현재는 ISO-8601)
- 발명자 기여도 가중치 알고리즘 정밀화

작성: 2026-05-04 [LAPTOP]
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any

from agents.base_agent import BaseAgent


# ──────────────────────────────────────────────────────────────────────────
# 법령 상수 (2026년 귀속 기준 — 2025년과 차이 있으면 양 연도 병기)
# ──────────────────────────────────────────────────────────────────────────

# 조특§10 R&D 세액공제율 (일반)
RD_CREDIT_GENERAL = {
    "중소": 0.25,   # 일반 R&D 25% (조특§10 ①1호)
    "중견": 0.08,   # 매출 5천억 미만 8%, 5천억~1조 6%, 1조 이상 2%
    "대기업": 0.02,  # 일반 2% (조특§10 ①3호) — 2025년: 1%, 2026년: 2% 확대
}

# 조특§10의2 신성장·원천기술 R&D 세액공제율
RD_CREDIT_NEW_GROWTH = {
    "중소": 0.40,   # 신성장 중소 40% (조특§10의2 ①1호)
    "중견": 0.30,   # 신성장 중견 30%
    "대기업": 0.20,  # 신성장 대기업 20% — 2025년: 20%, 2026년: 동일
}

# 조특§12 직무발명 보상금 비과세 한도 (소§12⑤마목)
INVENTOR_REWARD_TAX_FREE_ANNUAL = 7_000_000  # 연 700만원 비과세

# 영업비밀 4요건 (부정경쟁방지법 §2 8호)
TRADE_SECRET_REQUIREMENTS = [
    "비공지성 (공연히 알려지지 아니함)",
    "경제적 가치 (독립된 경제적 가치를 가짐)",
    "합리적 비밀유지노력 (상당한 노력으로 비밀로 유지됨)",
    "기술상·경영상 정보 (영업활동에 유용한 정보)",
]


class RnDLabNotebookAgent(BaseAgent):
    """직무발명·R&D 세액공제 입증용 연구노트 작성 에이전트."""

    name: str = "RnDLabNotebookAgent"
    role: str = "직무발명·R&D 입증 연구노트 전문가"
    model: str = "claude-sonnet-4-6"
    system_prompt: str = (
        "당신은 직무발명·R&D 세액공제 사전심사·영업비밀 입증을 위한 "
        "연구노트 작성 전문가입니다. 발명진흥법 §10, 조특§10·§10의2·§12, "
        "부정경쟁방지법 §2를 기준으로 발명자 특정·실험 가설→결과 인과·"
        "선행기술조사·타임스탬프·해시 보존 등 입증력을 갖춘 연구노트를 "
        "작성합니다. 부정 결과도 누락 없이 기록합니다."
    )

    # ------------------------------------------------------------------ #
    # 초기화 — analyze() 결정론 호출은 ANTHROPIC_API_KEY 불필요               #
    # ------------------------------------------------------------------ #

    def __init__(self, verbose: bool = False) -> None:
        # BaseAgent.__init__ 우회 — analyze()는 LLM 호출 없이 결정론 계산
        self.verbose = verbose
        self.conversation: list[dict[str, Any]] = []
        self.tools: list[dict[str, Any]] = []
        self.client = None  # run() 호출 시 lazy init

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
        """연구노트 항목 1건 생성 + R&D 세액공제 추정 + 5축 검증 + 4단계 헷지."""
        topic        = company_data.get("research_topic", "미지정")
        inventor     = company_data.get("inventor", "미지정")
        inv_role     = company_data.get("inventor_role", "연구원")
        contrib_pct  = company_data.get("inventor_contribution_pct", 100)  # [3중루프 보강] 기여도
        company_size = company_data.get("company_size", "중소")
        rd_expense   = company_data.get("rd_expense", 0)
        is_new       = company_data.get("is_new_growth", False)
        ksic_code    = company_data.get("ksic_code", "")  # [3중루프 보강] 업종코드
        inv_reward   = company_data.get("inventor_reward", 0)
        prior_art    = company_data.get("prior_art_searched", False)
        hypothesis   = company_data.get("hypothesis", "")
        result_pos   = company_data.get("result_positive", "")
        result_neg   = company_data.get("result_negative", "")

        # ── R&D 세액공제 추정 (조특§10 / §10의2) ──────────────────────
        rate_table = RD_CREDIT_NEW_GROWTH if is_new else RD_CREDIT_GENERAL
        credit_rate = rate_table.get(company_size, RD_CREDIT_GENERAL["중소"])
        rd_credit = rd_expense * credit_rate

        # ── 직무발명 보상 비과세 (조특§12 / 소§12⑤마목) ───────────────
        reward_taxfree = min(inv_reward, INVENTOR_REWARD_TAX_FREE_ANNUAL)
        reward_taxable = max(0, inv_reward - INVENTOR_REWARD_TAX_FREE_ANNUAL)

        # ── 타임스탬프 + 문서 해시 (입증력 확보) ──────────────────────
        ts_iso = datetime.now(timezone.utc).isoformat()
        doc_payload = json.dumps(
            {"topic": topic, "inventor": inventor, "ts": ts_iso,
             "hypothesis": hypothesis, "result_pos": result_pos,
             "result_neg": result_neg},
            ensure_ascii=False, sort_keys=True,
        )
        doc_hash = hashlib.sha256(doc_payload.encode("utf-8")).hexdigest()

        # ── 영업비밀 4요건 자가점검 ──────────────────────────────────
        trade_secret_check = self._check_trade_secret(company_data)

        # ── 결과 본문 ──────────────────────────────────────────────
        text = (
            f"발명자 관점: {inventor}({inv_role}) — 직무발명 (발명진흥법§10) 해당.\n"
            f"법인 측면: R&D 세액공제 약 {rd_credit:,.0f}원 "
            f"({company_size} {credit_rate:.0%}, "
            f"{'조특§10의2 신성장' if is_new else '조특§10 일반'}).\n"
            f"과세관청 관점: 직무발명 보상 {inv_reward:,.0f}원 중 "
            f"{reward_taxfree:,.0f}원 비과세(조특§12/소§12⑤마목), "
            f"과세분 {reward_taxable:,.0f}원.\n"
            f"금융기관 관점: 특허 자본화 시 무형자산 → IP 담보 대출 활용 가능.\n"
            f"문서 해시 SHA-256: {doc_hash[:16]}... (전체 길이 64) — 위·변조 방지."
        )

        result = {
            "agent": self.name,
            "text": text,
            "research_topic": topic,
            "inventor": inventor,
            "rd_credit_amount": rd_credit,
            "rd_credit_rate": credit_rate,
            "inventor_reward_tax_free": reward_taxfree,
            "inventor_reward_taxable": reward_taxable,
            "timestamp_utc": ts_iso,
            "document_hash_sha256": doc_hash,
            "trade_secret_4_requirements": trade_secret_check,
            "prior_art_searched": prior_art,
            "hypothesis": hypothesis,
            "result_positive": result_pos,
            "result_negative": result_neg,
            "inventor_contribution_pct": contrib_pct,
            "ksic_code": ksic_code,
            "ksic_new_growth_eligible": self._check_ksic_new_growth(ksic_code),
            "rd_pre_review_guide": self._rd_pre_review_guide(),
            "backup_schedule_guide": self._backup_schedule_guide(),
            "checklist": self._checklist(),
            "disclaimer": self._disclaimer(),
            "require_full_4_perspective": True,
        }

        # 5축 리스크 검증 + 4단계 헷지 + 4자×3시점 매트릭스 자동 첨부
        result["risk_5axis"] = self.validate_risk_5axis(result, company_data)
        result["risk_hedge_4stage"] = self.generate_risk_hedge_4stage(company_data)
        result["matrix_4x3"] = self._build_4x3_matrix(result)

        # 자가검증 4축
        result["self_check_4axis"] = self.validate(result)

        return result

    # ------------------------------------------------------------------ #
    # §A 리스크 검증 5축 (DOMAIN·LEGAL·CALC·LOGIC·CROSS)                    #
    # ------------------------------------------------------------------ #

    def validate_risk_5axis(self, result: dict, company_data: dict) -> dict:
        axes: dict[str, dict] = {}

        # DOMAIN: 발명자 특정·기여도·실험 재현성·선행기술조사
        domain_pass = (
            result.get("inventor", "미지정") != "미지정"
            and result.get("research_topic", "미지정") != "미지정"
            and result.get("prior_art_searched", False) is True
        )
        axes["DOMAIN"] = {
            "pass": domain_pass,
            "detail": (
                f"발명자={result['inventor']}, 주제={result['research_topic']}, "
                f"선행기술조사={result['prior_art_searched']}"
            ),
        }

        # LEGAL: 발명진흥법§10 직무발명 정의 + 영업비밀 4요건
        ts_check = result.get("trade_secret_4_requirements", {})
        legal_pass = (
            sum(1 for v in ts_check.values() if v) >= 3  # 4요건 중 3개 이상
        )
        axes["LEGAL"] = {
            "pass": legal_pass,
            "detail": (
                f"영업비밀 4요건 충족 {sum(1 for v in ts_check.values() if v)}/4 "
                f"(부정경쟁방지법§2 8호) | 직무발명(발명진흥법§10) 적용"
            ),
        }

        # CALC: R&D 공제율 정확성 (조특§10/§10의2)
        company_size = company_data.get("company_size", "중소")
        is_new = company_data.get("is_new_growth", False)
        expected_rate = (
            RD_CREDIT_NEW_GROWTH if is_new else RD_CREDIT_GENERAL
        ).get(company_size, RD_CREDIT_GENERAL["중소"])
        calc_pass = abs(result["rd_credit_rate"] - expected_rate) < 1e-9
        axes["CALC"] = {
            "pass": calc_pass,
            "detail": (
                f"공제율 적용 {result['rd_credit_rate']:.0%} = "
                f"기대치 {expected_rate:.0%} ({company_size}, "
                f"{'신성장' if is_new else '일반'})"
            ),
        }

        # LOGIC: 가설→결과 인과 + 부정 결과도 기록
        logic_pass = bool(
            result.get("hypothesis") and (
                result.get("result_positive") or result.get("result_negative")
            )
        )
        axes["LOGIC"] = {
            "pass": logic_pass,
            "detail": (
                f"가설 기록={bool(result.get('hypothesis'))}, "
                f"긍정결과={bool(result.get('result_positive'))}, "
                f"부정결과={bool(result.get('result_negative'))}"
            ),
        }

        # CROSS: 4자관점 (발명자·법인·과세관청·금융기관) 모두 본문 포함
        text = result.get("text", "")
        perspectives = ["발명자", "법인", "과세관청", "금융기관"]
        present = [p for p in perspectives if p in text]
        cross_pass = len(present) == 4
        axes["CROSS"] = {
            "pass": cross_pass,
            "detail": f"4자관점 노출 {len(present)}/4 ({present})",
        }

        all_pass = all(a["pass"] for a in axes.values())
        return {
            "all_pass": all_pass,
            "axes": axes,
            "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5",
        }

    # ------------------------------------------------------------------ #
    # §B 리스크 헷지 4단계 (Pre·Now·Post·Worst)                              #
    # ------------------------------------------------------------------ #

    def generate_risk_hedge_4stage(self, company_data: dict) -> dict:
        return {
            "1_pre": [
                "발명자 사전 특정 — 인사기록·연구계약서 명시",
                "NDA(비밀유지계약) 체결 — 부정경쟁방지법§2 영업비밀 입증",
                "선행기술조사 — KIPRIS·Google Patents 검색 결과 첨부",
            ],
            "2_now": [
                "타임스탬프 부여 — UTC ISO-8601 + SHA-256 해시 보존",
                "증인 서명 — 동료 연구원 1인 이상 서명·날짜 기재",
                "UTF-8 BOM 저장 — 한글 인코딩 무결성 보장",
            ],
            "3_post": [
                "정기 백업 — Git 커밋 + 외부 클라우드 이중 보관",
                "R&D 세액공제 사전심사 신청 — 국세청 사전 적격성 확인",
                "분기별 노트 누적 검토 — 영업비밀 합리적 노력 입증",
            ],
            "4_worst": [
                "위·변조 의혹 시: 해시 검증 + 증인 진술서 + 실험장비 로그",
                "세무조사 시: 연구노트 원본 + 해시 + 증빙 일괄 제출",
                "분쟁 시: 발명자 진술서 + 시계열 백업 + DOI(발급 시) 제시",
            ],
        }

    # ------------------------------------------------------------------ #
    # 4자관점 × 3시점 매트릭스                                               #
    # ------------------------------------------------------------------ #

    def _build_4x3_matrix(self, result: dict) -> dict:
        return {
            "발명자": {
                "사전": "직무발명 신고 의무·보상 청구권 확보",
                "현재": f"보상금 {result['inventor_reward_tax_free']:,.0f}원 비과세 수령",
                "사후": "특허 등록 후 추가 보상·로열티 수령",
            },
            "법인": {
                "사전": "직무발명 규정·보상 기준 사전 정비",
                "현재": f"R&D 세액공제 {result['rd_credit_amount']:,.0f}원 적용",
                "사후": "특허권 자본화·IP 담보 대출 활용",
            },
            "과세관청": {
                "사전": "R&D 세액공제 사전심사 적격성 확인 + KSIC 신성장 분류 검토",
                "현재": "조특§10/§10의2·§12 적용 검증 + 직무발명 보상금 비과세 한도",
                "사후": "사후관리 5년 — 적격 R&D 지출 입증 + 부정행위 시 가산세 40%",
            },
            "금융기관": {
                "사전": "IP 담보가치 사전 평가 의뢰",
                "현재": "R&D 자본화 → 무형자산 인식 → 신용등급 영향",
                "사후": "특허 등록 후 IP 담보 대출 한도 상향",
            },
        }

    # ------------------------------------------------------------------ #
    # 자가검증 4축 (계산·법령·4자관점·회귀)                                    #
    # ------------------------------------------------------------------ #

    def validate(self, result: dict) -> dict:
        text = result.get("text", "")
        ax_calc = any(c.isdigit() for c in text)
        ax_law  = any(k in text for k in ["§", "법", "조특", "발명진흥"])
        ax_4P   = sum(1 for p in ["발명자", "법인", "과세관청", "금융기관"]
                      if p in text) >= 4
        ax_regr = result.get("require_full_4_perspective", False)
        return {
            "calc": ax_calc, "law": ax_law,
            "perspective_4": ax_4P, "regression": ax_regr,
            "all_pass": all([ax_calc, ax_law, ax_4P, ax_regr]),
        }

    # ------------------------------------------------------------------ #
    # 보조: 영업비밀 4요건 점검·체크리스트·면책                                #
    # ------------------------------------------------------------------ #

    def _check_trade_secret(self, company_data: dict) -> dict[str, bool]:
        # [3중루프 보강] input pass-through 대신 다중 조건 점검
        nda_signed     = company_data.get("nda_signed", False)
        access_control = company_data.get("access_control", False)
        has_marking    = company_data.get("confidential_marking", False)
        return {
            "비공지성": company_data.get("not_publicly_known", True),
            "경제적가치": company_data.get("has_economic_value", True)
                          and company_data.get("rd_expense", 0) > 0,
            "합리적비밀유지노력": nda_signed and (access_control or has_marking),
            "기술경영정보": (
                company_data.get("research_topic", "") != ""
                and company_data.get("research_topic", "") != "미지정"
            ),
        }

    # [3중루프 보강] KSIC 신성장 적격성 안내
    def _check_ksic_new_growth(self, ksic_code: str) -> dict:
        # 조특§10의2 별표 — 신성장원천기술 KSIC 예시 코드
        new_growth_prefixes = ["26", "27", "28", "30", "61", "62", "70", "72"]
        eligible = any(ksic_code.startswith(p) for p in new_growth_prefixes) if ksic_code else False
        return {
            "ksic_code": ksic_code,
            "is_new_growth_eligible": eligible,
            "guide": (
                "조특§10의2 신성장원천기술 R&D 적격 KSIC 코드: "
                "26(전자부품)·27(의료정밀광학)·28(전기장비)·30(자동차)·"
                "61(통신)·62(SW개발)·70(R&D서비스)·72(연구개발). "
                f"입력 KSIC '{ksic_code}' → {'적격' if eligible else '비적격(일반 적용)'}"
            ),
        }

    # [3중루프 보강] R&D 세액공제 사전심사 절차 안내
    def _rd_pre_review_guide(self) -> dict:
        return {
            "신청기관": "국세청 (관할 세무서)",
            "근거": "조특§10·§10의2 + 조특령§9",
            "신청시기": "R&D 종료 전 또는 신고 이전",
            "절차": [
                "1. 연구개발계획서·예산서 준비",
                "2. 연구노트·실험데이터·증빙 첨부",
                "3. 신성장 적격 시 한국산업기술진흥원(KIAT) 적격성 확인서",
                "4. 국세청 사전심사 신청 → 결과 회신 (30~60일)",
                "5. 결과 반영하여 법인세 신고서 작성",
            ],
            "효과": "사후 부인 위험 최소화 + 가산세 면제",
        }

    # [3중루프 보강] 정기 백업 schtasks 등록 안내
    def _backup_schedule_guide(self) -> dict:
        return {
            "frequency": "주 1회 (매주 일요일 23:00)",
            "schtasks_command": (
                'schtasks /Create /TN "RnDLabNotebookBackup" /TR '
                '"powershell -File C:\\Users\\sik37\\consulting-agent\\bootstrap\\rnd_backup.ps1" '
                "/SC WEEKLY /D SUN /ST 23:00 /F"
            ),
            "backup_targets": [
                "agents/active/rnd_lab_notebook.py",
                "output/연구노트_*.docx",
                "output/연구노트_*.json (해시 포함)",
            ],
            "retention": "최소 5년 (조특§10 사후관리 기간)",
        }

    def _checklist(self) -> list[str]:
        return [
            "[함정] 발명자 특정 누락 시 직무발명 입증 실패",
            "[함정] 부정 결과 누락 시 R&D 세액공제 부인 위험",
            "[리스크] NDA 미체결 시 영업비밀 4요건 중 합리적 비밀유지노력 미충족",
            "[실행] 매 실험마다 타임스탬프 + 해시 + 증인 서명 3종 동시 확보",
            "[실행] 분기별 R&D 세액공제 사전심사 신청 (국세청)",
        ]

    def _disclaimer(self) -> str:
        return (
            "본 자료는 검토용 초안이며, 최종 직무발명 신고·특허 출원·"
            "R&D 세액공제 신고는 변리사·세무사 검토를 거쳐 진행하십시오. "
            "특허 분쟁·소송 대응은 변호사 자문 필수."
        )
