/**
 * report_to_ppt_navy.js
 * 디자인B 레이아웃 + 안정감 있는 네이비 색감
 * 실행: node report_to_ppt_navy.js
 * 입력: output/report.txt (또는 output/final_report.txt)
 * 출력: output/컨설팅보고서_YYYYMMDD_HHMM.pptx
 */

const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

// ═══════════════════════════════════════════════════════
// 1. COLOR PALETTE — 안정감 있는 네이비 팔레트
// ═══════════════════════════════════════════════════════
const C = {
  // 메인 색상
  navy:      "000080",   // 헤더·주요 요소
  navyDeep:  "000050",   // 표지 배경
  navyMid:   "1E3A5F",   // 섹션 강조
  navyLight: "E8EDF5",   // 카드 배경
  navyPale:  "F0F3F8",   // 연한 배경

  // 기본
  white:     "FFFFFF",
  offWhite:  "F8FAFC",
  grayLine:  "D1D9E6",   // 구분선
  grayMid:   "64748B",   // 보조 텍스트
  grayBody:  "334155",   // 본문 텍스트
  grayLight: "94A3B8",   // 비활성

  // 리스크 색상 (어두울수록 위험)
  critical:  "7F1D1D",   // CRITICAL — 버건디
  high:      "3D1A0F",   // HIGH — 다크 브라운
  medium:    "475569",   // MEDIUM — 슬레이트
  low:       "14532D",   // LOW — 다크 그린 (양호)
  warn:      "78350F",   // WARNING — 다크 앰버

  // 차트 색상
  chartMain: "000080",   // 주 기업 데이터
  chartComp: "94A3B8",   // 업계 평균
  chartPos:  "1E3A5F",   // 긍정 수치
  chartNeg:  "7F1D1D",   // 부정 수치
};

// ═══════════════════════════════════════════════════════
// 2. 보고서 파싱
// ═══════════════════════════════════════════════════════
function loadReport() {
  const candidates = [
    "output/final_report.txt",
    "output/report.txt",
  ];
  for (const p of candidates) {
    if (fs.existsSync(p)) return fs.readFileSync(p, "utf8");
  }
  // 데모 데이터
  return null;
}

function parseReport(text) {
  if (!text) return getDemoData();
  const data = getDemoData();

  // 회사명
  const nameMatch = text.match(/주식회사\s+([^\s\n|]+)/);
  if (nameMatch) data.companyName = "주식회사 " + nameMatch[1];

  // 업종
  const indMatch = text.match(/업종[:\s]+([^\n,|]+)/);
  if (indMatch) data.industry = indMatch[1].trim();

  // 매출
  const revMatch = text.match(/연매출[:\s]+([0-9,]+)/);
  if (revMatch) data.revenue = revMatch[1];

  // 절세 효과
  const taxMatch = text.match(/연간\s*(?:총\s*)?절세[··\s]*절감[:\s]+([0-9.~\s억원]+)/);
  if (taxMatch) data.annualSaving = taxMatch[1].trim();

  // 최종 판정
  const judgeMatch = text.match(/종합\s*판정[:\s]+([^\n]+)/);
  if (judgeMatch) data.judgment = judgeMatch[1].trim();

  return data;
}

