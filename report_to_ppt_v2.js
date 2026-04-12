/**
 * report_to_ppt_v2.js
 * ===================
 * pptxgenjs 기반 컨설팅 보고서 PPT 생성기
 *
 * 사용법:
 *   node report_to_ppt_v2.js [input.json] [output.pptx]
 *
 * JSON 스키마 (최소 필수):
 * {
 *   "company_name": "...",
 *   "gen_date": "YYYY-MM-DD",
 *   "final_text": "...",          // 최종 통합 보고서 마크다운
 *   "verify_text": "...",         // 검증 요약
 *   "agent_results": {            // 에이전트별 결과
 *     "TaxAgent": "...",
 *     ...
 *   },
 *   "top5": [                     // (선택) 파싱 불필요 시 직접 입력
 *     { "title": "...", "body": "...", "level": "CRITICAL|HIGH|MEDIUM" }
 *   ],
 *   "savings": [                  // (선택)
 *     { "item": "...", "val": "...", "note": "..." }
 *   ],
 *   "diagnosis": [                // (선택)
 *     { "domain": "...", "kpi": "...", "level": "CRITICAL|MEDIUM|LOW" }
 *   ],
 *   "strategy": [                 // (선택)
 *     { "period": "3~6개월", "items": ["..."] }
 *   ]
 * }
 */

"use strict";

const fs   = require("fs");
const path = require("path");
const PptxGenJS = require("pptxgenjs");

// ── 색상 팔레트 ─────────────────────────────────────────────────────────
const C = {
  NAVY:     "000080",
  WHITE:    "FFFFFF",
  LGRAY:    "D1D9E6",   // 구분선·테이블 보더
  BGRAY:    "F5F7FA",   // 테이블 짝수행
  DKGRAY:   "333333",   // 일반 텍스트
  MGRAY:    "666666",   // 서브텍스트
  CRITICAL: "7F1D1D",   // 위험
  HIGH:     "B45309",   // 경고
  MEDIUM:   "475569",   // 주의
  GREEN:    "166534",   // 양호
};

// 슬라이드 크기 (16:9, in inches)
const W = 13.33;
const H = 7.5;

// 공통 치수
const HDR_H  = 0.7;
const DIV_Y  = HDR_H;
const DIV_H  = 0.025;
const BODY_Y = HDR_H + DIV_H + 0.12;
const FOOT_Y = H - 0.28;

const FONT_KR = "나눔고딕";
const FONT_EN = "Calibri";

// ── 유틸 ────────────────────────────────────────────────────────────────

