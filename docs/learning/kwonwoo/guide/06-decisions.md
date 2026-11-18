---
title: 결정 지도 (ADR 0001~0064)
date: 2026-11-18
updated: 2026-11-18
asker: KWON-WOO
level: 중급
tags: [adr, decision, tradeoff]
---

# 결정 지도 (ADR 0001~0064)

목차: [README](README.md)

`docs/decisions/`의 ADR 64건을 영역별로 한 줄씩 묶었다. 각 줄은 "무엇을 골랐나 / 무엇을 버렸나 / 무엇을 근거로 했나"다. 자세한 내용은 번호를 눌러 원문을 본다. 2026-11-18 기준이다.

## 읽는 법

- 상태: 채택(확정), 제안(담당 결정 뒤 팀 확인 대기), 대체됨, 철회. "제안"은 코드에 들어갔더라도 팀 확인 절차가 남은 것이다. 발표나 면접에서 "확정"이라고 말하지 않는다.
- 근거 칸에 수치가 없으면 원문에도 측정이 없는 결정이다. 0024, 0029, 0039의 숫자는 측정이 아니라 가정값이다.
- 결정 대부분은 Notion SA보다 저장소 기록이 우선한다(`AGENTS.md` 대전제 4). SA를 바꾼 결정은 6절에 모았다.

## 1. 플랫폼과 개발 기반

| ADR | 결정 | 버린 대안과 이유 | 근거 | 상태 |
|---|---|---|---|---|
| [0001](../../../decisions/0001-java-21.md) | Java 21 | Java 25: 사용자가 21로 바꿈(이유 미기재) | Boot 4.1.2 지원 범위 | 채택 |
| [0003](../../../decisions/0003-config-server-native.md) | 같은 저장소 `config-repo/`를 native Config Server로 | 별도 Git 설정 저장소: 접근 정보 없이 개발하려고. Config 제외: 설정 통합 의견 | - | 채택 |
| [0004](../../../decisions/0004-workspace-auth-bootstrap.md) | 전체 워크스페이스와 M1 인증 한 번에 구축 | 공통 라이브러리만: 범위 부족 | - | 채택(일부 0013·0014가 대체) |
| [0011](../../../decisions/0011-junit-verification-boundary.md) → [0012](../../../decisions/0012-java-gradle-workspace-tools.md) | 검증과 개발 도구를 Java·Gradle로 통일, Python 제거 | Python 유지: 도구가 둘로 갈림 | JUnit 124개 등 통과 | 0012 채택 |
| [0013](../../../decisions/0013-single-common-module.md) | 공통 모듈은 `common` 하나, 메시징은 `@Import`로 | SA의 4모듈 분리: 관리 비용 | 의존을 api로 바꾸면 테스트가 실패하는지 확인 | 채택 |
| [0014](../../../decisions/0014-package-name-com-iseonjwa.md) | 패키지 `com.iseonjwa` | `iseonjwa.*`: 자바 관례와 다름 | - | 채택 |
| [0030](../../../decisions/0030-table-naming-plural.md) | 테이블 snake_case 복수형 | 단수형: `user` 같은 예약어 예외가 생김 | - | 제안 |
| [0043](../../../decisions/0043-inbound-adapters-in-presentation.md) | Kafka 소비자·스케줄러 같은 입구는 presentation 계층 | infrastructure에 두기(AI 제안): 의존 방향이 다른 두 종류가 섞임 | - | 채택 |
| [0063](../../../decisions/0063-swagger-ui-at-gateway.md) | Swagger UI는 Gateway `/api/docs` 한 곳 | 서비스마다 UI: Gateway 인증을 건너뜀 | Gateway 메모리 여유 | 채택 |

## 2. 인증과 Gateway

