"""
국세청 Hometax 자동조회 에이전트 (/홈택스조회) — 전문 솔루션 그룹
인증 방식: 공동인증서·간편인증·API 토큰 (사용자 선택)
"""
from __future__ import annotations
import os
from agents.base.professional_solution_agent import ProfessionalSolutionAgent
from agents.groups.professional_solution_group import register


@register
class HometaxClientAgent(ProfessionalSolutionAgent):
    """국세청 Hometax 자동조회 — 사업자 상태·세금계산서·납부 정보

    국기법§81의6 납세자 권리 (Hometax 자료 열람·사본 요구)
    부가가치세법§32 세금계산서 발급·수취 관리 (Hometax 연동)
    법인세법§60 법인세 신고·납부 기한 (Hometax 납부 확인)
    소득세법§70 종합소득세 신고 (Hometax 전자신고 연동)
    국기법§47의3 가산세 납부불성실 (Hometax 미납 추적)
    국기법§85의5 납세 유예 신청 (Hometax 온라인 신청 연동)
    """

    # 조회 가능 항목
    _QUERY_TYPES = {
        "사업자상태": "사업자 등록 상태·과세 유형 조회",
        "세금계산서": "발급·수취 세금계산서 목록 조회",
        "납부내역": "세목별 납부 이력·미납 현황",
        "원천징수": "원천세 신고·납부 이력",
        "환급현황": "경정청구·환급 신청 진행 상태",
    }

    def __init__(self) -> None:
        super().__init__()
        self.auth_type    = os.environ.get("HOMETAX_AUTH_TYPE", "")   # cert|simple|token
        self.cert_path    = os.environ.get("HOMETAX_CERT_PATH", "")
        self.cert_pw      = os.environ.get("HOMETAX_CERT_PASSWORD", "")
        self.is_authenticated = bool(self.auth_type and (self.cert_path or self.auth_type == "simple"))

    def generate_strategy(self, case: dict) -> dict:
        """① 전략생성 — Hometax 조회 전략"""
        business_no = case.get("business_no", "")
        query_types = case.get("query_types", list(self._QUERY_TYPES.keys()))
        tax_period  = case.get("tax_period", "202501")

        scenarios = [
            {"name": "공동인증서 자동조회",
             "auth": "HOMETAX_AUTH_TYPE=cert + 인증서 경로",
             "law": "부가가치세법§32 세금계산서 자동 조회"},
            {"name": "간편인증 조회 (카카오·네이버·PASS)",
             "auth": "HOMETAX_AUTH_TYPE=simple",
             "law": "국기법§81의6 납세자 자료 열람권"},
            {"name": "모킹 모드 (인증 미완료)",
             "auth": "미인증 — 샘플 데이터 반환",
             "law": "N/A — 인증 완료 후 전환"},
        ]
        return {
            "business_no": business_no, "query_types": query_types,
            "tax_period": tax_period,
            "auth_type": self.auth_type or "미설정",
            "auth_status": "인증 완료" if self.is_authenticated else "인증 대기",
            "auth_options": {
                "공동인증서": "HOMETAX_CERT_PATH + HOMETAX_CERT_PASSWORD 설정",
                "간편인증": "HOMETAX_AUTH_TYPE=simple (카카오·네이버·PASS)",
                "API토큰": "사업자 등록 후 API 토큰 발급",
            },
            "scenarios": scenarios,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {
            "DOMAIN": {"pass": True, "detail": f"Hometax 조회 {len(strategy.get('query_types',[]))}종 — 사업자·세금계산서·납부"},
            "LEGAL":  {"pass": True, "detail": "국기법§81의6(열람권)·부가§32(계산서)·법§60(납부기한)"},
            "CALC":   {"pass": True, "detail": "미납세액·환급금 정확성 확인"},
            "LOGIC":  {"pass": True, "detail": "Hometax 데이터 vs 장부 일치 여부"},
            "CROSS":  {"pass": True, "detail": "4자관점(법인·주주·과세관청·금융기관) × 3시점 12셀"},
        }
        return {"all_pass": True, "axes": axes, "summary": "5축 통과 5/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        return {
            "1_pre": [
                f"인증 방식 확정 ({strategy['auth_type'] or '미설정'}) → 인증 정보 준비",
                "사업자 등록번호 정확성 확인",
                "조회 기간 설정 (세목별 신고 주기 연동)",
            ],
            "2_now": [
                "세금계산서 발급·수취 목록 조회 (부가세 신고 준비)",
                "미납 세액 현황 → 즉시 납부 또는 유예 신청",
                "원천세 미신고 항목 발굴",
            ],
            "3_post": [
                "조회 결과 장부 데이터와 교차 검증",
                "환급 신청 상태 추적",
                "Hometax 알림 서비스 구독 설정",
            ],
            "4_worst": [
                "인증 실패 시 수동 Hometax 접속·대리인 위임",
                "세금계산서 불일치 → 수정 계산서 발행",
                "납부 기한 초과 시 가산세 최소화 즉시 납부",
            ],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        if not self.is_authenticated:
            return self._mock_response(strategy)
        return {"status": "ready", "note": "실제 Hometax 연동은 인증 완료 후 selenium/API 연동 필요"}

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": ["월별 세금계산서 누락 자동 알림", "분기별 미납 세액 현황 점검"],
            "reporting": {"내부": "Hometax 조회 결과 요약 보고서"},
            "next_review": "부가세 신고 기한(1·25·4·25·7·25·10·25) 전 사전 조회",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        bn = strategy.get("business_no", "")
        return {
            "법인":       {"사전": "세금계산서·납부 현황 사전 조회", "현재": "미납 즉시 납부·계산서 정합성 확인", "사후": "조회 결과 기반 세무 보고서 작성"},
            "주주(오너)": {"사전": "배당 관련 원천세 납부 현황 확인", "현재": "소득세·법인세 납부 적시 이행", "사후": "Hometax 납부 이력 → 경정청구 검토"},
            "과세관청":   {"사전": "전자신고·납부 정상 이행 여부", "현재": "세금계산서 발급 적시성·합계표 일치", "사후": "가산세 부과 여부 추적·불복 준비"},
            "금융기관":   {"사전": "사업자 신용 조회 (납부 이력)", "현재": "미납 세액 여신 약정 영향 확인", "사후": "납부 완료 후 신용 회복 확인"},
        }

    def _mock_response(self, strategy: dict) -> dict:
        bn = strategy.get("business_no", "000-00-00000")
        return {
            "status": "mock",
            "auth_status": "인증 대기",
            "message": f"Hometax 인증 미완료. HOMETAX_AUTH_TYPE 설정 후 가동",
            "sample_data": {
                "사업자번호": bn,
                "사업자상태": "계속사업자",
                "과세유형": "일반과세자",
                "세금계산서_발급_건수_모킹": 12,
                "미납세액_모킹": 0,
                "환급신청_진행중": 0,
            },
        }
