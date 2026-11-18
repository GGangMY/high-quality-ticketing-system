# 결과보고서

캠프 가이드 「최종 발표 결과 보고서 작성」에 맞춘 최종 결과보고서다. 가이드는 실시간 발표 PPT가 곧 결과보고서이고, 목차 5개(프로젝트 개요, 팀 구성 및 역할, 수행 절차 및 방법, 수행 경과, 자체 평가 의견)를 바꾸지 않게 정해 두었다. 파일명은 가이드대로 `결과보고서_05조_이선좌.pdf`다.

| 파일 | 내용 |
|---|---|
| [결과보고서_05조_이선좌.pdf](결과보고서_05조_이선좌.pdf) | 제출용 PDF 23쪽(1920×1080) |
| [report.html](report.html) | 원본. 장마다 `<section class="slide">` 하나 |
| [render.sh](render.sh) | Chrome headless로 PDF와 장별 PNG(`slide-N.png`, 커밋하지 않음)를 만든다 |
| [figures/](figures/) | 새로 그린 ERD 두 장(예매 DB, 결제·사용자 DB)과 설계 의도. `erd-gen.py`가 표 자리를 직접 정한 HTML을 만들고, Chrome으로 3200×1800 PNG를 뽑는다 |

## 형식

- 개조식, 명사 종결. 글꼴 Pretendard(로컬 설치), 색은 가이드 PDF의 빨강 `#E8344E` 한 가지와 검정·회색.
- 본문 장은 머리말 아래부터 꼬리말 위까지를 내용이 고르게 채운다(위아래 맞춤). 내용을 늘려 빈 곳을 메우지 않는다.
- 구조도·흐름도·ERD처럼 복잡한 그림은 장 전체를 그림으로 채우고 위에 제목만 작게 단다.
- 채울 근거가 없는 칸(자체 평가 점수·사유)은 비워 둔다.

## 근거

숫자와 사실은 [브로셔](../overview/2026-11-16-brochure.md)(11/16 집계), [SA MASTER](../../core/SA%20MASTER.md), [ADR](../../decisions/README.md), 코드에서 가져왔다. 피드백 반영 장은 Notion 「261026 1차 피드백 내용 모음」과 [11/9 튜터 이슈 노트](../../learning/kangmin/qna/2026-11-09-tutor-issues-ntp-ratelimiter-bulkhead.md)의 항목을 코드·설정·ADR과 대조해 반영 상태를 적었다.

## 다시 만들기

```bash
docs/presentation/report/render.sh
```