| ADR | 결정 | 버린 대안과 이유 | 근거 | 상태 |
|---|---|---|---|---|
| [0005](../../../decisions/0005-auth-redis-fail-closed.md) | 인증 Redis 장애면 503(fail-closed), 기동 때 PING 예열 | fail-open: 로그아웃한 토큰이 계속 통함 | 기동 직후 첫 요청 503을 예열로 해결 | 채택 |
| [0006](../../../decisions/0006-gateway-single-access-policy.md) | 경로별 인증 판정은 Gateway `AccessPolicy` 한 곳 | 공유 상수(AI 제안): 판정 지점이 여전히 둘 | - | 채택 |
| [0007](../../../decisions/0007-login-lockout-admin-reset.md) | 로그인 5회 실패 잠금, 관리자 초기화로만 해제 | Redis 카운터: 장애면 잠금이 사라짐 | 통합 테스트 20개 | 채택 |
| [0008](../../../decisions/0008-internal-trust-and-auth-design.md) | Gateway가 JWT 검증, 서비스는 헤더 신뢰. `/internal/**` 외부 404 | 서비스 직접 검증·RS256: SA "MVP 이후"와 충돌 | 위협 모델 T1~T7 | 설계 중 |
| [0009](../../../decisions/0009-service-access-jwt-verification.md) | 서비스가 JWT 직접 검증 | HS256이면 Gateway도 키를 가져 위조를 못 막음 | - | 철회 |
| [0010](../../../decisions/0010-auth-session-serialization.md) | 세션 변경을 사용자 행 잠금으로 직렬화 | synchronized: 인스턴스 사이에서 안 됨 | 수정 전 경합 테스트 실패 → 통과 | 채택 |
| [0050](../../../decisions/0050-gateway-auth-redis-breaker-bulkhead-split.md) | `auth-redis` 차단기는 Redis 장애만 세고, 과부하는 벌크헤드(50)가 거절 | 거절을 실패로 세기: 과부하 때 인증 전체가 503 | Redis CPU 8~17%인데 차단기가 열림, 1차 Q2 503 98.5% | 채택 |

## 3. 대기열

| ADR | 결정 | 버린 대안과 이유 | 근거 | 상태 |
|---|---|---|---|---|
| [0015](../../../decisions/0015-queue-admission-guards.md) | 입장 Lua에 `lastTick`, `admitted ≤ seq`, 발급 기록 | 발급 뒤 대기열에 남기기: 토큰이 계속 새로 발급됨 | - | 제안 |
| [0031](../../../decisions/0031-queue-token-api-and-ready-status.md) | 입장 토큰은 토큰 API에서만, 상태 WAITING·READY·ADMITTED, 판정은 Lua | 순번 조회에서 발급: 폴링 GET이 쓰기를 함 | 폴링 3~10초 + jitter | 제안 |
| [0053](../../../decisions/0053-entry-token-consume-on-hold.md) | 입장 토큰은 선점 성공 때 소모, DB 고유 제약으로 확인 | 1회 복원(AI 추천): 복잡. 리스너로 정리: 커넥션을 더 쥠 | - | 채택 |

## 4. 좌석 선점과 좌석 조회

