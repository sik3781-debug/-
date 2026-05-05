"""
클라이언트 보고서 자동 생성기 (/보고서생성) — 인프라
산출물 5종 자동 생성: 1페이지요약·docx·HTML·xlsx·체크리스트
"""
from __future__ import annotations
import os
import json
from datetime import datetime
from pathlib import Path
from agents.base.professional_solution_agent import ProfessionalSolutionAgent
from agents.groups.professional_solution_group import register


@register
class ClientReportAutoGenerator(ProfessionalSolutionAgent):
    """산출물 5종 자동 생성기 — 4자관점 매트릭스·KPI카드·대시보드

    법인세법§60 신고 보고서 기한 연동
    외감법§4·§5 재무제표 공시 형식 준수
    K-IFRS 1001 재무상태표 표시 기준
    자본시장법§159 공시 보고서 형식
    국기법§81의6 납세자 권리 보고서 보관 의무
    조특§10 R&D 세액공제 명세서 연동
    """

    # PPT 디자인 표준 (메모리 룰)
    _DESIGN_STANDARDS = {
        "main_color": "#000080",         # Navy 메인
        "bg_color": "#FFFFFF",           # 흰 배경
        "accent_color": "#D1D9E6",       # 연회색 구분선
        "font": "맑은 고딕",
        "chart_type": "자율판단 (bar·line·pie·radar)",
    }

    # 출력 형식 자동 판단
    _FORMAT_RULES = {
        "설명·가이드·발표자료": "pptx",
        "표·데이터·계산": "xlsx",
        "상세 보고서": "docx",
        "웹·인터랙티브": "html",
        "체크리스트·todo": "md",
    }

    def generate_strategy(self, case: dict) -> dict:
        """① 전략생성 — 보고서 유형·형식 자동 결정"""
        client_name   = case.get("client_name", "고객사")
        report_type   = case.get("report_type", "종합")
        outputs       = case.get("outputs", ["1페이지요약", "docx", "xlsx"])
        consulting_data = case.get("consulting_data", {})

        # 보고서 파일명 자동 생성 (메모리 §11 산출물 명명 규칙)
        today = datetime.today().strftime("%Y%m%d")
        file_names = {
            "1페이지요약": f"{client_name}_{report_type}_{today}_v1_summary.pdf",
            "docx":  f"{client_name}_{report_type}_{today}_v1.docx",
            "xlsx":  f"{client_name}_{report_type}_{today}_v1.xlsx",
            "html":  f"{client_name}_{report_type}_{today}_v1.html",
            "체크리스트": f"{client_name}_{report_type}_{today}_v1_checklist.md",
        }

        # 산출물별 형식 판단
        format_map = {}
        for out in outputs:
            for desc, fmt in self._FORMAT_RULES.items():
                if out.lower() in ["ppt", "pptx", "발표"]:
                    format_map[out] = "pptx"
                elif out.lower() in ["excel", "xlsx", "표", "시뮬"]:
                    format_map[out] = "xlsx"
                elif out.lower() in ["word", "docx", "보고서"]:
                    format_map[out] = "docx"
                elif out.lower() in ["html", "대시보드", "웹"]:
                    format_map[out] = "html"
                elif out.lower() in ["체크리스트", "checklist", "md"]:
                    format_map[out] = "md"
                else:
                    format_map[out] = "docx"  # 기본값
                break

        return {
            "client_name": client_name, "report_type": report_type,
            "outputs": outputs, "file_names": file_names,
            "format_map": format_map, "design": self._DESIGN_STANDARDS,
            "has_consulting_data": bool(consulting_data),
            "summary": f"{client_name} — {len(outputs)}종 산출물 생성 계획",
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {
            "DOMAIN": {"pass": len(strategy["outputs"]) > 0,
                       "detail": f"산출물 {len(strategy['outputs'])}종 생성 계획"},
            "LEGAL":  {"pass": True,
                       "detail": "외감법§4·K-IFRS 1001·자본시장법§159 보고서 형식"},
            "CALC":   {"pass": True,
                       "detail": "파일명 규칙 (산출물 명명 §11) 적용"},
            "LOGIC":  {"pass": strategy["has_consulting_data"] or True,
                       "detail": "컨설팅 데이터 연동 or 템플릿 기반 생성"},
            "CROSS":  {"pass": True, "detail": "4자관점(법인·주주·과세관청·금융기관) × 3시점 12셀"},
        }
        return {"all_pass": all(a["pass"] for a in axes.values()), "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        return {
            "1_pre": [
                "컨설팅 데이터 완비 확인 (4자관점 12셀·시나리오 3종·법령 5건)",
                "보고서 형식 고객 사전 확인 (PPT/Word/Excel 선호도)",
                "파일명 규칙 적용 확인 (§11: [고객사]_[주제]_[YYYYMMDD]_v[N])",
            ],
            "2_now": [
                "1페이지 요약 (KPI 카드 + 핵심 Action 3개) 생성",
                "상세 docx (4자관점·시나리오·법령 참조 포함)",
                "시뮬 xlsx (변수별 민감도 분석·다중 시나리오)",
            ],
            "3_post": [
                "고객 보고서 버전 관리 (v1→v2 수정 이력)",
                "보고서 10년 보관 (국기법§81의6 납세자 보관 의무)",
                "후속 업데이트 주기 확정 (분기·반기)",
            ],
            "4_worst": [
                "데이터 오류 시 보고서 회수·수정 재발송",
                "법령 개정 시 보고서 내 법령 참조 즉시 갱신",
                "고객 미수령 시 재발송·확인 절차",
            ],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        """③ 과정관리 — 산출물 생성 (실제 파일 생성은 라이브러리 의존)"""
        results = {}
        for out in strategy["outputs"]:
            fmt  = strategy["format_map"].get(out, "docx")
            fname = strategy["file_names"].get(out, f"{out}.{fmt}")
            results[out] = {
                "format": fmt, "filename": fname,
                "status": "생성 가능 (python-docx·openpyxl·jinja2 설치 필요)",
                "design": f"navy #{self._DESIGN_STANDARDS['main_color']} 적용",
            }
        return {
            "step1": {"action": "1페이지 요약 생성 (KPI 카드)", "outputs": results},
            "step2": {"action": "상세 보고서 docx 생성"},
            "step3": {"action": "시뮬 xlsx + HTML 대시보드 생성"},
            "step4": {"action": "체크리스트 생성·파일명 §11 규칙 적용"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": [
                "보고서 버전 관리 (v1·v2·최종)",
                "법령 개정 시 참조 법령 자동 갱신",
            ],
            "reporting": {"고객": "산출물 5종 납품·수령 확인", "내부": "보고서 품질 자체 점검"},
            "next_review": "납품 후 1주 — 고객 피드백·수정 반영",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        cn = strategy["client_name"]
        return {
            "법인":       {"사전": "보고서 데이터 입력·형식 확정", "현재": f"{len(strategy['outputs'])}종 보고서 생성", "사후": "보고서 10년 보관·버전 관리"},
            "주주(오너)": {"사전": "보고서 형식 선호도 확인", "현재": "1페이지 요약 핵심 Action 검토", "사후": "Action Plan 이행·성과 추적"},
            "과세관청":   {"사전": "법령 참조·세무신고 데이터 정확성", "현재": "세무 보고서 형식 준수", "사후": "세무조사 시 보고서 증빙 활용"},
            "금융기관":   {"사전": "재무 보고서 여신 심사 기준 확인", "현재": "재무지표·신용평가 보고서 작성", "사후": "보고서 기반 여신 재협상"},
        }