function getDemoData() {
  return {
    companyName: "주식회사 한국정밀",
    industry: "자동차부품 제조업",
    revenue: "85억원",
    totalAssets: "100억원",
    totalDebt: "102억원",
    equity: "25.5억원",
    netDebt: "60억원",
    judgment: "RED — 구조적 위기 | 흑자도산 경보 5단계",
    annualSaving: "1.7 ~ 2.2 억원",
    cumulSaving: "12 ~ 15 억원",
    agents: "23개",
    domains: "14개",
    topTasks: "TOP5",
    dateStr: (() => {
      const d = new Date();
      return `${d.getFullYear()}년 ${d.getMonth()+1}월 ${d.getDate()}일 결산 기준`;
    })(),
    // 슬라이드2 — S/I/W
    strength: [
      "매출 85억 지속 유지 (CAGR 양호)",
      "유동비율 60% — 단기 유동성 확보",
      "R&D 세액공제 5,225만원 즉시 신청 가능",
    ],
    issue: [
      "부채비율 400% — 이자보상배율 0.8배",
      "가지급금 2억원 — 세무조사 리스크",
      "순부채 60억 > EV 36억 — 기술적 자본잠식",
    ],
    watch: [
      "차명주식 — 형사·증여세 동시 리스크",
      "대표이사 58세 키맨 리스크 + 승계 전무",
      "EV 전환 — 자동차부품 업종 구조변화",
    ],
    // 슬라이드3 — 재무구조
    debtStructure: [
      { name: "단기차입금", val: 45 },
      { name: "장기차입금", val: 30 },
      { name: "매입채무",   val: 15 },
      { name: "기타부채",   val: 10 },
    ],
    revTrend: [
      { year: "2024", rev: 78, op: 5.1 },
      { year: "2025", rev: 82, op: 4.2 },
      { year: "2026(E)", rev: 85, op: 3.0 },
    ],
    // 슬라이드4 — TOP5
    tasks: [
      { rank: "01", title: "유동성 위기 방어 — 현금흐름 사수", level: "CRITICAL",
        desc: "유동비율 60% — 단기 금융부채 차환 및 매출채권 조기회수 긴급 추진", deadline: "D+30일" },
      { rank: "02", title: "가지급금 2억원 즉시 해소", level: "CRITICAL",
        desc: "인정이자 과세(연 4.6%) 회피 + 세무조사 선정 리스크 제거 → 절세 920만원/년", deadline: "D+60일" },
      { rank: "03", title: "법인세 절세 전략 즉시 실행", level: "CRITICAL",
        desc: "R&D 세액공제(조특법 §10) 연구전담부서 등록 → 연간 절세 5,225만원", deadline: "D+60일" },
      { rank: "04", title: "차명주식 명의신탁 해소", level: "MEDIUM",
        desc: "상증법 §45의2 증여세 + 간주취득세 리스크 → 실명 전환 로드맵 즉시 수립", deadline: "D+90일" },
      { rank: "05", title: "키맨보험으로 CEO 유고 리스크 차단", level: "MEDIUM",
        desc: "연 3,000만원 전액 손금산입 → 절세 660만원/년 + 경영권 보호", deadline: "D+30일" },
    ],
    // 슬라이드5 — 절세 효과
    savingItems: [
      { name: "신용등급 개선 (금융비용 절감)", val: 10000 },
      { name: "R&D 세액공제 (법인세 절세)",   val: 5225 },
      { name: "가지급금 해소 (인정이자 절감)", val: 920 },
      { name: "키맨보험 (손금산입)",           val: 660 },
    ],
    // 슬라이드6 — 레이더
    radar: [
      { name: "재무안정성", cur: 20, tgt: 55 },
      { name: "수익성",     cur: 35, tgt: 60 },
      { name: "유동성",     cur: 30, tgt: 65 },
      { name: "성장성",     cur: 50, tgt: 60 },
      { name: "기업가치",   cur: 25, tgt: 50 },
      { name: "리스크관리", cur: 15, tgt: 70 },
    ],
  };
}

// ═══════════════════════════════════════════════════════
// 3. 공통 헬퍼
// ═══════════════════════════════════════════════════════
function addHeader(slide, pres, companyName, dateStr, pageNum) {
  // 상단 네이비 헤더 바
  slide.addShape(pres.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.55,
    fill: { color: C.navy }, line: { color: C.navy }
  });
  // 회사명
  slide.addText(companyName, {
    x: 0.3, y: 0, w: 5, h: 0.55,
    fontSize: 10, color: "C5CFE8", bold: false,
    fontFace: "나눔고딕", valign: "middle"
  });
  // 날짜
  slide.addText(dateStr, {
    x: 5.3, y: 0, w: 3.5, h: 0.55,
    fontSize: 9, color: "8899BB", align: "right",
    fontFace: "나눔고딕", valign: "middle"
  });
  // 페이지 번호
  slide.addText(String(pageNum).padStart(2, "0"), {
    x: 8.9, y: 0, w: 0.8, h: 0.55,
    fontSize: 11, color: "6678AA", bold: true,
    align: "right", fontFace: "Calibri", valign: "middle"
  });
  // 하단 구분선
  slide.addShape(pres.ShapeType.rect, {
    x: 0, y: 0.55, w: "100%", h: 0.02,
    fill: { color: C.grayLine }, line: { color: C.grayLine }
  });
  // 푸터
  slide.addText("중기이코노미 기업지원단", {
    x: 0, y: 5.3, w: "100%", h: 0.25,
    fontSize: 8, color: C.grayLight, align: "center",
    fontFace: "나눔고딕"
  });
}

function riskColor(level) {
  if (level === "CRITICAL") return C.critical;
  if (level === "HIGH")     return C.high;
  if (level === "MEDIUM")   return C.medium;
  return C.low;
}

// ═══════════════════════════════════════════════════════
// 4. 슬라이드 생성
// ═══════════════════════════════════════════════════════