| ADR | 결정 | 버린 대안과 이유 | 근거 | 상태 |
|---|---|---|---|---|
| [0032](../../../decisions/0032-seat-hold-result-and-idempotency-contract.md) | 선점 응답에 seatIds, 동기형 실패는 전체 롤백, 같은 키 재요청 규칙 고정 | 실패도 커밋: 실패마다 INSERT로 WAL 급증 | - | 채택 |
| [0034](../../../decisions/0034-seathold-unidirectional-module-boundary.md) | seathold 패키지 분리, 의존은 seathold → reservation 한 방향 | quota를 seathold에: 순환 참조 | - | 제안 |
| [0035](../../../decisions/0035-defer-seathold-concurrency-and-reconciliation-to-m4.md) | 동시성 방어는 M4에서 결함을 재현·측정한 뒤 | 처음부터 전부: Before/After 근거가 없음 | - | 채택 |
| [0054](../../../decisions/0054-seat-layout-local-cache.md) | 좌석 배치 캐시는 Redis가 아니라 서비스 메모리 | Redis(SA 원안): 요청마다 약 1MB 역직렬화 | p95 7.0ms 대 38.3ms, 건당 CPU 약 4.5배 | 제안 |
| [0056](../../../decisions/0056-async-seat-hold-key-for-mixed-sections.md) | 접수형 키 `{scheduleId}:{section}`, 구역이 섞이면 가장 작은 구역 | 섞이면 400(AI 첫 추천): 일행 좌석 부분 성공 위험. 회차 키: 회차 전체가 한 줄 | 키당 초당 약 2건(계산) | 채택 |
| [0057](../../../decisions/0057-async-seat-hold-intake-and-mode.md) | 접수형은 잡힌 좌석을 즉시 409, 모드는 기동 때, 결과 조회는 늘 열림 | 모두 202로 받기: 요청의 87%가 헛되이 줄을 씀 | K1-H 409가 201+409의 87% | 채택 |
| [0058](../../../decisions/0058-sync-replay-of-async-requests.md) | 접수형으로 시작한 요청은 동기형 서버도 202로 | 409: 사용자가 모르는 예매가 생김 | - | 채택 |
| [0059](../../../decisions/0059-seat-auto-assign-skip-locked.md) | 자동 배정 API, `FOR UPDATE SKIP LOCKED` | Redis 좌석 풀: 좌석 상태가 두 곳. 연석 보장: 순환 의존 | 상한 실험 확정 +33.7%. 배포 1회 433명(인덱스 없음) | 제안 |
| [0060](../../../decisions/0060-seed-venue-1500-seats.md) | 측정·시연 시드 1,500석 | 공연장 새로 추가: venueId 1 참조를 모두 바꿔야 함 | 15,000석 응답 약 830KB가 4코어를 채움 | 제안 |
| [0061](../../../decisions/0061-seat-hold-lock-timeout-50ms.md) | 잠금 대기 500ms → 50ms, SKIP LOCKED는 안 씀 | SKIP LOCKED(AI 첫 추천): C2 성공 83→56 | C3 최대 대기 643 → 171~225ms | 채택 |
| [0062](../../../decisions/0062-seat-hold-structure-precheck-reorder-limit.md) | 먼저 거절, 좌석 UPDATE를 끝으로, 동시 처리 상한(운영에서는 끔) | 풀만 늘리기: 잠긴 좌석 대기가 풀을 쥐는 구조는 그대로 | 먼저 거절 처리량 +65%. 상한은 배포에서 503 32~58% | 채택 |

## 5. 예매·결제·추첨

