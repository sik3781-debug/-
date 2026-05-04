# pdf

## 역할
PPT·DOCX·HTML → PDF 변환 및 보고서 최종 배포 패키지 생성 스킬.

## 트리거
- "PDF로 변환", "PDF 출력", "최종 보고서 PDF"
- "인쇄용", "이메일 첨부용"

## 지원 변환 경로

| 입력 | 변환 방법 | 출력 |
|---|---|---|
| .pptx | LibreOffice / win32com | .pdf |
| .docx | python-docx + reportlab | .pdf |
| .html | weasyprint / pdfkit | .pdf |
| .xlsx | openpyxl + xlrd | .pdf (표 형식) |

## 변환 설정 기본값
- 페이지 크기: A4
- 여백: 상하 1.8cm, 좌우 2.0cm
- 해상도: 300 DPI
- 폰트 임베딩: 포함 (나눔고딕·Calibri)
- 메타데이터: 작성자 여운식, 기관명 자동 삽입

## Windows 환경 우선순위
1. win32com (MS Office 설치 시)
2. LibreOffice CLI (--headless --convert-to pdf)
3. reportlab (순수 Python, 한글 폰트 별도 설정)

## 품질 기준
- 한글 폰트 깨짐 0건
- 표·이미지 잘림 0건
- 파일 크기 10MB 이하 (컨설팅 보고서 기준)
