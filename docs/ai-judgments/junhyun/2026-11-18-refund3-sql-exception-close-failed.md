---
title: Ops 명령으로 닫을 수 없는 환불 3번을 묵음으로 두자는 AI 안을 거부하고, 이번만 SQL 예외로 FAILED 종결함
date: 2026-11-18
updated: 2026-11-18
judge: junhyun
ai: Claude Code (배포 서버 읽기 전용 조회, ops inspect --with-pg, 코드 대조)
verdict: 거부
area: 결제
presentation: 아님
shared: 예
---

# Ops 명령으로 닫을 수 없는 환불 3번을 묵음으로 두자는 AI 안을 거부하고, 이번만 SQL 예외로 FAILED 종결함

## 맥락
- 해결하려던 작업: 배포 서버의 `RefundManualCheckAging` 심각 알림(운영자 확인 환불이 24시간 넘게 남음, 6일 경과)을 해소한다. 11/12에 강민 님이 같은 건을 조사하고 결제 담당에게 넘겼다([기록](../kangmin/2026-11-12-silence-refund-manual-check-aging.md)).
- AI 활용 방식: 알림 화면을 주고 해소와 원인 브리핑을 맡겼다.

## AI 제안
- 원인: 환불 3번(결제 137870, Mock PG, 200만 원). 11/12 16:51 KST에 승인됐고, 19:22 배포로 Mock PG가 다시 뜨면서 메모리 원장이 사라졌다. 19:32에 예매를 취소하자 환불이 `NOT_REFUNDABLE`로 거절돼 `NEEDS_MANUAL_CHECK`가 됐다. 거래 ID가 ISE-253 이전의 서명 없는 형식이라 원장을 되살릴 수 없다. 오늘(11/18) 20:29에 다시 울린 것은 20:28 배포로 결제 서비스가 다시 떠 메트릭이 잠깐 끊겼기 때문이다.
- 닫는 경로가 없다: `refund resolve`는 PG `NotFound`에서 거부한다. `--close-failed`는 PG 조회가 `RefundRejected`일 때만 허용되는데, Mock PG는 거절한 환불을 저장하지 않아 조회가 404만 준다. `refund retry`는 같은 거절로 되돌아가 경과 시간만 새로 시작한다. 상태를 바꾸는 SQL은 운영 원칙(ADR 0028, INV-7)상 금지다.
- 처음 조치: Alertmanager 묵음(env=deploy, 11/20 09:00 KST까지)만 걸고 DB는 그대로 둔다. 남은 위험으로, 묵음이 새 환불 NMC도 가린다는 점을 알렸다.
- 사용자가 삭제를 지시한 뒤 영향을 확인해 세 안을 냈다.
  - 환불 행만 삭제: 대사 RC-2(승인 결제·환불 없음·예매 취소, 가장 심각)가 걸려 대사 심각 알림이 1시간마다 울린다.
  - 거래 전체 삭제: 이력 테이블의 삭제 금지 트리거를 잠시 꺼야 하고 감사 흔적이 사라진다.
  - `deleted_at`(소프트 삭제): 게이지·대사 어디서도 보지 않아 알림이 꺼지지 않는다.
  - 추천: Ops `refund resolve --close-failed`가 쓰는 전이(`closeAsFailed`)를 SQL 한 트랜잭션으로 그대로 쓴다. 환불을 FAILED로 바꾸고, 이력 한 줄(`OPS_CLOSED`, `OPS:junhyun`)과 감사 기록(APPLIED)을 남긴다.

## 판단
- 결과: 거부(묵음만 걸고 DB는 두는 안). 원칙의 예외를 지시한 뒤 처리 방법은 AI 추천을 골랐다.
- 판단자: junhyun
- 근거: "이번에만 예외로 DB에서 자료를 삭제해줘!" 처리 방법은 선택지에서 "FAILED로 닫기(추천)"를 골랐다.
- 검토한 대안: 묵음 유지(AI 처음 조치), 환불 행만 삭제, 거래 전체 삭제

## 반영
- 배포 서버 결제 DB(2026-11-18 22:31 KST, 한 트랜잭션):
  - `refunds` 3: `NEEDS_MANUAL_CHECK` → `FAILED`. `next_check_at`은 NULL로 바꿨고, 조건부 UPDATE가 1행이 아니면 롤백하게 했다.
  - `payment_status_histories` 487634: REFUND `NEEDS_MANUAL_CHECK` → `FAILED`, 사유 `OPS_CLOSED`, actor `OPS:junhyun`.
  - `manual_action_logs` 1: command `refund resolve (SQL 예외)`, APPLIED, external_ref `MOCK-PG-LEDGER-LOST-20261112`. 승인자는 없고, 사유에 SQL 예외임을 적었다.
- 결제 137870은 APPROVED 그대로 두고 이벤트는 내지 않았다. Ops `--close-failed`와 같은 결과다.
- 실행 전 백업: 서버 `~/iseonjwa-backups/refund3-before-20261118.csv`(환불·이력·결제 행).
- 원인이 없어져서 Alertmanager 묵음 두 건(`be01cb3b`, `c6636b53`)을 만료시켜 환불 감시를 되살렸다.

## 검증
- `refund_manual_check_count`는 0, `refund_manual_check_oldest_seconds`도 0이다.
- Prometheus의 환불 알림 firing 0건, Alertmanager 알림 0건, 남은 묵음 0건이다.
- 환불 상태는 FAILED 1건, REFUNDED 60,448건이다.
- RC-7(현재 상태와 마지막 이력 대조)은 환불 FAILED와 마지막 REFUND 이력 FAILED가 같아 걸리지 않는다. RC-2는 환불 행이 있으면 FAILED여도 대상이 아니다. 둘 다 규칙 코드로 확인했고, 다음 대사 회차의 결과는 아직 보지 않았다.

## 판단 이력
- 2026-11-18 거부: 묵음만 두는 AI 조치 대신 이번만 DB 예외 처리를 지시했다.
- 2026-11-18 선택: 삭제 세 안의 영향을 본 뒤 AI 추천인 FAILED 종결을 골랐다.

## 발표·면접 포인트
- 운영 원칙에 예외를 둘 때도 "삭제"를 그대로 하지 않고, 대사 규칙(RC-2·RC-7)과 감사 트리거를 먼저 확인했다. 설계된 Ops 전이와 같은 결과를 감사 기록과 함께 남기는 쪽으로 좁혔다.
- 남은 설계 한계: PG에 기록이 없는 환불을 외부 조치 참조와 함께 닫는 Ops 경로가 없다. Mock PG는 거절한 환불을 조회로 돌려주지 않아 `--close-failed`에 닿지 못한다.