| ADR | 결정 | 버린 대안과 이유 | 근거 | 상태 |
|---|---|---|---|---|
| [0016](../../../decisions/0016-payment-declined-token-reuse.md) | 거절된 결제 토큰 재사용을 결제·예매 양쪽에서 막음 | 예매 쪽 환불만: 불필요한 승인·환불 | - | 제안 |
| [0017](../../../decisions/0017-payment-idempotency-in-progress.md) | 처리 중인 멱등키는 202 + 기존 paymentId | 409 IN_PROGRESS: 클라이언트가 paymentId를 못 얻음 | - | 제안 |
| [0018](../../../decisions/0018-payment-pg-permit-before-tx1.md) | PG 허가를 TX1 앞에서, 승인·복구 그룹 분리 | 허가 실패를 DECLINED로: 장애로 사용자가 좌석을 잃음 | - | 제안 |
| [0019](../../../decisions/0019-payment-new-key-existing-payment.md) | 같은 예매에 새 키면 기존 결제로 응답, 새 키는 별칭 | 항상 409: 흔한 중복 클릭이 에러로 보임 | - | 제안 |
| [0020](../../../decisions/0020-payment-refund-dlq-manual-check.md) | 환불은 DB에 저장하고 워커 한 곳이 PG 호출 | 소비자가 직접 PG 호출: 파티션 점유, 중복 호출 | - | 제안 |
| [0021](../../../decisions/0021-payment-object-level-authorization.md) | 남의 결제는 404 | 403: 결제가 있다는 사실이 드러남 | - | 제안 |
| [0022](../../../decisions/0022-outbox-retry-and-retention.md) | Outbox 계속 재시도, 실제로 바뀐 전이만 이벤트 | 횟수 제한 뒤 FAILED: 수동 복구가 늘어남 | - | 제안 |
| [0023](../../../decisions/0023-payment-pg-client-port.md) | PgClient 포트 + 계약 테스트, Mock·토스 어댑터, 확실할 때만 Mock 폴백 | 계약 테스트 없음: 돈이 걸린 경로에 부족 | - | 제안 |
| [0024](../../../decisions/0024-payment-observability-metrics.md) | 결제 핵심 지표, 대시보드 1장, 금전 정합성 알림 | 대시보드를 나중으로: 미확정 금전 상태를 놓침 | 가정값 | 제안 |
| [0025](../../../decisions/0025-payment-token-secret-injection.md) | 결제 토큰 키는 환경변수, 기동 때 검증 | Config Server: Git이라 비밀값을 둘 수 없음 | - | 제안(키 부분 0055가 대체) |
| [0026](../../../decisions/0026-payment-one-per-reservation.md) | 예매당 결제 1건, `UNIQUE(reservation_id)` | 부분 유니크: 조회와 쓰기 사이 경합 | - | 제안 |
| [0027](../../../decisions/0027-reservation-payment-event-contract.md) | 결제 이벤트를 예매 원장과 대조해 상태별로 처리 | 결제 서비스 동기 조회: 결합, 코레오그래피와 어긋남 | - | 채택 |
| [0028](../../../decisions/0028-payment-ops-commands.md) | 운영 복구는 감사되는 Ops 명령만, 4-eyes·dry-run | 관리자 HTTP API: 외부 노출, 토큰 탈취 위험 | - | 제안 |
| [0029](../../../decisions/0029-payment-reservation-reconciliation.md) | 결제가 5분마다 예매 내부 API로 대사, 기록·알림만 | DB 직접 조회: 서비스 DB 경계를 깸 | 가정값 | 제안 |
| [0042](../../../decisions/0042-billing-key-aes-gcm-env-secret.md) | 빌링키 AES-256-GCM, 키는 환경변수 | pgcrypto: 키가 SQL 로그에 남을 수 있음 | - | 제안 |
| [0048](../../../decisions/0048-payment-tx1-commit-response-loss.md) | TX1 커밋 응답 유실은 DECLINED(NOT_SENT)로 닫는 한계로 둠 | 재시도가 이어받기: 승인이 두 번 갈 수 있음 | - | 채택 |
| [0055](../../../decisions/0055-payment-token-asymmetric-signature.md) | 결제 토큰 ES256, 개인키는 예매에만 | HS256 유지: 결제 서비스가 서명할 수 있는 키를 가짐 | 검증 평균 278.8µs(HS256 8.1µs) | 제안 |
| [0036](../../../decisions/0036-lottery-direction-measurement.md) | 추첨 유지, 측정 시나리오 3개 먼저 | 쿠폰 전환: 좌석 선점과 주제가 겹침 | 응모 p95 10.58ms, 자동결제 10분 내 100% | 제안 |
| [0037](../../../decisions/0037-lottery-seat-grade-split.md) | 추첨석은 S석에서 떼어 등급 LOTTERY | 구분 컬럼(AI 추천): 한 등급만 써서 이득이 작음 | - | 제안 |
| [0038](../../../decisions/0038-lottery-payment-failure-by-reason.md) | 자동결제 실패는 사유별, NOT_SENT만 재시도 | 모두 승계: 우리 장애로 당첨자가 자리를 잃음 | - | 제안 |
| [0039](../../../decisions/0039-lottery-billing-shared-approve-group.md) → [0051](../../../decisions/0051-lottery-billing-consumer-concurrency-and-billing-bulkhead.md) | 소비자 3, 전용 허가 `pg-billing` 3 | 소비자만 늘리고 그룹 공유: 일반 결제 503 약 27% | 10분 내 92~93% → 100% | 0051 채택 |
| [0041](../../../decisions/0041-lottery-seed-bytea-32.md) | 추첨 시드 BYTEA 32바이트 | BIGINT: 시드 공간이 2^64로 줄어듦 | SHA-256 순위 | 채택 |
| [0064](../../../decisions/0064-reservation-db-pool-keep-5.md) | 예매 DB 풀 5 유지 | 풀 10: 커넥션 보유 시간 2배, 선점 p95 1.06→1.83초(1회). 로컬 결과로 정하기: CPU 포화를 재현 못 함 | 개선 뒤 풀 5에서 대기 0 | 채택 |

## 6. 배포·관측·측정·기타

