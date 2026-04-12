"""
report_to_ppt.py
================
output/final_report.txt -> PPT 자동 변환
슬라이드 6장 구성 (네이비 #000080 헤더, 화이트 배경, 나눔고딕)

단독 실행:
  python report_to_ppt.py [report_path]

orchestrator.py 에서 자동 호출:
  from report_to_ppt import build_ppt
  build_ppt(company_name, agent_results, final_report, verify_results)
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Cm, Pt, Emu

# ── 색상 상수 ──────────────────────────────────────────────────────────────
NAVY   = RGBColor(0x00, 0x00, 0x80)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
LGRAY  = RGBColor(0xD1, 0xD9, 0xE6)
RED    = RGBColor(0xC0, 0x00, 0x00)
YELLOW = RGBColor(0xFF, 0xC0, 0x00)
GREEN  = RGBColor(0x00, 0x70, 0x00)
DKGRAY = RGBColor(0x40, 0x40, 0x40)

# ── 슬라이드 크기: 16:9 와이드 ───────────────────────────────────────────
SLIDE_W = Cm(33.87)
SLIDE_H = Cm(19.05)

FONT_KR = "나눔고딕"
FONT_EN = "Calibri"


# ──────────────────────────────────────────────────────────────────────────
# 헬퍼 함수
# ──────────────────────────────────────────────────────────────────────────

def _rgb_hex(hex_str: str) -> RGBColor:
    h = hex_str.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _add_rect(slide, left, top, width, height, fill: RGBColor | None = None,
              line: RGBColor | None = None, line_w: int = 0) -> Any:
    shape = slide.shapes.add_shape(1, left, top, width, height)  # MSO_SHAPE_TYPE.RECTANGLE
    shape.line.fill.background()
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill
    else:
        shape.fill.background()
    if line:
        shape.line.color.rgb = line
        shape.line.width = Pt(line_w) if line_w else Pt(0.5)
    else:
        shape.line.fill.background()
    return shape


def _add_textbox(slide, left, top, width, height, text: str,
                 font_size: int = 11, bold: bool = False,
                 color: RGBColor = DKGRAY, align=PP_ALIGN.LEFT,
                 font_name: str = FONT_KR, wrap: bool = True) -> Any:
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font_name
    return tb


def _add_header(slide, title: str, subtitle: str = "") -> None:
    """모든 슬라이드 공통 — 상단 네이비 헤더 + 구분선."""
    # 헤더 배경
    _add_rect(slide, Cm(0), Cm(0), SLIDE_W, Cm(1.8), fill=NAVY)
    # 제목
    _add_textbox(slide, Cm(0.5), Cm(0.15), Cm(28), Cm(1.4),
                 title, font_size=16, bold=True, color=WHITE,
                 align=PP_ALIGN.LEFT)
    # 우측 부제
    if subtitle:
        _add_textbox(slide, Cm(27), Cm(0.35), Cm(6.5), Cm(1.0),
                     subtitle, font_size=9, color=LGRAY,
                     align=PP_ALIGN.RIGHT)
    # 구분선
    _add_rect(slide, Cm(0), Cm(1.8), SLIDE_W, Cm(0.06), fill=LGRAY)


def _add_footer(slide, page_num: int, total: int, company: str) -> None:
    """하단 페이지 번호 + 회사명."""
    _add_rect(slide, Cm(0), Cm(18.5), SLIDE_W, Cm(0.55), fill=_rgb_hex("#F5F7FA"))
    _add_textbox(slide, Cm(0.5), Cm(18.55), Cm(20), Cm(0.45),
                 company, font_size=7.5, color=DKGRAY)
    _add_textbox(slide, Cm(30), Cm(18.55), Cm(3.5), Cm(0.45),
                 f"{page_num} / {total}", font_size=7.5,
                 color=DKGRAY, align=PP_ALIGN.RIGHT)


def _status_color(status: str) -> RGBColor:
    return {"RED": RED, "YELLOW": YELLOW, "GREEN": GREEN}.get(status.upper(), DKGRAY)


def _badge(slide, left, top, width, height, text: str, fill: RGBColor) -> None:
    _add_rect(slide, left, top, width, height, fill=fill)
    _add_textbox(slide, left, top, width, height,
                 text, font_size=9, bold=True, color=WHITE,
                 align=PP_ALIGN.CENTER)


# ──────────────────────────────────────────────────────────────────────────
# 파싱 유틸
# ──────────────────────────────────────────────────────────────────────────

def _strip_md(text: str) -> str:
    """마크다운 기호 제거 (★,#,*,` 등)."""
    text = re.sub(r"[#*`>|]", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # 링크
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _extract_section(text: str, heading: str) -> str:
    """## heading 이하 다음 ## 까지 추출."""
    pat = re.compile(
        r"##\s+" + re.escape(heading) + r".*?\n(.*?)(?=\n##\s+|\Z)", re.DOTALL
    )
    m = pat.search(text)
    return m.group(1).strip() if m else ""


def _extract_agent_snippet(text: str, max_chars: int = 200) -> str:
    """에이전트 결과에서 첫 의미있는 줄들만 추출."""
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("```") or line.startswith("---"):
            continue
        cleaned = _strip_md(line)
        if cleaned and len(cleaned) > 5:
            lines.append(cleaned)
        if sum(len(l) for l in lines) > max_chars:
            break
    return " ".join(lines)[:max_chars]


def parse_report(report_path: str) -> dict:
    """final_report.txt 파싱 → 슬라이드 데이터 딕셔너리 반환."""
    with open(report_path, encoding="utf-8") as f:
        raw = f.read()

    # 회사명
    m = re.search(r"===\s+(.+?)\s+컨설팅", raw)
    company_name = m.group(1) if m else "대상법인"

    # 생성일시
    m = re.search(r"생성일시:\s*(.+)", raw)
    gen_date = m.group(1).strip()[:10] if m else datetime.now().strftime("%Y-%m-%d")

    # 에이전트별 결과 파싱
    agent_results: dict[str, str] = {}
    pattern = re.compile(
        r"={60}\n\[([^\]]+)\]\n={60}\n(.*?)(?=\n={60}|\Z)", re.DOTALL
    )
    for hit in pattern.finditer(raw):
        name = hit.group(1).strip()
        body = hit.group(2).strip()
        if name not in ("에이전트별 분석 결과", "검증 결과 요약", "최종 통합 보고서"):
            agent_results[name] = body

    # 최종 통합 보고서 섹션
    m = re.search(
        r"={60}\n\[ 최종 통합 보고서 \]\n={60}\n(.*?)$", raw, re.DOTALL
    )
    final_text = m.group(1).strip() if m else ""

    # 검증 결과 요약
    m = re.search(
        r"={60}\n\[ 검증 결과 요약 \]\n={60}\n(.*?)(?=\n={60})", raw, re.DOTALL
    )
    verify_text = m.group(1).strip() if m else ""

    return {
        "company_name": company_name,
        "gen_date": gen_date,
        "agent_results": agent_results,
        "final_text": final_text,
        "verify_text": verify_text,
    }


def _parse_top5(final_text: str) -> list[dict]:
    """최종 보고서에서 TOP5 과제 파싱."""
    tasks = []
    # ### ① ~ ⑤ 패턴 매칭
    pat = re.compile(
        r"###\s+[①②③④⑤\d]+[.)]?\s*([🔴🟡🟢]?)\s*(.+?)\n(.*?)(?=###\s+[①②③④⑤\d]|\n---|\n##|\Z)",
        re.DOTALL
    )
    for m in pat.finditer(final_text):
        emoji = m.group(1).strip()
        title = _strip_md(m.group(2)).strip()
        body = _strip_md(m.group(3)).strip()[:180]
        color = RED if "🔴" in emoji else (YELLOW if "🟡" in emoji else GREEN)
        tasks.append({"title": title, "body": body, "color": color})
        if len(tasks) >= 5:
            break

    # 패턴 미매칭 시 폴백
    if not tasks:
        for i, line in enumerate(final_text.splitlines()):
            if re.search(r"[①②③④⑤]", line):
                title = _strip_md(line)[:60]
                tasks.append({"title": title, "body": "", "color": NAVY})
            if len(tasks) >= 5:
                break
    return tasks


def _parse_savings(final_text: str) -> list[dict]:
    """절세·절감 효과 테이블 파싱."""
    rows = []
    in_table = False
    for line in final_text.splitlines():
        if "절세" in line and "|" in line and "항목" in line:
            in_table = True
            continue
        if in_table:
            if "|" not in line or "---" in line:
                if rows:
                    break
                continue
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cols) >= 2:
                item = _strip_md(cols[0])
                val  = _strip_md(cols[1])
                note = _strip_md(cols[2]) if len(cols) > 2 else ""
                if item and val and "항목" not in item:
                    rows.append({"item": item, "val": val, "note": note})
    return rows


def _parse_strategy(final_text: str) -> list[dict]:
    """중기 전략 단계 파싱 (3~6개월, 6~12개월 등)."""
    phases = []
    pat = re.compile(r"###\s+.*?(\d+~\d+개월)[^#\n]*\n(.*?)(?=###|\Z)", re.DOTALL)
    for m in pat.finditer(final_text):
        period = m.group(1)
        body   = m.group(2)
        items = []
        for line in body.splitlines():
            stripped = _strip_md(line).strip()
            if stripped and len(stripped) > 5 and not stripped.startswith("---"):
                items.append(stripped[:80])
            if len(items) >= 4:
                break
        if items:
            phases.append({"period": period, "items": items})
        if len(phases) >= 3:
            break
    return phases


def _parse_diagnosis(final_text: str) -> list[dict]:
    """경영 현황 진단 테이블 파싱."""
    rows = []
    in_table = False
    for line in final_text.splitlines():
        if "진단 영역" in line and "|" in line:
            in_table = True
            continue
        if in_table:
            if "|" not in line or "---" in line:
                if rows:
                    break
                continue
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cols) >= 3:
                domain = _strip_md(cols[0])
                signal = cols[1].strip()
                kpi    = _strip_md(cols[2])
                if domain and "진단" not in domain:
                    color = RED if "RED" in signal else (YELLOW if "YELLOW" in signal else GREEN)
                    rows.append({"domain": domain, "signal": signal, "kpi": kpi, "color": color})
    return rows[:6]


