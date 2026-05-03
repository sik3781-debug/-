# RnDLabNotebookAgent — `/연구노트`

직무발명·R&D 세액공제 사전심사·영업비밀 입증 대비 연구노트 자동 생성.

## 핵심 기능
- 발명자 특정 + 기여도 % 기록
- R&D 세액공제 추정 (조특§10 일반 / §10의2 신성장)
- 직무발명 보상 비과세 한도 산출 (조특§12, 연 700만원)
- 영업비밀 4요건 자가점검 (부정경쟁방지법§2)
- KSIC 신성장 적격성 분류
- 타임스탬프(UTC) + SHA-256 해시 보존

## 핵심 법령
- 발명진흥법 §2 (직무발명 정의), §10 (사용자 권리·발명자 보상)
- 조특 §10 (R&D 세액공제 — 중소 25% / 중견 8% / 대기업 2%)
- 조특 §10의2 (신성장 — 중소 40% / 중견 30% / 대기업 20%)
- 조특 §12 (직무발명 보상금 50% 감면 + 연 700만원 비과세)
- 부정경쟁방지법 §2 (영업비밀 4요건)
- 특허법 §29 (신규성·진보성)

## 5축 리스크 검증
| 축 | 검증 항목 |
|---|---|
| DOMAIN | 발명자·주제·선행기술조사 모두 특정 |
| LEGAL | 영업비밀 4요건 중 3개 이상 충족 |
| CALC | R&D 공제율 lookup 정확성 |
| LOGIC | 가설 + (긍정 또는 부정) 결과 기록 |
| CROSS | 4자관점(발명자·법인·과세관청·금융기관) 본문 노출 |

## 4단계 헷지
- **사전**: 발명자 특정 / NDA 체결 / 선행기술조사
- **진행**: 타임스탬프 + 해시 + 증인 서명 + UTF-8 BOM
- **사후**: Git+클라우드 이중 백업 / R&D 사전심사 신청
- **최악**: 위·변조 의혹 시 해시 검증·증인 진술서·실험장비 로그

## 후속 세션 심화 권고
- DOI 자동 발급 API 통합 (현재 SHA-256만)
- 블록체인 타임스탬프 (현재 ISO-8601만)
- 발명자 기여도 가중치 알고리즘 정밀화

## 사용 예
```python
from agents.active.rnd_lab_notebook import RnDLabNotebookAgent
result = RnDLabNotebookAgent().analyze({
    "research_topic": "AI 자동화 검사 알고리즘",
    "inventor": "김개발",
    "company_size": "중소",
    "rd_expense": 200_000_000,
    "is_new_growth": True,
    "ksic_code": "26120",
    "inventor_reward": 10_000_000,
    "prior_art_searched": True,
    "hypothesis": "딥러닝으로 검사정확도 95% 달성",
    "result_positive": "정확도 96.3%",
    "result_negative": "엣지케이스 일부 실패",
    "nda_signed": True, "access_control": True, "confidential_marking": True,
})
```

작성: 2026-05-04 [LAPTOP]