| ADR | 결정 | 버린 대안과 이유 | 근거 | 상태 |
|---|---|---|---|---|
| [0040](../../../decisions/0040-frontend-react-spa-in-monorepo.md) | 프론트는 같은 저장소 React SPA, nginx가 `/api/` 중계 | Next.js: Node 서버 필요, 검색 노출 이점 없음. Gateway 내장: 측정 대상 JVM에 부담 | 같은 출처라 CORS 설정 없음 | 채택 |
| [0044](../../../decisions/0044-deploy-actions-ghcr-jenkins.md) | Actions가 GHCR에 이미지, 별도 EC2 Jenkins가 배포 | EC2에서 빌드: 5~10분, 서비스와 CPU 경쟁 | - | 제안 |
| [0045](../../../decisions/0045-logs-loki-alerts-slack.md) | Alloy→Loki 로그, Alertmanager→슬랙 | ELK: 약 2GB 더 듦 | 결제 알림 규칙 22개가 보낼 곳이 없었음 | 제안 |
| [0046](../../../decisions/0046-load-test-k6.md) | k6를 같은 리전 별도 EC2에서, 결과는 Prometheus로 | 노트북 실행: 네트워크·노트북 성능이 섞임 | - | 제안 |
| [0047](../../../decisions/0047-single-ec2-first-managed-split-review.md) | EC2 한 대에 전부, 매니지드 분리는 검토만 | 처음부터 분리: 이틀 안에 어렵고 비용 증가 | 하루 약 6.8달러 | 채택 |
| [0049](../../../decisions/0049-assistant-service-claude-api.md) | AI 상담은 별도 서비스, 키워드 검색 + Claude, 장애면 검색 모드 | pgvector: 키·메모리·구현 기간 추가 | 질문당 약 $0.0005(가정) | 채택 |
| [0052](../../../decisions/0052-request-log-problems-only-in-operation.md) | 운영 요청 로그는 5xx·끊김·200ms 이상만 | 운영에서 끄기: 실패 요청도 못 찾음 | Gateway CPU 78→66%, 성공 처리량 1,814→2,122/s | 채택 |
| [0033](../../../decisions/0033-venue-seat-row-no-int.md) | 좌석 열 번호는 정수 | 문자열: 1, 10, 11, 2 순서로 정렬됨 | - | 제안 |

## 7. 바뀐 결정 읽기

결정이 바뀐 자리는 앞선 결정을 지우지 않고 상태와 이력으로 남겼다. 처음 보는 사람은 아래 줄기 다섯 개만 알면 대부분 따라갈 수 있다.

1. 좌석 선점 방어: 0035(나중에 측정하고 넣자) → 0061(잠금 50ms) → 0062(먼저 거절, 상한) → 0064(풀 5 유지). 각 단계가 앞 단계 측정 결과를 받아 정했다.
2. 결제 토큰: 0025(공유 비밀) → 0055(ES256). 검증하는 쪽이 서명 키를 갖지 않게 했다.
3. 추첨 자동결제: 0039(일반 결제와 같은 허가 그룹, 측정 뒤 나누기로 함) → 0051(측정 결과로 분리).
4. 요청 로그: 0045(요청마다 한 줄) → 0052(운영은 문제 요청만). Gateway CPU 측정이 근거다.
5. 결제 멱등과 1건 규칙: 0016·0017·0019를 0026(`UNIQUE(reservation_id)`)에 맞춰 함께 고쳤다.

### SA를 대체한 결정

0005(인증 fail-open → fail-closed), 0040(정적 HTML → React SPA), 0050(Gateway Redis 값), 0053(입장 토큰 1회용 불가 → 선점 때 소모), 0055(결제 토큰 HMAC → ES256), 0060(15,000석 시드 → 1,500석), 0061(잠금 500ms → 50ms).

## 면접 포인트

- "ADR을 왜 썼나" → 되돌리기 어려운 선택의 이유를 코드와 같은 저장소에 남겨, 결정이 바뀔 때 무엇이 바뀌었고 왜인지 PR로 리뷰하려고 했다. 버린 대안과 이유를 함께 적어 같은 논의를 반복하지 않았다.
- "AI 제안을 거부한 결정은" → 0061(SKIP LOCKED를 측정 뒤 거부), 0037(구분 컬럼 대신 등급 분리), 0003(Config Server를 빼자는 제안 거부), 0053(1회 복원 대신 단순한 소모).