// ── SLIDE 1: 표지 ──────────────────────────────────────
function makeSlide1(pres, d) {
  const s = pres.addSlide();
  // 좌측 네이비 패널
  s.addShape(pres.ShapeType.rect, {
    x: 0, y: 0, w: 3.5, h: 5.625,
    fill: { color: C.navyDeep }, line: { color: C.navyDeep }
  });
  // 좌측 하단 강조선
  s.addShape(pres.ShapeType.rect, {
    x: 0, y: 5.2, w: 3.5, h: 0.08,
    fill: { color: C.navy }, line: { color: C.navy }
  });

  // 좌측: 기업명
  s.addText("기업분석 보고서", {
    x: 0.3, y: 0.5, w: 2.9, h: 0.35,
    fontSize: 11, color: "8899BB", fontFace: "나눔고딕"
  });
  s.addText(d.companyName, {
    x: 0.3, y: 0.9, w: 2.9, h: 1.1,
    fontSize: 22, bold: true, color: C.white,
    fontFace: "나눔고딕", breakLine: false
  });
  s.addShape(pres.ShapeType.rect, {
    x: 0.3, y: 2.05, w: 2.5, h: 0.02,
    fill: { color: "3355AA" }, line: { color: "3355AA" }
  });

  // 보고서 핵심 항목
  s.addText("보고서 핵심", {
    x: 0.3, y: 2.15, w: 2.9, h: 0.25,
    fontSize: 9, color: "8899BB", fontFace: "나눔고딕"
  });
  const bullets = [
    "재무제표 요약 / 재무구조 진단",
    "수익성 분석 / 리스크 현황",
    "절세 전략 / 승계 플랜 / 기업가치",
  ];
  bullets.forEach((b, i) => {
    s.addText("• " + b, {
      x: 0.3, y: 2.43 + i * 0.3, w: 2.9, h: 0.28,
      fontSize: 9.5, color: "AABBDD", fontFace: "나눔고딕"
    });
  });

  // KPI 3개
  const kpis = [
    { label: "분석 에이전트", val: d.agents },
    { label: "분석 도메인",   val: d.domains },
    { label: "즉시 과제",     val: d.topTasks },
  ];
  kpis.forEach((k, i) => {
    const y = 3.55 + i * 0.48;
    s.addShape(pres.ShapeType.rect, {
      x: 0.3, y, w: 2.9, h: 0.42,
      fill: { color: "0A1040" }, line: { color: "223377" }
    });
    s.addText(k.val, {
      x: 0.35, y: y + 0.02, w: 1.0, h: 0.38,
      fontSize: 18, bold: true, color: "AABBDD",
      fontFace: "Calibri", valign: "middle"
    });
    s.addText(k.label, {
      x: 1.4, y: y + 0.1, w: 1.75, h: 0.25,
      fontSize: 9, color: "8899BB", fontFace: "나눔고딕"
    });
  });

  // 날짜
  s.addText(d.dateStr, {
    x: 0.3, y: 5.25, w: 2.9, h: 0.25,
    fontSize: 8, color: "6677AA", fontFace: "나눔고딕"
  });

  // 우측: 보고서 정보 패널
  s.addShape(pres.ShapeType.rect, {
    x: 3.5, y: 0, w: 6.5, h: 5.625,
    fill: { color: C.offWhite }, line: { color: C.offWhite }
  });

  // 우측 상단
  s.addText("보고서 정보", {
    x: 3.7, y: 0.15, w: 6.1, h: 0.3,
    fontSize: 10, bold: true, color: C.navyMid, fontFace: "나눔고딕"
  });
  const infoRows = [
    ["기준 연도", "2026년 결산"],
    ["전문 영역", "5그룹"],
    ["우선 실행", d.topTasks],
    ["업종",     d.industry],
    ["기준 자료", "재무제표 기반"],
    ["보고 목적", "종합 경영진단"],
  ];
  infoRows.forEach(([k, v], i) => {
    const col = i % 2 === 0 ? 3.7 : 6.8;
    const row = Math.floor(i / 2);
    const y = 0.52 + row * 0.55;
    s.addShape(pres.ShapeType.rect, {
      x: col - 0.05, y: y - 0.02, w: 2.8, h: 0.46,
      fill: { color: C.navyLight }, line: { color: C.grayLine }
    });
    s.addText(k, { x: col, y, w: 2.7, h: 0.22, fontSize: 8.5, color: C.grayMid, fontFace: "나눔고딕" });
    s.addText(v, { x: col, y: y + 0.2, w: 2.7, h: 0.22, fontSize: 11, bold: true, color: C.navyMid, fontFace: "나눔고딕" });
  });

  // 종합 판정 박스
  s.addShape(pres.ShapeType.rect, {
    x: 3.65, y: 4.3, w: 6.2, h: 0.75,
    fill: { color: C.critical }, line: { color: C.critical }
  });
  s.addText("종합 판정", {
    x: 3.8, y: 4.32, w: 1.5, h: 0.25,
    fontSize: 8, color: "FFAAAA", fontFace: "나눔고딕"
  });
  s.addText("● " + d.judgment, {
    x: 3.8, y: 4.55, w: 5.9, h: 0.42,
    fontSize: 12, bold: true, color: C.white, fontFace: "나눔고딕", valign: "middle"
  });

  // 기관명
  s.addText("중기이코노미 기업지원단  |  전문 경영컨설턴트", {
    x: 3.65, y: 5.2, w: 6.2, h: 0.3,
    fontSize: 8.5, color: C.grayMid, align: "right", fontFace: "나눔고딕"
  });
}