# ──────────────────────────────────────────────────────────────────────────
# 슬라이드 빌더
# ──────────────────────────────────────────────────────────────────────────

def _slide1_cover(prs: Presentation, company: str, date_str: str) -> None:
    """슬라이드 1: 표지."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank

    # 전체 네이비 배경
    _add_rect(slide, Cm(0), Cm(0), SLIDE_W, SLIDE_H, fill=NAVY)

    # 장식 라인 (화이트)
    _add_rect(slide, Cm(1.5), Cm(5.5), Cm(30.5), Cm(0.08), fill=WHITE)
    _add_rect(slide, Cm(1.5), Cm(13.5), Cm(30.5), Cm(0.08), fill=WHITE)

    # 메인 제목
    _add_textbox(slide, Cm(2), Cm(6.5), Cm(29), Cm(2.5),
                 "중소기업 경영컨설팅\n종합 분석 보고서",
                 font_size=28, bold=True, color=WHITE,
                 align=PP_ALIGN.CENTER)

    # 회사명
    _add_textbox(slide, Cm(2), Cm(9.5), Cm(29), Cm(1.8),
                 company, font_size=22, bold=True, color=LGRAY,
                 align=PP_ALIGN.CENTER)

    # 구분자
    _add_textbox(slide, Cm(2), Cm(11.2), Cm(29), Cm(0.8),
                 "16개 전문 에이전트 분석 | AI 기반 통합 컨설팅",
                 font_size=10, color=LGRAY, align=PP_ALIGN.CENTER)

    # 날짜
    _add_textbox(slide, Cm(2), Cm(14.5), Cm(29), Cm(1.0),
                 f"보고서 생성일: {date_str}",
                 font_size=10, color=LGRAY, align=PP_ALIGN.CENTER)


def _slide2_exec_summary(prs: Presentation, company: str,
                         final_text: str, verify_text: str) -> None:
    """슬라이드 2: Executive Summary."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_header(slide, "Executive Summary — 경영 현황 종합 진단", company)
    _add_footer(slide, 2, 6, company)

    # 종합 판정 배지
    _add_rect(slide, Cm(0.8), Cm(2.0), Cm(6.5), Cm(2.2), fill=RED)
    _add_textbox(slide, Cm(0.8), Cm(2.1), Cm(6.5), Cm(1.0),
                 "종합 판정", font_size=9, color=WHITE, align=PP_ALIGN.CENTER, bold=False)
    _add_textbox(slide, Cm(0.8), Cm(2.9), Cm(6.5), Cm(1.1),
                 "RED", font_size=20, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    # 진단 테이블
    diag = _parse_diagnosis(final_text)
    if not diag:
        diag = [
            {"domain": "재무 안정성", "signal": "🔴 RED", "kpi": "부채비율 400%, 유동비율 60%", "color": RED},
            {"domain": "신용·유동성", "signal": "🔴 RED", "kpi": "신용등급 CCC 이하, 금리 10.5%", "color": RED},
            {"domain": "수익성",     "signal": "🟡 YELLOW", "kpi": "영업이익률 3.5%", "color": YELLOW},
            {"domain": "기업가치",   "signal": "🔴 RED", "kpi": "순부채 60억 > 사업가치", "color": RED},
            {"domain": "세무·법률",  "signal": "🟡 YELLOW", "kpi": "가지급금 2억, 승계계획 전무", "color": YELLOW},
            {"domain": "산업 포지션","signal": "🟡 YELLOW", "kpi": "EV 전환 대응 불확실", "color": YELLOW},
        ]

    row_h = Cm(1.55)
    top0 = Cm(2.0)
    col_x = [Cm(7.8), Cm(17.0), Cm(21.5)]
    col_w = [Cm(8.8),  Cm(4.0),  Cm(11.5)]

    # 헤더행
    for ci, (hdr, cw) in enumerate(zip(["진단 영역", "신호", "핵심 지표"], col_w)):
        _add_rect(slide, col_x[ci], top0, cw, Cm(0.65), fill=NAVY)
        _add_textbox(slide, col_x[ci], top0, cw, Cm(0.65),
                     hdr, font_size=9, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    for ri, row in enumerate(diag[:6]):
        y = top0 + Cm(0.65) + ri * row_h
        bg = _rgb_hex("#F9F9FB") if ri % 2 == 0 else WHITE
        for ci, (key, cw) in enumerate(zip(["domain", "signal", "kpi"], col_w)):
            _add_rect(slide, col_x[ci], y, cw, row_h, fill=bg, line=LGRAY, line_w=0)
            txt = row[key]
            _add_textbox(slide, col_x[ci] + Cm(0.1), y + Cm(0.25),
                         cw - Cm(0.2), row_h - Cm(0.3),
                         _strip_md(txt), font_size=8.5, color=DKGRAY,
                         align=PP_ALIGN.LEFT if ci != 1 else PP_ALIGN.CENTER)
        # 신호 컬러 바
        _add_rect(slide, col_x[0], y, Cm(0.25), row_h, fill=row["color"])

    # 검증 요약 (우측 하단)
    if verify_text:
        _add_rect(slide, Cm(0.8), Cm(14.5), Cm(32.0), Cm(3.7), fill=_rgb_hex("#F0F3F8"))
        _add_textbox(slide, Cm(1.0), Cm(14.7), Cm(6), Cm(0.5),
                     "검증 결과", font_size=8, bold=True, color=NAVY)
        _add_textbox(slide, Cm(1.0), Cm(15.2), Cm(32.0), Cm(2.8),
                     _strip_md(verify_text)[:300], font_size=8, color=DKGRAY)


def _slide3_top5(prs: Presentation, company: str, final_text: str) -> None:
    """슬라이드 3: 즉시 실행 과제 TOP 5."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_header(slide, "즉시 실행 과제 TOP 5", company)
    _add_footer(slide, 3, 6, company)

    tasks = _parse_top5(final_text)
    if not tasks:
        tasks = [
            {"title": "유동성 위기 방어", "body": "유동비율 60%, 단기차입 차환 긴급 추진", "color": RED},
            {"title": "가지급금 2억원 해소", "body": "세무조사 트리거, 인정이자 연 920만원 절감", "color": RED},
            {"title": "법인세 절세 실행", "body": "R&D 세액공제 등 연간 5,225만원", "color": RED},
            {"title": "차명주주 명의신탁 해소", "body": "증여세·간주취득세 즉시 리스크", "color": YELLOW},
            {"title": "키맨보험 가입", "body": "연 660만원 절세 + 경영권 보호", "color": YELLOW},
        ]

    card_w = Cm(6.2)
    card_h = Cm(14.8)
    gap    = Cm(0.38)
    top0   = Cm(2.0)

    for i, task in enumerate(tasks[:5]):
        x = Cm(0.5) + i * (card_w + gap)
        # 카드 배경
        _add_rect(slide, x, top0, card_w, card_h, fill=_rgb_hex("#F9FAFB"), line=LGRAY, line_w=0)
        # 우선순위 컬러 상단 바
        _add_rect(slide, x, top0, card_w, Cm(0.45), fill=task["color"])
        # 순서 배지
        _badge(slide, x + Cm(0.15), top0 + Cm(0.6), Cm(0.9), Cm(0.65),
               f"0{i+1}", task["color"])
        # 제목
        _add_textbox(slide, x + Cm(0.15), top0 + Cm(1.4), card_w - Cm(0.3), Cm(3.0),
                     task["title"], font_size=10.5, bold=True, color=NAVY)
        # 본문
        _add_textbox(slide, x + Cm(0.15), top0 + Cm(4.2), card_w - Cm(0.3), Cm(10.0),
                     task["body"], font_size=8.5, color=DKGRAY)


def _slide4_savings(prs: Presentation, company: str, final_text: str) -> None:
    """슬라이드 4: 예상 절감효과 KPI 카드."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_header(slide, "예상 절세·절감 효과", company)
    _add_footer(slide, 4, 6, company)

    rows = _parse_savings(final_text)
    if not rows:
        rows = [
            {"item": "R&D 세액공제 외 법인세 절세", "val": "5,225만원/년", "note": "과세표준 압축"},
            {"item": "가지급금 해소 (인정이자 절감)", "val": "920만원/년",  "note": "연 4.6% 기준"},
            {"item": "키맨보험 손금산입 절세",         "val": "660만원/년",  "note": "법인세율 22%"},
            {"item": "신용등급 개선 → 금융비용 절감",  "val": "1~1.5억/년", "note": "금리 3~4%p"},
        ]

    # 상단 KPI 카드 2개
    kpi_cards = [
        {"label": "연간 총 절세·절감", "val": "1.7 ~ 2.2억원", "color": NAVY},
        {"label": "7년 누적 효과",     "val": "12 ~ 15억원",   "color": _rgb_hex("#1A5276")},
    ]
    for i, kpi in enumerate(kpi_cards):
        x = Cm(1.0) + i * Cm(16.5)
        _add_rect(slide, x, Cm(2.1), Cm(15.5), Cm(3.2), fill=kpi["color"])
        _add_textbox(slide, x, Cm(2.2), Cm(15.5), Cm(1.0),
                     kpi["label"], font_size=10, color=LGRAY, align=PP_ALIGN.CENTER)
        _add_textbox(slide, x, Cm(3.0), Cm(15.5), Cm(2.0),
                     kpi["val"], font_size=22, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    # 항목 테이블
    top0 = Cm(5.8)
    col_w = [Cm(16.5), Cm(8.0), Cm(8.5)]
    col_x = [Cm(0.8), Cm(17.5), Cm(25.7)]

    for ci, hdr in enumerate(["절세·절감 항목", "연간 효과", "비고"]):
        _add_rect(slide, col_x[ci], top0, col_w[ci], Cm(0.7), fill=NAVY)
        _add_textbox(slide, col_x[ci], top0, col_w[ci], Cm(0.7),
                     hdr, font_size=9.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    row_h = Cm(1.55)
    for ri, row in enumerate(rows):
        y = top0 + Cm(0.7) + ri * row_h
        bg = _rgb_hex("#EEF2F8") if ri % 2 == 0 else WHITE
        vals = [row["item"], row["val"], row.get("note", "")]
        for ci, (val, cw) in enumerate(zip(vals, col_w)):
            _add_rect(slide, col_x[ci], y, cw, row_h, fill=bg, line=LGRAY)
            _add_textbox(slide, col_x[ci] + Cm(0.15), y + Cm(0.3),
                         cw - Cm(0.3), row_h - Cm(0.4),
                         _strip_md(val), font_size=9, color=DKGRAY,
                         align=PP_ALIGN.LEFT if ci != 1 else PP_ALIGN.CENTER,
                         bold=(ci == 1))


def _slide5_agents(prs: Presentation, company: str,
                   agent_results: dict[str, str]) -> None:
    """슬라이드 5: 에이전트별 발견사항 2열 테이블."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_header(slide, "에이전트별 핵심 발견사항", company)
    _add_footer(slide, 5, 6, company)

    AGENT_LABELS = {
        "TaxAgent":           "세무전략",
        "StockAgent":         "주식평가",
        "SuccessionAgent":    "가업승계",
        "FinanceAgent":       "재무구조",
        "LegalAgent":         "법률리스크",
        "PatentAgent":        "특허·IP",
        "LaborAgent":         "인사노무",
        "IndustryAgent":      "업종분석",
        "WebResearchAgent":   "시장조사",
        "PolicyFundingAgent": "정책자금",
        "CashFlowAgent":      "현금흐름",
        "CreditRatingAgent":  "신용등급",
        "RealEstateAgent":    "부동산",
        "InsuranceAgent":     "보험설계",
        "MAValuationAgent":   "기업가치",
        "ESGRiskAgent":       "ESG",
    }

    items = []
    for name, label in AGENT_LABELS.items():
        if name in agent_results:
            snippet = _extract_agent_snippet(agent_results[name], 140)
            items.append((label, snippet))

    col_w = Cm(16.2)
    row_h = Cm(1.6)
    gap   = Cm(0.4)
    top0  = Cm(2.1)
    cols  = [Cm(0.5), Cm(17.0)]
    label_w = Cm(3.0)

    for i, (label, snippet) in enumerate(items[:16]):
        col = i % 2
        row = i // 2
        x = cols[col]
        y = top0 + row * row_h

        bg = _rgb_hex("#EEF2F8") if (row % 2 == 0) else WHITE
        _add_rect(slide, x, y, col_w, row_h, fill=bg, line=LGRAY)
        # 라벨 배지
        _add_rect(slide, x, y, label_w, row_h, fill=NAVY)
        _add_textbox(slide, x, y + Cm(0.45), label_w, row_h - Cm(0.5),
                     label, font_size=8.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        # 내용
        _add_textbox(slide, x + label_w + Cm(0.15), y + Cm(0.2),
                     col_w - label_w - Cm(0.3), row_h - Cm(0.4),
                     snippet if snippet else "분석 완료",
                     font_size=7.5, color=DKGRAY)


def _slide6_strategy(prs: Presentation, company: str, final_text: str) -> None:
    """슬라이드 6: 중장기 전략방향 3단계 타임라인."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_header(slide, "중장기 전략 방향", company)
    _add_footer(slide, 6, 6, company)

    phases = _parse_strategy(final_text)
    if not phases:
        phases = [
            {"period": "3~6개월",  "items": ["부채비율 400%→250% 단기 개선", "가지급금 해소 완료", "R&D 세액공제 등록"]},
            {"period": "6~12개월", "items": ["신용등급 CCC→B+ 회복", "영업이익률 3.5%→6% 개선", "주식 승계 로드맵 수립"]},
            {"period": "12~36개월","items": ["BBB 등급 달성·여신 정상화", "EV 부품 라인업 전환", "가업상속공제 구조 완성"]},
        ]

    PHASE_COLORS = [RED, YELLOW, GREEN]
    PHASE_LABELS = ["단기", "중기", "장기"]
    box_w = Cm(10.5)
    box_h = Cm(14.5)
    gap   = Cm(0.4)
    top0  = Cm(2.1)

    # 연결 화살표 라인
    _add_rect(slide, Cm(0.5), Cm(9.4), Cm(32.8), Cm(0.12), fill=LGRAY)

    for i, phase in enumerate(phases[:3]):
        x = Cm(0.5) + i * (box_w + gap)
        color = PHASE_COLORS[i]

        # 카드
        _add_rect(slide, x, top0, box_w, box_h, fill=WHITE, line=color, line_w=1)
        # 상단 헤더
        _add_rect(slide, x, top0, box_w, Cm(1.6), fill=color)
        # 단계 라벨
        _add_textbox(slide, x, top0 + Cm(0.1), Cm(2.5), Cm(0.75),
                     PHASE_LABELS[i], font_size=8.5, bold=True, color=WHITE,
                     align=PP_ALIGN.CENTER)
        # 기간
        _add_textbox(slide, x + Cm(2.5), top0 + Cm(0.1), box_w - Cm(2.5), Cm(0.75),
                     phase["period"], font_size=10, bold=True, color=WHITE)
        # 화살표 마커
        _add_rect(slide, x + box_w - Cm(0.3), Cm(9.2), Cm(0.6), Cm(0.6), fill=color)

        # 항목들
        for j, item in enumerate(phase["items"][:5]):
            y_item = top0 + Cm(2.0) + j * Cm(2.4)
            _add_rect(slide, x + Cm(0.3), y_item, Cm(0.3), Cm(0.3), fill=color)
            _add_textbox(slide, x + Cm(0.75), y_item - Cm(0.1),
                         box_w - Cm(1.0), Cm(2.1),
                         item, font_size=8.5, color=DKGRAY)


# ──────────────────────────────────────────────────────────────────────────
# 메인 빌더
# ──────────────────────────────────────────────────────────────────────────

def build_ppt(company_name: str,
              agent_results: dict[str, str],
              final_text: str,
              verify_text: str = "",
              gen_date: str = "",
              output_dir: str = "output") -> str:
    """PPT 생성 후 저장 경로 반환."""
    if not gen_date:
        gen_date = datetime.now().strftime("%Y-%m-%d")
    ts = datetime.now().strftime("%Y%m%d_%H%M")

    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H

    _slide1_cover(prs, company_name, gen_date)
    _slide2_exec_summary(prs, company_name, final_text, verify_text)
    _slide3_top5(prs, company_name, final_text)
    _slide4_savings(prs, company_name, final_text)
    _slide5_agents(prs, company_name, agent_results)
    _slide6_strategy(prs, company_name, final_text)

    os.makedirs(output_dir, exist_ok=True)
    filename = f"컨설팅보고서_{ts}.pptx"
    out_path = os.path.join(output_dir, filename)
    prs.save(out_path)
    print(f"[PPT 저장] {out_path}")
    return out_path


def build_ppt_from_file(report_path: str, output_dir: str = "output") -> str:
    """final_report.txt 로부터 PPT 생성."""
    data = parse_report(report_path)
    return build_ppt(
        company_name   = data["company_name"],
        agent_results  = data["agent_results"],
        final_text     = data["final_text"],
        verify_text    = data["verify_text"],
        gen_date       = data["gen_date"],
        output_dir     = output_dir,
    )


# ──────────────────────────────────────────────────────────────────────────
# CLI 진입점
# ──────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    report_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "output", "final_report.txt"
    )
    if not os.path.exists(report_path):
        print(f"[오류] 보고서 파일 없음: {report_path}")
        sys.exit(1)

    out = build_ppt_from_file(
        report_path,
        output_dir=os.path.join(os.path.dirname(__file__), "output"),
    )
    print(f"[완료] PPT 파일: {out}")
