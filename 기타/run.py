"""
run.py — 컨설팅 에이전트 시스템 진입점
======================================
COMPANY_DATA에 고객 데이터를 입력한 후 실행:
  python run.py
"""

import sys
import os

# ── 경로 설정 ──────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

# ── API 키 확인 ─────────────────────────────────────────────────────────────
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("[오류] ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
    print("  PowerShell: $env:ANTHROPIC_API_KEY = 'sk-ant-...'")
    sys.exit(1)

from orchestrator import Orchestrator

# ============================================================
# COMPANY_DATA — 여기에 고객 데이터를 입력하세요
# ============================================================
COMPANY_DATA = {
    # 기업 기본정보
    "company_name":       "(주)한국정밀",
    "industry":           "자동차부품 제조업",
    "years_in_operation": 18,
    "employees":          45,

    # 손익
    "revenue":            8_500_000_000,    # 연매출 85억
    "taxable_income":     800_000_000,      # 과세표준 8억
    "net_income":         300_000_000,      # 당기순이익 3억
    "rd_expense":         150_000_000,      # R&D 지출 1.5억

    # 재무상태표
    "total_assets":       10_000_000_000,   # 100억
    "total_equity":        2_000_000_000,   # 20억
    "total_debt":          8_000_000_000,   # 80억
    "current_assets":      1_500_000_000,   # 15억
    "current_liabilities": 2_500_000_000,   # 25억

    # 주식
    "shares_outstanding":   200_000,        # 20만주
    "net_asset_per_share":   10_000,        # 1주당 순자산가치 1만원
    "net_income_per_share":  15_000,        # 1주당 순손익가치 1.5만원

    # 승계
    "business_value":    10_000_000_000,    # 가업 자산 100억
    "ceo_age":                        58,
    "successor_name":    "김민준 (아들, 30세)",

    # 특허·자산
    "patents":                         3,
    "provisional_payment": 200_000_000,     # 가지급금 2억
    "real_estate": {
        "type": "공장",
        "value": 3_000_000_000,             # 공장 30억
        "location": "경기 안산시",
    },

    # 주요 고객사
    "main_customers": ["현대자동차", "기아", "현대모비스"],

    # 주요 현안 (자유 기술)
    "concerns": [
        "가지급금 2억원 미해결 — 세무조사 리스크",
        "부채비율 400% — 금융기관 신규 여신 제한",
        "대표 58세 — 승계 계획 전무",
        "중대재해처벌법 대응 체계 미구축 (45인)",
        "보유 특허 3건 — IP 금융 미활용",
        "현대자동차 협력사 ESG 실사 예정 (2025년)",
        "공장 30억 법인 보유 — 양도 시 최적 구조 미검토",
    ],
}
# ============================================================


def main() -> None:
    orchestrator = Orchestrator(verbose=True)
    result = orchestrator.run(COMPANY_DATA)
    result.print_summary()

    # 결과 파일 저장
    output_path = os.path.join(os.path.dirname(__file__), "output", "report.txt")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"=== {COMPANY_DATA['company_name']} 컨설팅 보고서 ===\n\n")
        f.write(f"실행 시간: {result.elapsed_seconds:.1f}초\n\n")
        for name, text in result.agent_results.items():
            f.write(f"\n{'='*60}\n[{name}]\n{'='*60}\n{text}\n")
        f.write(f"\n{'='*60}\n[최종 보고서]\n{'='*60}\n{result.final_report}\n")
    print(f"\n[저장 완료] {output_path}")


if __name__ == "__main__":
    main()