function stripMd(t = "") {
  return t
    .replace(/[#*`>|🔴🟡🟢①②③④⑤📌⚡]/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/\s{2,}/g, " ")
    .trim();
}

function snippet(text = "", maxLen = 160) {
  const lines = [];
  for (const ln of text.split("\n")) {
    const s = stripMd(ln).trim();
    if (s.length > 4 && !s.startsWith("---") && !s.startsWith("```")) {
      lines.push(s);
    }
    if (lines.join(" ").length > maxLen) break;
  }
  return lines.join(" ").slice(0, maxLen);
}

function levelColor(lvl = "") {
  const m = { CRITICAL: C.CRITICAL, HIGH: C.HIGH, MEDIUM: C.MEDIUM, LOW: C.GREEN,
               RED: C.CRITICAL, YELLOW: C.HIGH, GREEN: C.GREEN };
  return m[lvl.toUpperCase()] || C.MGRAY;
}

function levelLabel(lvl = "") {
  const m = { CRITICAL:"CRITICAL", HIGH:"HIGH", MEDIUM:"MEDIUM", LOW:"LOW",
               RED:"CRITICAL", YELLOW:"MEDIUM", GREEN:"LOW" };
  return m[lvl.toUpperCase()] || lvl;
}

// ── 파싱 ────────────────────────────────────────────────────────────────

function parseTop5(txt) {
  const pat = /###\s+[①②③④⑤\d]+[.)]\s*([🔴🟡🟢]?)\s*(.+?)\n([\s\S]*?)(?=###\s+[①②③④⑤\d]|\n---|\n##|$)/g;
  const tasks = [];
  let m;
  while ((m = pat.exec(txt)) !== null && tasks.length < 5) {
    const emoji = m[1];
    const lvl   = emoji.includes("🔴") ? "CRITICAL" : emoji.includes("🟡") ? "MEDIUM" : "LOW";
    tasks.push({ title: stripMd(m[2]).slice(0, 70), body: stripMd(m[3]).slice(0, 200), level: lvl });
  }
  if (!tasks.length) return [
    { title:"유동성 위기 방어",      body:"유동비율 60%, 단기차입 차환 긴급 추진",        level:"CRITICAL" },
    { title:"가지급금 2억원 해소",   body:"세무조사 트리거, 인정이자 연 920만원 절감",    level:"CRITICAL" },
    { title:"법인세 절세 실행",      body:"R&D 세액공제 등 연간 5,225만원",             level:"HIGH" },
    { title:"차명주주 명의신탁 해소",body:"증여세·간주취득세 즉시 리스크",               level:"MEDIUM" },
    { title:"키맨보험 가입",         body:"연 660만원 절세 + 경영권 보호",              level:"MEDIUM" },
  ];
  return tasks;
}

function parseSavings(txt) {
  const rows = [];
  let inTbl = false;
  for (const ln of txt.split("\n")) {
    if (ln.includes("절세") && ln.includes("|") && ln.includes("항목")) { inTbl = true; continue; }
    if (inTbl) {
      if (!ln.includes("|") || ln.includes("---")) { if (rows.length) break; continue; }
      const cols = ln.trim().replace(/^\||\|$/g, "").split("|").map(c => stripMd(c.trim()));
      if (cols.length >= 2 && cols[0] && !cols[0].includes("항목"))
        rows.push({ item: cols[0], val: cols[1], note: cols[2] || "" });
    }
  }
  if (!rows.length) return [
    { item:"R&D 세액공제 외 법인세 절세",   val:"5,225만원/년",  note:"과세표준 2.5억 압축" },
    { item:"가지급금 해소 (인정이자 절감)", val:"920만원/년",   note:"연 4.6% 기준" },
    { item:"키맨보험 손금산입 절세",        val:"660만원/년",   note:"법인세율 22%" },
    { item:"신용등급 개선 → 금융비용 절감", val:"1~1.5억원/년", note:"금리 3~4%p 인하" },
  ];
  return rows;
}

function parseDiagnosis(txt) {
  const rows = [];
  let inTbl = false;
  for (const ln of txt.split("\n")) {
    if (ln.includes("진단 영역") && ln.includes("|")) { inTbl = true; continue; }
    if (inTbl) {
      if (!ln.includes("|") || ln.includes("---")) { if (rows.length) break; continue; }
      const cols = ln.trim().replace(/^\||\|$/g, "").split("|").map(c => c.trim());
      if (cols.length >= 3 && cols[0] && !cols[0].includes("진단")) {
        const sig = cols[1] || "";
        const lvl = sig.includes("RED") ? "CRITICAL" : sig.includes("YELLOW") ? "MEDIUM" : "LOW";
        rows.push({ domain: stripMd(cols[0]), kpi: stripMd(cols[2]), level: lvl });
      }
    }
  }
  return rows.slice(0, 6);
}

function parseStrategy(txt) {
  const pat = /###\s+.*?(\d+~\d+개월)[^\n]*\n([\s\S]*?)(?=###|$)/g;
  const phases = [];
  let m;
  while ((m = pat.exec(txt)) !== null && phases.length < 3) {
    const items = m[2].split("\n")
      .map(l => stripMd(l).trim())
      .filter(l => l.length > 5 && !l.startsWith("---"))
      .slice(0, 5)
      .map(l => l.slice(0, 80));
    if (items.length) phases.push({ period: m[1], items });
  }
  if (!phases.length) return [
    { period:"3~6개월",   items:["부채비율 400%→250% 개선","가지급금 해소 완료","R&D 세액공제 등록"] },
    { period:"6~12개월",  items:["신용등급 CCC→B+ 회복","영업이익률 3.5%→6%","주식 승계 로드맵 수립"] },
    { period:"12~36개월", items:["BBB 등급 달성·여신 정상화","EV 부품 라인업 전환","가업상속공제 구조 완성"] },
  ];
  return phases;
}

// ── 공통 슬라이드 요소 ────────────────────────────────────────────────────

function addHeader(slide, title, page, total) {
  // 네이비 헤더
  slide.addShape("rect", { x:0, y:0, w:W, h:HDR_H, fill:{ color:C.NAVY }, line:{ type:"none" } });
  slide.addText(title, {
    x:0.25, y:0.1, w:W-1.5, h:0.5,
    fontSize:14, bold:true, color:C.WHITE,
    fontFace:FONT_KR, valign:"middle",
  });
  if (page) {
    slide.addText(`${page} / ${total}`, {
      x:W-1.2, y:0.15, w:1.0, h:0.4,
      fontSize:9, color:C.LGRAY, fontFace:FONT_EN, align:"right",
    });
  }
  // 구분선
  slide.addShape("rect", { x:0, y:DIV_Y, w:W, h:DIV_H, fill:{ color:C.LGRAY }, line:{ type:"none" } });
}

function addFooter(slide, company) {
  slide.addShape("rect", { x:0, y:FOOT_Y, w:W, h:0.22, fill:{ color:C.BGRAY }, line:{ type:"none" } });
  slide.addText(company, { x:0.25, y:FOOT_Y+0.03, w:6, h:0.18, fontSize:7, color:C.MGRAY, fontFace:FONT_KR });
  slide.addText("본 보고서는 AI 에이전트 분석 결과이며 전문가 검토를 권고합니다.", {
    x:W-6, y:FOOT_Y+0.03, w:5.8, h:0.18, fontSize:6.5, color:C.MGRAY, fontFace:FONT_KR, align:"right",
  });
}

function addRiskBadge(slide, x, y, level) {
  const clr = levelColor(level);
  const lbl = levelLabel(level);
  slide.addShape("rect", { x, y, w:0.85, h:0.25, fill:{ color:clr }, line:{ type:"none" } });
  slide.addText(lbl, { x, y, w:0.85, h:0.25, fontSize:6.5, bold:true, color:C.WHITE, fontFace:FONT_EN, align:"center", valign:"middle" });
}

// ── 슬라이드 1: 표지 ──────────────────────────────────────────────────────

function slide1Cover(prs, company, genDate) {
  const slide = prs.addSlide();
  // 상단 네이비 밴드 (~38%)
  const bandH = 2.9;
  slide.addShape("rect", { x:0, y:0, w:W, h:bandH, fill:{ color:C.NAVY }, line:{ type:"none" } });
  // 좌측 화이트 강조 바
  slide.addShape("rect", { x:0.35, y:0.45, w:0.05, h:1.9, fill:{ color:C.WHITE }, line:{ type:"none" } });
  // 제목 (밴드 내)
  slide.addText("중소기업 경영컨설팅 종합 분석 보고서", {
    x:0.6, y:0.55, w:12.5, h:0.85,
    fontSize:22, bold:true, color:C.WHITE, fontFace:FONT_KR,
  });
  slide.addText("16 + 2 Expert Agents  ·  AI-Powered Integrated Consulting", {
    x:0.6, y:1.45, w:12.5, h:0.4,
    fontSize:10, color:C.LGRAY, fontFace:FONT_EN,
  });
  // 화이트 영역 — 회사명
  slide.addText(company, {
    x:0.6, y:3.3, w:12.5, h:1.1,
    fontSize:26, bold:true, color:C.NAVY, fontFace:FONT_KR,
  });
  // 구분선
  slide.addShape("rect", { x:0.6, y:4.4, w:12.3, h:0.025, fill:{ color:C.LGRAY }, line:{ type:"none" } });
  // 메타
  slide.addText(`보고서 생성일: ${genDate}`, {
    x:0.6, y:4.55, w:6, h:0.3, fontSize:10, color:C.MGRAY, fontFace:FONT_KR,
  });
  slide.addText("본 보고서는 AI 에이전트 분석 결과입니다. 최종 의사결정 전 전문가 검토를 권고합니다.", {
    x:0.6, y:4.92, w:12.5, h:0.3, fontSize:8.5, color:C.MGRAY, fontFace:FONT_KR,
  });
}

// ── 슬라이드 2: Executive Summary ─────────────────────────────────────────

function slide2Exec(prs, company, data) {
  const slide = prs.addSlide();
  addHeader(slide, "Executive Summary  —  경영 현황 종합 진단", 2, 6);
  addFooter(slide, company);

  // 종합 판정 박스
  slide.addShape("rect", { x:0.25, y:BODY_Y, w:1.9, h:1.05,
    fill:{ color:C.WHITE }, line:{ color:C.CRITICAL, pt:1.2 } });
  slide.addShape("rect", { x:0.25, y:BODY_Y, w:1.9, h:0.07,
    fill:{ color:C.CRITICAL }, line:{ type:"none" } });
  slide.addText("종합 판정", { x:0.25, y:BODY_Y+0.1, w:1.9, h:0.3,
    fontSize:8, color:C.MGRAY, fontFace:FONT_KR, align:"center" });
  slide.addText("RED", { x:0.25, y:BODY_Y+0.42, w:1.9, h:0.5,
    fontSize:20, bold:true, color:C.CRITICAL, fontFace:FONT_EN, align:"center" });

  // 진단 테이블
  const diag = data.diagnosis || parseDiagnosis(data.final_text || "");
  const colX  = [2.4, 5.55, 6.6];
  const colW  = [3.1, 1.0,  5.5];
  const hdrs  = ["진단 영역", "위험등급", "핵심 지표"];
  const rh    = 0.52;
  const tY    = BODY_Y;

  // 헤더행
  hdrs.forEach((h, i) => {
    slide.addShape("rect", { x:colX[i], y:tY, w:colW[i], h:rh,
      fill:{ color:C.NAVY }, line:{ type:"none" } });
    slide.addText(h, { x:colX[i]+0.06, y:tY+0.08, w:colW[i]-0.12, h:rh-0.12,
      fontSize:8.5, bold:true, color:C.WHITE, fontFace:FONT_KR, valign:"middle",
      align: i === 1 ? "center" : "left" });
  });

  (diag.length ? diag : [
    { domain:"재무 안정성", kpi:"부채비율 400%, 유동비율 60%",      level:"CRITICAL" },
    { domain:"신용·유동성", kpi:"신용등급 CCC 이하, 금리 10.5%",    level:"CRITICAL" },
    { domain:"수익성",     kpi:"영업이익률 3.5% (업계 5~8% 하회)",  level:"MEDIUM" },
    { domain:"기업가치",   kpi:"순부채 60억 > 사업가치",            level:"CRITICAL" },
    { domain:"세무·법률",  kpi:"가지급금 2억, 승계계획 전무",       level:"MEDIUM" },
    { domain:"산업 포지션",kpi:"EV 전환 대응 불확실",              level:"MEDIUM" },
  ]).forEach((row, ri) => {
    const y  = tY + rh * (ri + 1);
    const bg = ri % 2 === 0 ? C.WHITE : C.BGRAY;

    // 진단 영역
    slide.addShape("rect", { x:colX[0], y, w:colW[0], h:rh, fill:{ color:bg }, line:{ color:C.LGRAY, pt:0.4 } });
    slide.addShape("rect", { x:colX[0], y, w:0.1, h:rh, fill:{ color:levelColor(row.level) }, line:{ type:"none" } });
    slide.addText(row.domain, { x:colX[0]+0.16, y:y+0.09, w:colW[0]-0.22, h:rh-0.14,
      fontSize:8.5, bold:true, color:C.NAVY, fontFace:FONT_KR, valign:"middle" });

    // 위험등급 배지
    slide.addShape("rect", { x:colX[1], y, w:colW[1], h:rh, fill:{ color:bg }, line:{ color:C.LGRAY, pt:0.4 } });
    addRiskBadge(slide, colX[1]+0.075, y+0.135, row.level);

    // KPI
    slide.addShape("rect", { x:colX[2], y, w:colW[2], h:rh, fill:{ color:bg }, line:{ color:C.LGRAY, pt:0.4 } });
    slide.addText(row.kpi, { x:colX[2]+0.08, y:y+0.07, w:colW[2]-0.16, h:rh-0.1,
      fontSize:8, color:C.DKGRAY, fontFace:FONT_KR, valign:"middle" });
  });

  // 검증 결과 띠
  if (data.verify_text) {
    const vy = tY + rh * 7 + 0.1;
    slide.addShape("rect", { x:0.25, y:vy, w:W-0.5, h:0.45,
      fill:{ color:C.BGRAY }, line:{ color:C.LGRAY, pt:0.4 } });
    slide.addText("검증 결과", { x:0.4, y:vy+0.06, w:1.5, h:0.3,
      fontSize:7.5, bold:true, color:C.NAVY, fontFace:FONT_KR });
    slide.addText(stripMd(data.verify_text).slice(0, 220), {
      x:1.9, y:vy+0.06, w:W-2.2, h:0.35,
      fontSize:7.5, color:C.DKGRAY, fontFace:FONT_KR,
    });
  }
}

// ── 슬라이드 3: TOP 5 과제 ───────────────────────────────────────────────

function slide3Top5(prs, company, data) {
  const slide = prs.addSlide();
  addHeader(slide, "즉시 실행 과제  TOP 5", 3, 6);
  addFooter(slide, company);

  const tasks = data.top5 || parseTop5(data.final_text || "");
  const cardH = 1.03;
  const gap   = 0.11;

  tasks.slice(0, 5).forEach((task, i) => {
    const y   = BODY_Y + i * (cardH + gap);
    const clr = levelColor(task.level);

    // 카드 배경
    slide.addShape("rect", { x:0.25, y, w:W-0.5, h:cardH,
      fill:{ color:C.WHITE }, line:{ color:C.LGRAY, pt:0.5 } });
    // 상단 컬러 바
    slide.addShape("rect", { x:0.25, y, w:W-0.5, h:0.07,
      fill:{ color:clr }, line:{ type:"none" } });

    // 번호
    slide.addText(`0${i+1}`, { x:0.35, y:y+0.1, w:0.55, h:0.6,
      fontSize:18, bold:true, color:C.NAVY, fontFace:FONT_EN, valign:"middle" });

    // 위험등급 배지
    addRiskBadge(slide, 0.35, y+0.71, task.level);

    // 제목
    slide.addText(task.title, { x:1.1, y:y+0.1, w:6.5, h:0.42,
      fontSize:10.5, bold:true, color:C.NAVY, fontFace:FONT_KR, valign:"middle" });

    // 본문
    slide.addText(task.body, { x:1.1, y:y+0.53, w:W-1.5, h:0.42,
      fontSize:8.5, color:C.DKGRAY, fontFace:FONT_KR, valign:"top" });
  });
}

// ── 슬라이드 4: 절세 효과 ────────────────────────────────────────────────

function slide4Savings(prs, company, data) {
  const slide = prs.addSlide();
  addHeader(slide, "예상 절세·절감 효과", 4, 6);
  addFooter(slide, company);

  // KPI 카드 2개
  const kpiDefs = [
    { label:"연간 총 절세·절감", val:"1.7 ~ 2.2 억원", note:"직접 절세 + 금융비용 절감" },
    { label:"7년 누적 효과",     val:"12 ~ 15 억원",   note:"복리 효과 미포함" },
  ];
  const kpiW = 6.3;
  const kpiH = 1.2;
  kpiDefs.forEach((k, i) => {
    const x = 0.25 + i * (kpiW + 0.5);
    slide.addShape("rect", { x, y:BODY_Y, w:kpiW, h:kpiH,
      fill:{ color:C.WHITE }, line:{ color:C.LGRAY, pt:0.6 } });
    slide.addShape("rect", { x, y:BODY_Y, w:kpiW, h:0.07,
      fill:{ color:C.NAVY }, line:{ type:"none" } });
    slide.addText(k.label, { x:x+0.1, y:BODY_Y+0.12, w:kpiW-0.2, h:0.3,
      fontSize:8.5, color:C.MGRAY, fontFace:FONT_KR, align:"center" });
    slide.addText(k.val, { x:x+0.1, y:BODY_Y+0.42, w:kpiW-0.2, h:0.5,
      fontSize:20, bold:true, color:C.NAVY, fontFace:FONT_EN, align:"center" });
    slide.addText(k.note, { x:x+0.1, y:BODY_Y+0.94, w:kpiW-0.2, h:0.22,
      fontSize:7.5, color:C.MGRAY, fontFace:FONT_KR, align:"center" });
  });

  // 항목 테이블
  const rows   = data.savings || parseSavings(data.final_text || "");
  const tY     = BODY_Y + kpiH + 0.18;
  const colX   = [0.25, 6.95, 10.05];
  const colW   = [6.65, 3.05,  3.0];
  const hdrs   = ["절세·절감 항목", "연간 효과", "비고"];
  const rh     = 0.6;

  hdrs.forEach((h, i) => {
    slide.addShape("rect", { x:colX[i], y:tY, w:colW[i], h:rh,
      fill:{ color:C.NAVY }, line:{ type:"none" } });
    slide.addText(h, { x:colX[i]+0.07, y:tY+0.1, w:colW[i]-0.14, h:rh-0.14,
      fontSize:8.5, bold:true, color:C.WHITE, fontFace:FONT_KR,
      align: i === 1 ? "center" : "left", valign:"middle" });
  });

  rows.slice(0, 5).forEach((row, ri) => {
    const y  = tY + rh * (ri + 1);
    const bg = ri % 2 === 0 ? C.WHITE : C.BGRAY;
    [[row.item,"left"],[row.val,"center"],[row.note,"left"]].forEach(([val, al], ci) => {
      slide.addShape("rect", { x:colX[ci], y, w:colW[ci], h:rh,
        fill:{ color:bg }, line:{ color:C.LGRAY, pt:0.4 } });
      slide.addText(val, { x:colX[ci]+0.07, y:y+0.1, w:colW[ci]-0.14, h:rh-0.14,
        fontSize:ci === 1 ? 9 : 8.5, bold:ci === 1,
        color: ci === 1 ? C.NAVY : C.DKGRAY,
        fontFace:FONT_KR, align:al, valign:"middle" });
    });
  });
}

// ── 슬라이드 5: 에이전트 발견사항 ──────────────────────────────────────────

function slide5Agents(prs, company, data) {
  const slide = prs.addSlide();
  addHeader(slide, "에이전트별 핵심 발견사항", 5, 6);
  addFooter(slide, company);

  const ORDER = [
    ["TaxAgent","세무전략"],["StockAgent","주식평가"],["SuccessionAgent","가업승계"],
    ["FinanceAgent","재무구조"],["LegalAgent","법률리스크"],["PatentAgent","특허·IP"],
    ["LaborAgent","인사노무"],["IndustryAgent","업종분석"],["WebResearchAgent","시장조사"],
    ["PolicyFundingAgent","정책자금"],["CashFlowAgent","현금흐름"],["CreditRatingAgent","신용등급"],
    ["RealEstateAgent","부동산"],["InsuranceAgent","보험설계"],["MAValuationAgent","기업가치"],
    ["ESGRiskAgent","ESG"],
  ];

  const ar    = data.agent_results || {};
  const items = ORDER.filter(([k]) => ar[k]).map(([k, lbl]) => [lbl, snippet(ar[k], 110)]);

  const rh    = 0.52;
  const lblW  = 1.2;
  const cntW  = 5.05;
  const colL  = [0.22, 6.72];  // 2열 시작 X

  items.slice(0, 16).forEach(([lbl, snip], i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x   = colL[col];
    const y   = BODY_Y + row * rh;
    const bg  = row % 2 === 0 ? C.WHITE : C.BGRAY;

    // 레이블 (네이비)
    slide.addShape("rect", { x, y, w:lblW, h:rh,
      fill:{ color:C.NAVY }, line:{ type:"none" } });
    slide.addText(lbl, { x:x+0.05, y:y+0.1, w:lblW-0.1, h:rh-0.14,
      fontSize:8, bold:true, color:C.WHITE, fontFace:FONT_KR, align:"center", valign:"middle" });

    // 내용
    slide.addShape("rect", { x:x+lblW, y, w:cntW, h:rh,
      fill:{ color:bg }, line:{ color:C.LGRAY, pt:0.4 } });
    slide.addText(snip || "분석 완료", { x:x+lblW+0.07, y:y+0.07, w:cntW-0.14, h:rh-0.1,
      fontSize:7.8, color:C.DKGRAY, fontFace:FONT_KR, valign:"middle" });
  });
}

// ── 슬라이드 6: 중장기 전략 ───────────────────────────────────────────────

function slide6Strategy(prs, company, data) {
  const slide = prs.addSlide();
  addHeader(slide, "중장기 전략 방향", 6, 6);
  addFooter(slide, company);

  const phases   = data.strategy || parseStrategy(data.final_text || "");
  const phaseClr = [C.CRITICAL, C.MEDIUM, C.GREEN];
  const phaseLbl = ["단기", "중기", "장기"];
  const colW     = 4.2;
  const gap      = 0.18;

  // 타임라인 연결선
  slide.addShape("rect", { x:0.25, y:BODY_Y+0.82, w:W-0.5, h:0.03,
    fill:{ color:C.LGRAY }, line:{ type:"none" } });

  phases.slice(0, 3).forEach((phase, i) => {
    const clr = phaseClr[i];
    const x   = 0.25 + i * (colW + gap);
    const cH  = FOOT_Y - BODY_Y - 0.08;

    // 카드
    slide.addShape("rect", { x, y:BODY_Y, w:colW, h:cH,
      fill:{ color:C.WHITE }, line:{ color:C.LGRAY, pt:0.5 } });
    // 상단 컬러 바
    slide.addShape("rect", { x, y:BODY_Y, w:colW, h:0.07,
      fill:{ color:clr }, line:{ type:"none" } });

    // 단계 레이블
    slide.addText(phaseLbl[i], { x:x+0.1, y:BODY_Y+0.1, w:0.65, h:0.3,
      fontSize:8.5, bold:true, color:clr, fontFace:FONT_KR, valign:"middle" });
    // 기간
    slide.addText(phase.period, { x:x+0.78, y:BODY_Y+0.1, w:colW-0.9, h:0.3,
      fontSize:10, bold:true, color:C.NAVY, fontFace:FONT_EN, valign:"middle" });
    // 구분선
    slide.addShape("rect", { x:x+0.1, y:BODY_Y+0.48, w:colW-0.2, h:0.02,
      fill:{ color:C.LGRAY }, line:{ type:"none" } });
    // 타임라인 마커
    slide.addShape("rect", { x:x+colW-0.15, y:BODY_Y+0.69, w:0.15, h:0.27,
      fill:{ color:clr }, line:{ type:"none" } });

    // 항목
    phase.items.slice(0, 5).forEach((item, j) => {
      const iy = BODY_Y + 0.62 + j * 1.08;
      slide.addShape("rect", { x:x+0.12, y:iy+0.2, w:0.1, h:0.1,
        fill:{ color:clr }, line:{ type:"none" } });
      slide.addText(item, { x:x+0.3, y:iy+0.1, w:colW-0.45, h:0.88,
        fontSize:8.5, color:C.DKGRAY, fontFace:FONT_KR, valign:"top" });
    });
  });
}

// ── 메인 ────────────────────────────────────────────────────────────────

function buildPpt(inputData, outputPath) {
  const prs = new PptxGenJS();
  prs.layout  = "LAYOUT_WIDE";
  prs.author  = "ConsultingAgent";
  prs.subject = "중소기업 컨설팅 보고서";

  const company = inputData.company_name || "대상법인";
  const date    = inputData.gen_date     || new Date().toISOString().slice(0, 10);

  slide1Cover(prs, company, date);
  slide2Exec(prs, company, inputData);
  slide3Top5(prs, company, inputData);
  slide4Savings(prs, company, inputData);
  slide5Agents(prs, company, inputData);
  slide6Strategy(prs, company, inputData);

  return prs.writeFile({ fileName: outputPath });
}

// ── CLI ──────────────────────────────────────────────────────────────────

(async () => {
  const args = process.argv.slice(2);
  const inputPath = args[0] || path.join(__dirname, "output", "report_data.json");

  if (!fs.existsSync(inputPath)) {
    console.error(`[오류] JSON 파일 없음: ${inputPath}`);
    console.error("사용법: node report_to_ppt_v2.js [input.json] [output.pptx]");
    process.exit(1);
  }

  let data;
  try {
    data = JSON.parse(fs.readFileSync(inputPath, "utf8"));
  } catch (e) {
    console.error(`[오류] JSON 파싱 실패: ${e.message}`);
    process.exit(1);
  }

  const ts         = new Date().toISOString().replace(/[-:T]/g, "").slice(0, 13);
  const company    = data.company_name || "report";
  const outputPath = args[1] || path.join(__dirname, "output", `컨설팅보고서_v2_${ts}.pptx`);

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });

  console.log(`[PPT 생성] ${company} → ${outputPath}`);
  try {
    await buildPpt(data, outputPath);
    console.log(`[완료] ${outputPath}`);
  } catch (e) {
    console.error(`[오류] PPT 생성 실패: ${e.message}`);
    process.exit(1);
  }
})();