// ── SLIDE 2: 결산 핵심진단 ─────────────────────────────
function makeSlide2(pres, d) {
  const s = pres.addSlide();
  addHeader(s, pres, d.companyName, d.dateStr, 2);

  // 제목
  s.addText("결산  핵심진단", {
    x: 0.3, y: 0.65, w: 5, h: 0.45,
    fontSize: 20, bold: true, color: C.navy, fontFace: "나눔고딕"
  });
  s.addText("재무제표 및 AI 에이전트 분석 기반", {
    x: 0.3, y: 1.08, w: 5, h: 0.22,
    fontSize: 9.5, color: C.grayMid, fontFace: "나눔고딕"
  });

  // S/I/W 3개 박스
  const siw = [
    { label: "Strength",   color: C.navyMid,  bg: "E8EDF5", items: d.strength },
    { label: "Issue",      color: C.critical, bg: "FDF0F0", items: d.issue },
    { label: "Watchpoint", color: C.warn,     bg: "FDF4E8", items: d.watch },
  ];
  siw.forEach((box, i) => {
    const x = 0.25 + i * 3.2;
    s.addShape(pres.ShapeType.rect, {
      x, y: 1.35, w: 3.1, h: 1.65,
      fill: { color: box.bg }, line: { color: box.color, pt: 1.2 }
    });
    s.addShape(pres.ShapeType.rect, {
      x, y: 1.35, w: 3.1, h: 0.3,
      fill: { color: box.color }, line: { color: box.color }
    });
    s.addText(box.label, {
      x: x + 0.1, y: 1.35, w: 2.9, h: 0.3,
      fontSize: 10, bold: true, color: C.white,
      fontFace: "Calibri", valign: "middle"
    });
    box.items.forEach((item, j) => {
      s.addText("• " + item, {
        x: x + 0.1, y: 1.68 + j * 0.3, w: 2.9, h: 0.28,
        fontSize: 9, color: C.grayBody, fontFace: "나눔고딕", wrap: true
      });
    });
  });

  // 차트 제목
  s.addText("주요 재무지표 — 한국정밀 vs 업계 평균", {
    x: 0.3, y: 3.1, w: 6, h: 0.25,
    fontSize: 9.5, bold: true, color: C.navyMid, fontFace: "나눔고딕"
  });

  // 묶음 바차트 (수동 구현)
  const metrics = [
    { name: "부채비율(%)",    comp: 400, avg: 150 },
    { name: "유동비율(%)",    comp: 60,  avg: 180 },
    { name: "영업이익률(%)",  comp: 3.5, avg: 6.5 },
    { name: "이자보상배율(x)", comp: 0.8, avg: 2.5 },
  ];
  const maxVal = 450;
  const chartX = 0.3, chartY = 3.42, chartW = 9.4, chartH = 1.8;
  const barW = 0.35, gap = 0.08, groupW = chartW / metrics.length;

  // 차트 배경
  s.addShape(pres.ShapeType.rect, {
    x: chartX, y: chartY, w: chartW, h: chartH,
    fill: { color: C.navyPale }, line: { color: C.grayLine, pt: 0.5 }
  });

  metrics.forEach((m, i) => {
    const cx = chartX + i * groupW + groupW / 2;
    const compH = (m.comp / maxVal) * (chartH - 0.4);
    const avgH  = (m.avg  / maxVal) * (chartH - 0.4);
    const baseY = chartY + chartH - 0.25;

    // 기업 바 (네이비)
    s.addShape(pres.ShapeType.rect, {
      x: cx - barW - gap/2, y: baseY - compH, w: barW, h: compH,
      fill: { color: C.navy }, line: { color: C.navy }
    });
    s.addText(String(m.comp), {
      x: cx - barW - gap/2 - 0.1, y: baseY - compH - 0.22, w: barW + 0.2, h: 0.2,
      fontSize: 8, color: C.navy, bold: true, align: "center", fontFace: "Calibri"
    });

    // 업계 바 (회색)
    s.addShape(pres.ShapeType.rect, {
      x: cx + gap/2, y: baseY - avgH, w: barW, h: avgH,
      fill: { color: C.grayLight }, line: { color: C.grayLight }
    });
    s.addText(String(m.avg), {
      x: cx + gap/2 - 0.1, y: baseY - avgH - 0.22, w: barW + 0.2, h: 0.2,
      fontSize: 8, color: C.grayMid, bold: true, align: "center", fontFace: "Calibri"
    });

    // 항목명
    s.addText(m.name, {
      x: cx - groupW/2 + 0.05, y: baseY + 0.03, w: groupW - 0.1, h: 0.18,
      fontSize: 8, color: C.grayBody, align: "center", fontFace: "나눔고딕"
    });
  });

  // 범례
  s.addShape(pres.ShapeType.rect, { x: 7.2, y: 3.12, w: 0.15, h: 0.15, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("한국정밀", { x: 7.38, y: 3.1, w: 1, h: 0.18, fontSize: 8, color: C.grayBody, fontFace: "나눔고딕" });
  s.addShape(pres.ShapeType.rect, { x: 8.3, y: 3.12, w: 0.15, h: 0.15, fill: { color: C.grayLight }, line: { color: C.grayLight } });
  s.addText("업계 평균", { x: 8.48, y: 3.1, w: 1, h: 0.18, fontSize: 8, color: C.grayBody, fontFace: "나눔고딕" });
}

// ── SLIDE 3: 재무구조 분석 ─────────────────────────────
function makeSlide3(pres, d) {
  const s = pres.addSlide();
  addHeader(s, pres, d.companyName, d.dateStr, 3);

  s.addText("재무구조 분석", {
    x: 0.3, y: 0.65, w: 5, h: 0.42,
    fontSize: 20, bold: true, color: C.navy, fontFace: "나눔고딕"
  });
  s.addText("부채 구조 / 매출·이익 추이", {
    x: 0.3, y: 1.05, w: 5, h: 0.22,
    fontSize: 9.5, color: C.grayMid, fontFace: "나눔고딕"
  });

  // ── 도넛 차트 (수동 파이 대신 범례+박스) ──
  s.addText("부채 구조", {
    x: 0.3, y: 1.32, w: 4.3, h: 0.22,
    fontSize: 9.5, bold: true, color: C.navyMid, fontFace: "나눔고딕"
  });

  const pieColors = [C.navy, C.navyMid, "4A6FA5", C.grayLight];
  const total = d.debtStructure.reduce((s, x) => s + x.val, 0);
  d.debtStructure.forEach((item, i) => {
    const pct = Math.round(item.val / total * 100);
    const y = 1.58 + i * 0.5;
    s.addShape(pres.ShapeType.rect, {
      x: 0.3, y: y + 0.05, w: 0.2, h: 0.3,
      fill: { color: pieColors[i] }, line: { color: pieColors[i] }
    });
    // 비율 바
    s.addShape(pres.ShapeType.rect, {
      x: 0.6, y: y + 0.05, w: pct * 0.035, h: 0.3,
      fill: { color: pieColors[i] }, line: { color: pieColors[i] },
      transparency: i * 10
    });
    s.addText(`${item.name}  ${pct}%  (${item.val}억)`, {
      x: 0.62, y: y + 0.08, w: 3.8, h: 0.25,
      fontSize: 9.5, color: C.grayBody, fontFace: "나눔고딕"
    });
  });

  // ── 막대 차트: 매출·이익 추이 ──
  s.addText("매출 및 영업이익 추이 (억원)", {
    x: 4.8, y: 1.32, w: 4.8, h: 0.22,
    fontSize: 9.5, bold: true, color: C.navyMid, fontFace: "나눔고딕"
  });

  const bx = 4.8, by = 1.58, bw = 4.8, bh = 1.85;
  const maxRev = 100;
  s.addShape(pres.ShapeType.rect, {
    x: bx, y: by, w: bw, h: bh,
    fill: { color: C.navyPale }, line: { color: C.grayLine, pt: 0.5 }
  });

  d.revTrend.forEach((item, i) => {
    const cx = bx + 0.5 + i * (bw / d.revTrend.length);
    const rH = (item.rev / maxRev) * (bh - 0.35);
    const oH = (item.op  / maxRev) * (bh - 0.35) * 3;
    const baseY = by + bh - 0.25;

    // 매출 바
    s.addShape(pres.ShapeType.rect, {
      x: cx, y: baseY - rH, w: 0.5, h: rH,
      fill: { color: C.navy }, line: { color: C.navy }
    });
    s.addText(String(item.rev), {
      x: cx, y: baseY - rH - 0.2, w: 0.5, h: 0.18,
      fontSize: 8, color: C.navy, bold: true, align: "center", fontFace: "Calibri"
    });

    // 영업이익 바
    s.addShape(pres.ShapeType.rect, {
      x: cx + 0.55, y: baseY - oH, w: 0.35, h: oH,
      fill: { color: "4A6FA5" }, line: { color: "4A6FA5" }
    });

    s.addText(item.year, {
      x: cx - 0.1, y: baseY + 0.03, w: 1.1, h: 0.18,
      fontSize: 8, color: C.grayBody, align: "center", fontFace: "나눔고딕"
    });
  });

  // 범례
  s.addShape(pres.ShapeType.rect, { x: 5.2, y: 1.34, w: 0.15, h: 0.14, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("매출액", { x: 5.38, y: 1.32, w: 0.9, h: 0.18, fontSize: 8, color: C.grayBody, fontFace: "나눔고딕" });
  s.addShape(pres.ShapeType.rect, { x: 6.2, y: 1.34, w: 0.15, h: 0.14, fill: { color: "4A6FA5" }, line: { color: "4A6FA5" } });
  s.addText("영업이익", { x: 6.38, y: 1.32, w: 0.9, h: 0.18, fontSize: 8, color: C.grayBody, fontFace: "나눔고딕" });

  // ── KPI 3개 카드 ──
  const kpis = [
    { label: "총 부채  /  부채비율 400%", val: d.totalDebt,  color: C.critical },
    { label: "자기자본  /  자본잠식 위험", val: d.equity,    color: C.warn },
    { label: "순부채  /  EV 36억 초과",   val: d.netDebt,   color: C.medium },
  ];
  kpis.forEach((k, i) => {
    const x = 0.25 + i * 3.25;
    s.addShape(pres.ShapeType.rect, {
      x, y: 3.62, w: 3.1, h: 1.45,
      fill: { color: C.navyLight }, line: { color: k.color, pt: 1.5 }
    });
    s.addShape(pres.ShapeType.rect, {
      x, y: 3.62, w: 3.1, h: 0.06,
      fill: { color: k.color }, line: { color: k.color }
    });
    s.addText(k.val, {
      x: x + 0.15, y: 3.75, w: 2.8, h: 0.7,
      fontSize: 28, bold: true, color: k.color,
      fontFace: "Calibri", valign: "middle"
    });
    s.addText(k.label, {
      x: x + 0.15, y: 4.5, w: 2.8, h: 0.45,
      fontSize: 9, color: C.grayMid, fontFace: "나눔고딕", wrap: true
    });
  });
}

// ── SLIDE 4: 즉시 실행 과제 TOP5 ─────────────────────
function makeSlide4(pres, d) {
  const s = pres.addSlide();
  addHeader(s, pres, d.companyName, d.dateStr, 4);

  s.addText("즉시 실행 과제  TOP 5", {
    x: 0.3, y: 0.65, w: 7, h: 0.42,
    fontSize: 20, bold: true, color: C.navy, fontFace: "나눔고딕"
  });
  s.addText("우선순위 · 실행 기한 · 절세 효과 기준", {
    x: 0.3, y: 1.05, w: 7, h: 0.22,
    fontSize: 9.5, color: C.grayMid, fontFace: "나눔고딕"
  });

  d.tasks.forEach((task, i) => {
    const y = 1.32 + i * 0.82;
    const rc = riskColor(task.level);

    // 행 배경
    s.addShape(pres.ShapeType.rect, {
      x: 0.25, y, w: 9.5, h: 0.75,
      fill: { color: i % 2 === 0 ? C.navyPale : C.white },
      line: { color: C.grayLine, pt: 0.5 }
    });
    // 좌측 컬러 바
    s.addShape(pres.ShapeType.rect, {
      x: 0.25, y, w: 0.06, h: 0.75,
      fill: { color: rc }, line: { color: rc }
    });

    // 순번
    s.addText(task.rank, {
      x: 0.38, y: y + 0.12, w: 0.45, h: 0.45,
      fontSize: 18, bold: true, color: rc,
      fontFace: "Calibri", align: "center", valign: "middle"
    });

    // 제목
    s.addText(task.title, {
      x: 0.9, y: y + 0.06, w: 5.5, h: 0.28,
      fontSize: 11, bold: true, color: C.navyMid, fontFace: "나눔고딕"
    });

    // 설명
    s.addText(task.desc, {
      x: 0.9, y: y + 0.36, w: 6.2, h: 0.32,
      fontSize: 8.5, color: C.grayBody, fontFace: "나눔고딕", wrap: true
    });

    // 레벨 뱃지
    s.addShape(pres.ShapeType.rect, {
      x: 7.2, y: y + 0.08, w: 1.0, h: 0.25,
      fill: { color: rc }, line: { color: rc }
    });
    s.addText(task.level, {
      x: 7.2, y: y + 0.08, w: 1.0, h: 0.25,
      fontSize: 8, bold: true, color: C.white,
      align: "center", valign: "middle", fontFace: "Calibri"
    });

    // 기한
    s.addShape(pres.ShapeType.rect, {
      x: 8.35, y: y + 0.08, w: 1.2, h: 0.25,
      fill: { color: C.navyLight }, line: { color: C.grayLine, pt: 0.5 }
    });
    s.addText(task.deadline, {
      x: 8.35, y: y + 0.08, w: 1.2, h: 0.25,
      fontSize: 8.5, bold: true, color: C.navyMid,
      align: "center", valign: "middle", fontFace: "나눔고딕"
    });
  });
}

// ── SLIDE 5: 예상 절세·절감 효과 ─────────────────────
function makeSlide5(pres, d) {
  const s = pres.addSlide();
  addHeader(s, pres, d.companyName, d.dateStr, 5);

  s.addText("예상 절세·절감 효과", {
    x: 0.3, y: 0.65, w: 6, h: 0.42,
    fontSize: 20, bold: true, color: C.navy, fontFace: "나눔고딕"
  });
  s.addText("즉시 실행 시 연간 효과 기준", {
    x: 0.3, y: 1.05, w: 6, h: 0.22,
    fontSize: 9.5, color: C.grayMid, fontFace: "나눔고딕"
  });

  // KPI 2개 빅카드
  const kpiCards = [
    { label: "연간 총 절세·절감", sub: "직접 절세 + 금융비용 절감", val: d.annualSaving },
    { label: "7년 누적 효과",    sub: "복리 효과 미포함 기준",       val: d.cumulSaving },
  ];
  kpiCards.forEach((k, i) => {
    const x = 0.25 + i * 4.8;
    s.addShape(pres.ShapeType.rect, {
      x, y: 1.32, w: 4.5, h: 1.0,
      fill: { color: C.navy }, line: { color: C.navy }
    });
    s.addText(k.label, {
      x: x + 0.2, y: 1.35, w: 4.1, h: 0.25,
      fontSize: 9, color: "AABBDD", fontFace: "나눔고딕"
    });
    s.addText(k.val, {
      x: x + 0.2, y: 1.58, w: 4.1, h: 0.5,
      fontSize: 26, bold: true, color: C.white,
      fontFace: "Calibri", valign: "middle"
    });
    s.addText(k.sub, {
      x: x + 0.2, y: 2.05, w: 4.1, h: 0.22,
      fontSize: 8.5, color: "8899BB", fontFace: "나눔고딕"
    });
  });

  // 수평 바 차트
  s.addText("항목별 연간 절세·절감 (만원)", {
    x: 0.3, y: 2.42, w: 6, h: 0.22,
    fontSize: 9.5, bold: true, color: C.navyMid, fontFace: "나눔고딕"
  });

  const maxSaving = 12000;
  const chartX = 0.25, chartY = 2.68, chartH = 2.4;
  const barH = 0.38, rowGap = 0.58;

  d.savingItems.forEach((item, i) => {
    const y = chartY + i * rowGap;
    const barW = (item.val / maxSaving) * 7.5;

    // 레이블
    s.addText(item.name, {
      x: chartX, y, w: 4.2, h: 0.25,
      fontSize: 9, color: C.grayBody, fontFace: "나눔고딕"
    });

    // 바
    s.addShape(pres.ShapeType.rect, {
      x: chartX, y: y + 0.27, w: barW, h: barH,
      fill: { color: i === 0 ? C.navyMid : C.navy },
      line: { color: i === 0 ? C.navyMid : C.navy }
    });

    // 값
    s.addText(item.val.toLocaleString() + "만원", {
      x: chartX + barW + 0.1, y: y + 0.27, w: 1.5, h: barH,
      fontSize: 10, bold: true, color: C.navyMid,
      fontFace: "Calibri", valign: "middle"
    });
  });
}

// ── SLIDE 6: 중장기 전략 ──────────────────────────────
function makeSlide6(pres, d) {
  const s = pres.addSlide();
  addHeader(s, pres, d.companyName, d.dateStr, 6);

  s.addText("중장기 전략 방향", {
    x: 0.3, y: 0.65, w: 6, h: 0.42,
    fontSize: 20, bold: true, color: C.navy, fontFace: "나눔고딕"
  });
  s.addText("단기 3~6개월 / 중기 6~12개월 실행 로드맵", {
    x: 0.3, y: 1.05, w: 6, h: 0.22,
    fontSize: 9.5, color: C.grayMid, fontFace: "나눔고딕"
  });

  // 좌측 전략 테이블
  const strategies = [
    { term: "단기 3~6개월", items: [
      { title: "부채비율 개선",   target: "목표: 400% → 250%", desc: "유상증자·자산매각·이익잉여금 전환" },
      { title: "영업이익률 개선", target: "목표: 3.5% → 6%+",  desc: "원가구조 분석·불량률 감소" },
      { title: "이자비용 절감",   target: "목표: 10.5% → 7%대", desc: "신용등급 개선 후 금리 재협상" },
    ]},
    { term: "중기 6~12개월", items: [
      { title: "신용등급 회복",   target: "목표: CCC → B+",     desc: "부채 감축 + 이자보상배율 1.5배" },
      { title: "EV 전환 대응",   target: "목표: 매출처 다각화", desc: "전기차 부품 라인업 확장" },
      { title: "주식 승계 설계", target: "목표: 절세형 승계",   desc: "주가 13,000원 기준 증여세 최소화" },
    ]},
  ];

  strategies.forEach((group, gi) => {
    const baseY = 1.33 + gi * 2.05;
    s.addShape(pres.ShapeType.rect, {
      x: 0.25, y: baseY, w: 0.2, h: 1.9,
      fill: { color: C.navy }, line: { color: C.navy }
    });
    s.addText(group.term, {
      x: 0.55, y: baseY, w: 5.5, h: 0.28,
      fontSize: 10, bold: true, color: C.navy, fontFace: "나눔고딕"
    });
    group.items.forEach((item, j) => {
      const y = baseY + 0.32 + j * 0.52;
      s.addShape(pres.ShapeType.rect, {
        x: 0.55, y, w: 5.5, h: 0.46,
        fill: { color: j % 2 === 0 ? C.navyPale : C.white },
        line: { color: C.grayLine, pt: 0.3 }
      });
      s.addText(item.title, {
        x: 0.65, y: y + 0.02, w: 2.2, h: 0.22,
        fontSize: 9.5, bold: true, color: C.navyMid, fontFace: "나눔고딕"
      });
      s.addText(item.target, {
        x: 0.65, y: y + 0.24, w: 2.2, h: 0.2,
        fontSize: 9, color: C.grayMid, fontFace: "나눔고딕"
      });
      s.addText(item.desc, {
        x: 2.95, y: y + 0.1, w: 3.0, h: 0.28,
        fontSize: 8.5, color: C.grayBody, fontFace: "나눔고딕", wrap: true
      });
    });
  });

  // 우측 레이더 차트 (수동 — 거미줄 없이 비교 바)
  s.addText("경영 건전성 현황", {
    x: 6.2, y: 1.33, w: 3.5, h: 0.25,
    fontSize: 9.5, bold: true, color: C.navyMid, fontFace: "나눔고딕"
  });

  // 범례
  s.addShape(pres.ShapeType.rect, { x: 6.2, y: 1.6, w: 0.15, h: 0.14, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("현재", { x: 6.38, y: 1.58, w: 0.7, h: 0.18, fontSize: 8, color: C.grayBody, fontFace: "나눔고딕" });
  s.addShape(pres.ShapeType.rect, { x: 7.1, y: 1.6, w: 0.15, h: 0.14, fill: { color: C.grayLight }, line: { color: C.grayLight } });
  s.addText("목표(1년 후)", { x: 7.28, y: 1.58, w: 1.2, h: 0.18, fontSize: 8, color: C.grayBody, fontFace: "나눔고딕" });

  const maxScore = 100;
  const rX = 6.2, rY = 1.82;
  d.radar.forEach((item, i) => {
    const y = rY + i * 0.56;
    const curW = (item.cur / maxScore) * 3.3;
    const tgtW = (item.tgt / maxScore) * 3.3;

    s.addText(item.name, {
      x: rX, y, w: 1.1, h: 0.22,
      fontSize: 8.5, color: C.grayBody, fontFace: "나눔고딕"
    });
    // 목표 바 (뒤)
    s.addShape(pres.ShapeType.rect, {
      x: rX + 1.15, y: y + 0.02, w: tgtW, h: 0.18,
      fill: { color: C.grayLine }, line: { color: C.grayLine }
    });
    // 현재 바 (앞)
    s.addShape(pres.ShapeType.rect, {
      x: rX + 1.15, y: y + 0.06, w: curW, h: 0.1,
      fill: { color: C.navy }, line: { color: C.navy }
    });
    s.addText(`${item.cur} → ${item.tgt}`, {
      x: rX + 1.15 + tgtW + 0.05, y, w: 0.8, h: 0.22,
      fontSize: 7.5, color: C.grayMid, fontFace: "Calibri"
    });
  });
}

// ═══════════════════════════════════════════════════════
// 5. MAIN
// ═══════════════════════════════════════════════════════
async function main() {
  const reportText = loadReport();
  const d = parseReport(reportText);

  const pres = new pptxgen();
  pres.layout  = "LAYOUT_WIDE";   // 13.33 x 7.5 → 10 x 5.625 인치 변환
  pres.layout  = "LAYOUT_16x9";
  pres.author  = "중기이코노미 기업지원단";
  pres.subject = "기업 경영진단 보고서";
  pres.title   = `${d.companyName} 경영진단 보고서`;

  makeSlide1(pres, d);
  makeSlide2(pres, d);
  makeSlide3(pres, d);
  makeSlide4(pres, d);
  makeSlide5(pres, d);
  makeSlide6(pres, d);

  if (!fs.existsSync("output")) fs.mkdirSync("output");
  const now = new Date();
  const stamp = `${now.getFullYear()}${String(now.getMonth()+1).padStart(2,"0")}${String(now.getDate()).padStart(2,"0")}_${String(now.getHours()).padStart(2,"0")}${String(now.getMinutes()).padStart(2,"0")}`;
  const outPath = `output/컨설팅보고서_navy_${stamp}.pptx`;

  await pres.writeFile({ fileName: outPath });
  console.log(`\n✅ 완료: ${outPath}`);
}

main().catch(console.error);
