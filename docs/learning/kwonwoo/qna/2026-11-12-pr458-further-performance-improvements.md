---
title: PR 458번과 측정 브랜치(F) 이후 성능 지표를 더 끌어올릴 방안과 트레이드오프
date: 2026-11-12
updated: 2026-11-12
asker: KWON-WOO
level: 고급
tags: [performance, seathold, seat-map, gateway, postgresql, load-shedding, cache]
---

# PR 458번과 측정 브랜치(F) 이후 성능 지표를 더 끌어올릴 방안과 트레이드오프

## 질문
PR 458번에서 성능 개선을 진행 중이고 실제 코드는 측정용 브랜치에 별도로 실려 있다. PR 458번에서 성능 지표를 더 끌어올릴 수 있는 방안들을 구체적인 내용과 각각의 트레이드오프를 포함해 제시해 달라는 요청이다.

## 짧은 답
측정 브랜치(`experiment/ISE-79-k6-steps`)의 F 조합(G1, R1, P1 풀 10, P4a~P4c, S1~S4)은 K1 기본 부하(초당 100명)를 100% 성공(좌석 조회 p95 7ms, 선점 p95 8ms)으로 통과했다. 여기서 지표를 한 단계 더 끌어올리려면, 이후 측정(CPU 4코어 상한, 매진을 피한 스트레스, 잠긴 행 집중 Z, 만료 동시 실행 X)에서 새로 드러난 병목 다섯 곳을 겨냥해야 한다.
1. **선점 트랜잭션 DB 왕복 압축과 사전 거절:** 409 재시도 증폭(전체의 77%)과 잠긴 행 번짐(초당 20건 한계), 유령 선점을 줄인다.
2. **좌석 조회 830KB 응답과 직렬화 비용 제거:** CPU 상한에서 앱 CPU의 57%를 차지하는 직렬화(P4d)와 Gateway OOMKilled를 부르는 830KB 대역폭을 줄인다.
3. **만료 스케줄러 처리량과 잠금 순서 정렬:** 부하 중 쌓이는 만료 적체(9,050건)와 결제 확정 소비자와의 역순 잠금을 없앤다.
4. **Gateway 요청당 비용 절감과 배압(Backpressure) 제어:** 640명에서 먼저 열리는 인증 차단기와 메모리 상한 도달을 막는다.
5. **PostgreSQL 저장소 튜닝:** `schedule_seats` 반복 갱신의 인덱스 비용(HOT 업데이트)과 조회 인덱스 스캔 범위를 줄인다.

## 자세히

### 1. 선점(`seathold`) 경로: DB 왕복 압축·사전 거절·유령 선점 차단 (담당 영역)

PR #458에 실린 `SyncSeatHoldService`는 S1~S3로 정합성을 확보했지만, 선점 1건당 DB 왕복이 약 10~12번 일어나고 잠긴·잡힌 좌석 요청이 DB 커넥션을 점유한 뒤에야 거절된다.

| 방안 | 구체적인 내용 | 끌어올리는 지표 | 트레이드오프 (대가와 위험) |
|---|---|---|---|
| **1-1. 좌석 조회·잠금·갱신 한 문장 통합 (`UPDATE ... RETURNING`)** | 현재 `findSeats`(SELECT)로 가격·소속을 확인한 뒤 `holdAvailableSeats`에서 서브쿼리 `FOR UPDATE` + `UPDATE`를 따로 실행한다. 이를 `UPDATE schedule_seats SET status = 'HELD', ... WHERE schedule_id = :scheduleId AND id IN (:ids) AND status = 'AVAILABLE' AND grade <> 'LOTTERY' RETURNING id, price` 한 문장으로 합친다. 반환된 행 수가 요청 좌석 수보다 적으면 롤백한다(사전 소속 검사는 캐시된 배치로 대체). | 선점 트랜잭션의 DB 왕복 1~2회 감소, 커넥션 점유 시간 단축, 고부하 시 선점 p95·p99 개선 | 회차 소속이 아닌 좌석(`SEAT_COUNT_MISMATCH`)과 이미 잡힌 좌석(`SEAT_ALREADY_HELD`)을 구분하려면 P4b 배치 캐시를 참조하거나 실패 시에만 추가 조회해야 한다. |
| **1-2. 409 응답에 충돌 좌석 ID 포함** | 1-1의 `RETURNING id` 결과와 요청 `seatIds`의 차집합으로 "이미 선점된 좌석 ID 목록"을 구해 409 응답 본문(`conflictSeatIds`)에 담아 내려준다. 프런트엔드는 전체 좌석(830KB)을 다시 조회하지 않고 해당 좌석만 비활성화한 뒤 재선택을 유도한다. | K1 매진 전 구간에서 409(약 77%) 뒤 따라오는 재조회 요청 수 자체가 줄어들어 좌석 조회 RPS와 대역폭 감소 | 프런트엔드·API 응답 계약 변경(`contract` 이슈)이 필요하다. 다른 사용자가 그사이 잡은 좌석까지는 반영하지 못해 연속 409가 일부 남을 수 있다. |
| **1-3. Redis 비트맵/Set 사전 거절 (Pre-filter) + 선점 세마포어** | 잠긴 행 집중(Z) 측정에서 `lock_timeout` 500ms(S3)만으로는 초당 20건(`풀 10 ÷ 0.5초`)을 넘길 때 커넥션 풀이 고갈되어 좌석 조회 성공률이 53.5%로 떨어졌다. 선점 성공 시 Redis(또는 로컬 캐시)에 선점 좌석을 기록해 트랜잭션 시작 전에 즉시 409로 거절하고, 선점 진입에 세마포어(예: 동시 8개, 풀 10개 중 2개는 조회·만료용으로 보호)를 둔다. | Z·K 시나리오에서 잠긴 행에 요청이 몰려도 좌석 조회·공연 목록 성공률 100% 유지(장애 격리), 409 응답 지연 수 ms 이내로 단축 | 좌석 상태가 DB와 캐시 두 곳에 존재한다. 만료·취소 시 캐시 해제 누락 위험이 있으므로 **거절(409)에만 쓰고 허용 판정은 반드시 DB 조건부 UPDATE**에 맡겨야 한다. |
| **1-4. 요청 기한 전파(`X-Request-Deadline`)로 유령 선점 방지** | Z 측정에서 클라이언트가 Gateway 3초 타임아웃(504)으로 떠난 뒤에도 서버 대기열에 남은 요청이 실행되어 아무도 받지 못한 예매(유령 선점 8~9건)가 생성됐다. Gateway가 진입 시각 + 3초를 헤더로 넘기면, `SyncSeatHoldService`가 트랜잭션 진입 직전과 커밋 직전에 남은 시간이 임계값(예: 200ms) 미만일 때 즉시 포기(롤백)한다. | 과부하 구간에서 유령 선점 0건 달성, 이미 떠난 클라이언트를 위해 쓰는 헛된 DB 트랜잭션·좌석 잠금 제거 | 서버 간 시계 오차(NTP drift)가 있으면 정상 요청을 조기 거절할 수 있다. 절대 시각 대신 경과 시간 계산이나 커넥션 획득 소요 시간(`elapsed > 2500ms`) 검사를 함께 써야 안전하다. |
| **1-5. 회차(`Schedule`) 로컬 캐시와 결제 토큰 서명 분리(P2)** | `inventory.findSchedule`이 매번 읽는 `maxPerUser`, `holdMinutes`, `openAt`, `startsAt`을 짧은 TTL 로컬 캐시로 읽어 트랜잭션 시작 전에 판매 기간을 검사한다. 또한 `paymentTokenIssuer.issue`(HMAC-SHA256 서명)와 `ReservationNo.next` 생성을 `writeTransaction.execute` 바깥으로 뺀다. | 판매 기간 외 요청의 DB 커넥션 점유 0, 트랜잭션 내부 DB 왕복 1회 감소 및 커넥션 보유 시간 단축 | 운영자가 회차 판매 시각을 긴급 변경했을 때 캐시 TTL만큼 늦게 반영된다. 토큰 서명 중 예외가 나면 좌석은 선점됐으나 응답이 실패하지만, 이미 구현된 S2 멱등 재조회(`replay`)가 복구해 준다. |
| **1-6. 매수 한도 단일 문장 Upsert + 엔티티 Sequence Batch Insert (P3)** | 현재 매수 반영은 `UPDATE` 0행 시 `SAVEPOINT` + `INSERT` + 재`UPDATE`로 첫 선점마다 최대 3번 왕복한다. 이를 `INSERT INTO user_schedule_quotas ... ON CONFLICT (user_id, schedule_id) DO UPDATE SET held_count = ... WHERE held_count + :qty <= :limit` 한 문장으로 줄인다. 또한 `Reservation`·`ReservationSeat`·`ReservationStatusHistory`의 ID 전략을 `IDENTITY`에서 `SEQUENCE`(`allocationSize = 50`)로 바꾸고 `reWriteBatchedInserts=true`를 켠다. | 첫 선점 사용자의 DB 왕복 2회 감소, 다좌석 선점 시 `ReservationSeat` 개별 INSERT 왕복이 1회 배치로 압축 | `IDENTITY`를 `SEQUENCE`로 바꾸면 Flyway/DDL 스키마 변경이 필요하다. SA 12-7의 쿼리 모양과 달라지므로 ADR과 SA 변경 기록을 남겨야 한다. |

### 2. 좌석 조회(`concert`) 경로: CPU 상한과 네트워크 대역폭 돌파 (협업: ISE-189)

측정 브랜치의 P4b·P4c는 아직 `dev`에 반영되지 않았고(현재 `dev`는 JPQL 기반 P4a만 반영), 4코어 CPU 상한 측정에서는 P4c 위에서도 160~320명 구간에 앱 CPU와 Gateway 메모리가 한계에 닿았다.

| 방안 | 구체적인 내용 | 끌어올리는 지표 | 트레이드오프 (대가와 위험) |
|---|---|---|---|
| **2-1. P4b·P4c 본 반영 + P4d(직렬화 바이트·gzip 사전 압축 캐시)** | P4c JFR 분석에서 Jackson 직렬화(32%)와 응답 객체 조립(24.5%)이 앱 CPU의 56.5%를 썼다. 1초 상태 스냅숏이 바뀔 때만 `ScheduleSeatsResponse`의 JSON `byte[]`와 gzip 압축 `byte[]`를 한 번 만들어 캐시한다. 요청마다 압축하지 않고 캐시된 압축 바이트를 그대로 내려준다. | 4코어 CPU 상한 스트레스에서 320명 이상의 좌석 조회 성공률 상승, 응답 크기(830KB → 수십 KB) 축소로 배포 환경 발생기 대역폭 한계(초당 약 230건) 및 Gateway 소켓 버퍼 급등 해소 | 컨트롤러가 공통 `SuccessResponse` 직렬화를 우회하거나 `RawJson` 래퍼를 써야 한다. 요청마다 달라지는 `traceId`·`serverTime`을 응답 헤더로 옮기거나 바이트 앞뒤만 조합해야 하므로 JSON 동등성 테스트가 필수다. |
| **2-2. `ETag`와 `304 Not Modified` 조건부 응답** | P4c의 1초 상태 스냅숏 버전(예: `scheduleId + "-" + snapshotEpochSecond` 또는 상태 배열 해시)을 `ETag` 헤더로 내려준다. 409 충돌 직후 재조회하는 클라이언트가 `If-None-Match`를 보내면 같은 1초 안에서는 본문 없이 `304 Not Modified`만 반환한다. | 재조회 요청의 응답 바이트가 830KB → 0B로 감소, Gateway 직접 버퍼·커널 소켓 버퍼 점유량 급감 | 1초가 지나 스냅숏이 갱신되면 다시 830KB 전체를 보내야 한다. k6 스크립트와 브라우저 캐시 설정(`Cache-Control: no-cache`)이 맞물려 동작하는지 검증해야 한다. |
| **2-3. 정적 배치와 동적 상태 비트맵 분리** | 좌석 배치(구역·열·번호·등급·가격)는 불변 API(또는 CDN/장기 캐시)로 분리하고, 상태 조회 API는 15,000석의 선택 가능 여부를 좌석 순번 비트맵(1,875바이트, Base64 약 2.5KB)으로만 반환한다. | 응답 크기가 830KB에서 약 2.5KB(약 330분의 1)로 줄어 직렬화 CPU, 네트워크 대역폭, Gateway OOMKilled 문제가 근본적으로 사라짐 | 프런트엔드 렌더링 구조와 API 계약을 모두 바꿔야 하는 가장 큰 변경이다. 발표 전 남은 일정 안에서 프런트엔드와 맞출 수 있는지 먼저 따져야 한다. |

### 3. 만료 스케줄러(`SeatHoldExpiry`)와 회수 경로: 적체 해소와 잠금 순서 정렬 (담당 영역)

PR #458에 포함된 `SeatHoldExpiryService`와 `SeatHoldExpiryScheduler`에서 직접 고칠 수 있는 지점이다.

| 방안 | 구체적인 내용 | 끌어올리는 지표 | 트레이드오프 (대가와 위험) |
|---|---|---|---|
| **3-1. 만료 배치 상한 확대(`100 → 1,000`) 또는 시간 예산 기반 드레인** | X 측정(만료 켬)에서 `seathold.expiry.batch-size: 100`(5초 주기, 초당 20건 상한)은 초당 50건씩 발생하는 만료를 따라잡지 못해 기한 지난 HELD가 9,050건 쌓였다. 측정 브랜치에서 1,000으로 올렸을 때 선점 p95(8ms) 영향 없이 적체가 57~269건으로 줄었다. 설정 기본값을 1,000으로 올리거나 주기 내 시간 예산(예: 3초) 동안 빌 때까지 돌게 한다. | 미결제 좌석 회수 지연이 수 분에서 약 5초 이내로 단축, 유효 판매 가능 좌석 회전율 상승 | `expireNext`는 건별 트랜잭션이므로 1,000건 처리 시 스케줄러 스레드 1개가 커넥션 1개를 연속으로 사용한다. 풀을 10으로 늘리는 설정(P1)과 함께 들어가야 선점 요청과 경합하지 않는다. |
| **3-2. 단건 만료(`expireNext`) 대신 소규모 묶음(Chunk) 만료** | 현재 `expireNext`는 `SKIP LOCKED`로 예매 1건을 집어 만료할 때마다 DB 왕복을 약 6~7번(예매 잠금, 연장 확인, 만료 UPDATE, 예매 조회, 예매 좌석 조회·해제, 회차 좌석 해제, 매수 차감, 이력 저장) 수행한다. 1,000건이면 약 6,000~7,000번 왕복이다. `SKIP LOCKED LIMIT 50`으로 묶어 한 트랜잭션에서 `IN (:reservationIds)`로 일괄 해제한다. | 만료 1,000건 처리 시 DB 왕복 수십 분의 1로 감소, 만료 주기의 DB CPU와 WAL fsync 부하 감소 | 묶음 중 한 건에서 예외가 나면 50건 전체가 롤백되어 실패 격리 단위가 커진다. 또한 여러 좌석·매수 행을 한 트랜잭션에서 잠그므로 잠금 정렬 순서를 엄격히 지켜야 데드락이 나지 않는다. |
| **3-3. 선점·만료·확정 간 전역 잠금 순서 통일** | `SyncSeatHoldService`는 `매수(quotas) → 회차 좌석(schedule_seats) → 예매(reservations)` 순으로 잠그지만, `SeatHoldExpiryService`는 `예매 → 예매 좌석 → 회차 좌석 → 매수` 역순으로 잠근다(코드 TODO R4). 같은 사용자가 한 좌석을 추가 선점하는 순간 기존 선점이 만료되면 `quotas`와 `reservations` 사이에서 교착(Deadlock) 가능성이 있다. | 만료와 선점·결제가 동시에 도는 통합 부하(O1, X1)에서 잠재적 데드락 위험 제거 | 만료 대상은 `reservations`에서 먼저 찾아야 하므로, `SKIP LOCKED`로 예매를 집은 뒤 내부 갱신 순서를 맞추거나 조건부 전이 방식을 결제 결과 소비자와 함께 맞춰야 한다. |

### 4. 인프라·Gateway·DB 설정: 시스템 상한 확장 (협업: `contract` 이슈)

| 방안 | 구체적인 내용 | 끌어올리는 지표 | 트레이드오프 (대가와 위험) |
|---|---|---|---|
| **4-1. 공유 설정 2종(`connection-timeout: 1000`, `maximum-pool-size: 10`) 본 반영** | 측정 브랜치에서 검증된 R1(대기 시한 1초)과 P1(풀 10)을 `config-repo/reservation-service.yml`에 반영한다. | 과부하 뒤 회복 불능(B8) 해결(40초 내 자동 회복), 선점 경로 커넥션 대기 40 → 0 및 p99 33ms → 6ms 단축 | 풀이 5에서 10으로 늘어나므로 인스턴스 수 × 10이 PostgreSQL `max_connections` 안에 드는지 관리해야 한다. 대기 1초 초과 시 클라이언트가 500을 빠르게 받는다. |
| **4-2. Gateway 인증 차단기 `BulkheadFullException` 분리 + 백엔드 동시 처리 상한** | 운영 차단기 값(P)에서는 Redis 오류 0건인데도 인증 벌크헤드(25) 거절이 차단기 실패로 집계되어 320명에서 차단기가 열렸다. 반대로 벌크헤드 거절을 무시한 시험 값(T)에서는 통과한 830KB 응답이 쌓여 커널 소켓 받기 버퍼(590MiB) + 직접 버퍼(183MB)로 Gateway가 `OOMKilled`됐다. 차단기에서 벌크헤드 거절은 빼되, 좌석 조회 라우트에 전체 in-flight 동시 처리 상한과 소켓 수신 버퍼 상한(`SO_RCVBUF`)을 함께 둔다. | 매진을 피한 스트레스 320~640명 구간의 Gateway 503 급증 해소 및 1,280명 구간의 Gateway `OOMKilled` 방지 | 동시 처리 상한을 넘긴 요청은 Gateway에서 즉시 503(`Retry-After`)으로 거절된다. 하지만 프로세스가 죽어 전체가 끊기는 것보다 정상 처리량을 지키는 편이 낫다. |
| **4-3. PostgreSQL `schedule_seats` `fillfactor = 80` 및 가용 좌석 부분 인덱스** | `schedule_seats`는 선점·만료·확정마다 `status`와 `updated_at`만 계속 바뀐다. 두 열이 인덱스에 걸려 있지 않다면 페이지 내 빈 공간을 쓰는 HOT(Heap-Only Tuple) 업데이트가 가능하다. `fillfactor`를 80~85로 낮추고, P4b의 `findHoldableSeatIds`를 위해 `(schedule_id, id) WHERE status = 'AVAILABLE' AND grade <> 'LOTTERY'` Index-Only Scan용 부분 인덱스를 둔다. | 선점·만료 UPDATE 시 인덱스 갱신 생략으로 쓰기 지연·autovacuum 부하 감소, 매진에 가까울수록 상태 조회 쿼리가 읽는 인덱스 크기 축소 | `fillfactor`를 낮추면 초기 테이블 디스크 사용량이 약 15~20% 늘어난다. 반면 부분 인덱스는 `status`를 조건에 포함하므로, 부분 인덱스를 걸면 `status` 변경 시 HOT 업데이트가 깨진다. 따라서 **쓰기(HOT)와 읽기(부분 인덱스) 중 하나만 선택**해야 하며, P4c(1초 캐시)가 있으면 조회 쿼리는 초당 1번뿐이므로 부분 인덱스보다 `fillfactor`를 통한 HOT 업데이트 유지가 유리하다. |

## 우선순위 제안

발표와 PR #458 마무리에 바로 도움이 되고 다른 팀 의존성이 적은 순서다.
1. **내 영역에서 바로 반영할 것:** 3-1(만료 배치 상한 1,000 반영)과 4-1(R1 커넥션 대기 1초, P1 풀 10 `contract` 제안 마무리). 이미 측정 브랜치에서 수치로 검증됐다.
2. **선점 코드 내부 개선(계약 변경 없음):** 1-1(`UPDATE ... RETURNING`으로 조회·갱신 통합), 1-4(경과 시간 검사로 유령 선점 차단), 1-5(회차 짧은 로컬 캐시·토큰 서명 분리). Z·K 시나리오로 전후 비교 수치를 바로 뽑을 수 있다.
3. **좌석 조회·Gateway 협업:** 2-1(P4b·P4c 본 반영 및 P4d + 사전 gzip), 4-2(Gateway 차단기·동시 처리 상한). 4코어 배포 환경 측정의 한계를 직접 올린다.
4. **외부 계약·스키마 변경이 따르는 것:** 1-2(409 충돌 좌석 ID 반환), 1-3(Redis 사전 거절), 1-6(매수 Upsert + Sequence 배치), 2-3(상태 비트맵). 효과는 크지만 프런트엔드 합의나 DDL 변경이 필요하므로 배포 본 측정 결과를 본 뒤 결정한다.

## 덧붙인 질문: 1-1에서 배치 캐시를 참조할 때 캐시 스탬피드(Cache Stampede)가 발생하면 문제가 생기지 않는가?

### 결론
1. **캐시 없이 해결하는 방법이 더 낫다.** 1-1에서 `SEAT_COUNT_MISMATCH`(존재하지 않거나 다른 회차의 좌석, 400)와 `SEAT_ALREADY_HELD`(이미 잡힌 좌석, 409)를 구분하려고 굳이 사전 배치 캐시를 볼 필요가 없다. **먼저 `UPDATE ... RETURNING`을 실행하고, 반환된 행 수가 요청 좌석 수보다 적을 때(실패 경로)만 `SELECT COUNT(*)`(또는 `findSeats`)로 소속 좌석 수를 확인**하면 된다.
2. 만약 사전 검증에 배치 캐시를 쓰더라도, 측정 브랜치의 `SharedLoadCache`는 `CompletableFuture` 기반 **Single-flight(단일 비행) 구조와 무기한 TTL(`ttl = null`)**로 되어 있어 일반적인 캐시 스탬피드(동시 DB 조회 폭발)는 막아 준다.
3. **다만 선점 트랜잭션 안에서 `SharedLoadCache`를 호출하면 위험하다.** 캐시가 비어 있는 첫 순간에 선점 요청들이 이미 DB 커넥션을 쥔 채 캐시 로딩 스레드를 기다리면서 **커넥션 풀 교착(Connection Pool Starvation Deadlock)**이 생길 수 있다.

### 이유 1: 캐시 스탬피드와 커넥션 풀 교착 위험
일반적인 캐시(`get → 없으면 DB 조회 → put`)는 캐시가 비어 있거나 만료된 순간 동시 요청 N개가 전부 DB로 몰리는 캐시 스탬피드를 일으킨다. 측정 브랜치의 `SharedLoadCache`는 첫 요청만 `CompletableFuture`를 넣고 나머지 요청은 `future.join()`으로 기다리게 해 DB 쿼리는 1번만 나간다.

그러나 **선점 트랜잭션(`writeTransaction.execute`) 안**에서 이 캐시를 부르면 다른 문제가 생긴다.
- HikariCP 커넥션 풀이 10개일 때, 캐시가 아직 없는 상태에서 선점 요청 10개가 동시에 트랜잭션을 시작해 커넥션 10개를 모두 쥔다.
- 이 때 배치 캐시 로더(`SeatMapReader.readLayout`)가 별도 트랜잭션이나 다른 스레드의 좌석 조회 요청을 기다려야 한다면, 로더는 커넥션을 얻지 못해 멈추고, 커넥션을 쥔 10개 스레드는 `future.join()`에서 로더를 기다리는 **데드락**에 빠진다.
- 또한 `concert` 모듈의 조회용 캐시를 `seathold` 모듈이 직접 참조하면 모듈 간 결합도도 높아진다.

### 이유 2: 캐시 의존 없이 DB 왕복도 줄이는 낙관적 진행 + 실패 시 사후 판별
정상적인 프런트엔드 흐름에서 들어오는 요청은 모두 그 회차에 실제 존재하는 좌석 ID를 보낸다. 없는 좌석 ID나 다른 회차 좌석 ID(`SEAT_COUNT_MISMATCH`, 400)가 들어오는 경우는 비정상 요청뿐이다.

따라서 사전 조회도, 캐시 참조도 하지 않고 다음 순서로 처리하는 편이 가장 깔끔하다.
1. `UPDATE schedule_seats SET status = 'HELD', ... WHERE schedule_id = :scheduleId AND id IN (:ids) AND status = 'AVAILABLE' AND grade <> 'LOTTERY' RETURNING id, price`를 바로 실행한다.
2. **성공 경로(반환 행 수 == `seatIds.size()`):** 요청한 좌석이 모두 그 회차의 소속이면서 `AVAILABLE`이었다는 뜻이 동시에 증명된다. `findSeats` 왕복 1회가 조건 없이 사라진다.
3. **실패 경로(반환 행 수 < `seatIds.size()`):** 어차피 예외를 던져 롤백할 트랜잭션이다. 이때만 `SELECT count(*) FROM schedule_seats WHERE schedule_id = :scheduleId AND id IN (:ids)`를 한 번 실행한다.
   - 개수가 `seatIds.size()`보다 적으면 `SEAT_COUNT_MISMATCH`(400)를 던진다.
   - 개수가 같으면 좌석은 존재하지만 상태가 `AVAILABLE`이 아니거나 추첨석이었다는 뜻이므로 `SEAT_ALREADY_HELD`(409)를 던진다.

이렇게 하면 **캐시 스탬피드·커넥션 교착 위험이 0**이고, `concert` 모듈 캐시에 의존하지 않으면서도 성공 경로의 DB 왕복을 줄이고, 실패 경로에서는 기존 오류 코드 계약(`400` vs `409`)을 100% 그대로 지킨다.

## 덧붙인 질문 2: 각 방안의 구체적인 단점, 그 단점의 해결 방안, 그리고 실제 손익(이득 vs 손실) 판정

모든 방안을 **"무엇이 문제인가(구체적 단점) → 어떻게 보완하는가(해결 방안) → 그래도 이득이 큰가, 손실이 큰가(최종 손익 판정)"** 기준으로 다시 검증했다. 측정 브랜치의 실제 수치(K1 L에서 409 비율 77%, 선점 단독 K1-H 800명 p99 6ms, Z 잠긴 행 집중 시 좌석 조회 53.5%, X 만료 적체 9,050건)를 판단 근거로 삼았다.

### 1. 선점(`seathold`) 경로 방안별 심층 검증

#### 1-1. 좌석 조회·잠금·갱신 통합 (`UPDATE ... RETURNING`)
- **구체적인 단점:**
  1. **사전 캐시 참조 시:** 트랜잭션 안에서 배치 캐시(`SharedLoadCache`)를 부르면 캐시 미스 순간에 선점 스레드들이 DB 커넥션을 쥔 채 캐시 로더를 기다리고, 캐시 로더는 커넥션을 얻지 못하는 **커넥션 풀 교착(Starvation Deadlock)**이 발생할 수 있다.
  2. **실패 시 사후 `COUNT` 조회 시:** K1 매진 전 구간에서는 선점 시도의 **약 77%가 409 충돌**이다. 성공(23%)에서는 왕복이 2회 → 1회로 줄지만, 실패(77%)에서는 여전히 `UPDATE`(0행) + `SELECT COUNT`(소속 확인)로 2회 왕복하고 `seat_hold_requests`와 `user_schedule_quotas` 롤백 비용도 그대로다.
  3. **2석 이상 부분 충돌 시 불필요한 잠금:** 2석을 요청했는데 1석만 `AVAILABLE`이면, `UPDATE ... RETURNING`은 1석을 실제로 갱신·잠근 뒤 행 수 불일치로 롤백한다.
- **단점 해결 방안:**
  - 배치 캐시를 전혀 쓰지 않거나, 쓰더라도 `writeTransaction.execute` 바깥(커넥션 획득 전)에서만 좌석 ID 존재 여부를 확인한다.
  - 또는 단일 SQL 안에서 CTE(`WITH target AS (SELECT id FROM schedule_seats WHERE schedule_id = :scheduleId AND id IN (:ids)), updated AS (UPDATE ... WHERE count(target) = :size RETURNING id, price) SELECT (SELECT count(*) FROM target), id, price FROM updated`)로 묶어 성공·실패 모두 DB 왕복을 정확히 1회로 고정한다.
- **손익 판정: 보류 (손실·복잡도가 이득보다 큼)**
  - **근거:** 이미 Gateway 우회 K1-H 측정에서 초당 800명(서버 초당 2,200건) 부하에서도 커넥션 대기 0, 선점 p99 6ms였다. 정상 선점의 DB 왕복 1회를 줄여 얻는 지연 단축은 약 0.3~0.5ms 수준인 반면, 네이티브 CTE 쿼리 복잡도와 오류 분기 복잡도가 커진다.

#### 1-2. 409 응답에 충돌 좌석 ID(`conflictSeatIds`) 포함
- **구체적인 단점:**
  1. **API·프런트엔드 계약 변경:** 공통 오류 응답(`ErrorResponse`) 구조를 확장하고 프런트엔드 상태 관리 코드를 고쳐야 한다(`contract` 이슈 필수).
  2. **정보 노후화(Stale UI):** 충돌한 좌석 1~2개만 알려 주면, 사용자가 고민하던 1~3초 사이에 다른 사람들이 잡은 수백 개의 다른 좌석은 화면에 여전히 선택 가능한 것으로 남는다. 결국 다음 클릭에서 **연속 409**를 맞을 확률이 높아진다.
- **단점 해결 방안:**
  - 409 응답에 충돌 좌석만 주지 않고, 서버가 이미 가지고 있는 P4c의 최신 `holdableSeatIds`(또는 변경분)를 함께 주거나 프런트엔드가 P4c(1초 캐시)가 적용된 조회 API를 부르게 둔다.
- **손익 판정: 손실이 더 큼 (비추천)**
  - **근거:** P4b·P4c가 들어가면 좌석 재조회 자체가 DB를 치지 않고 메모리에서 7ms 만에 끝난다. 재조회 1번을 아끼려고 프런트엔드 계약을 바꾸면 오히려 사용자가 낡은 좌석 화면을 보고 연속 409를 겪는 역효과가 난다.

#### 1-3. 선점 세마포어(벌크헤드) vs Redis 사전 거절 (P5)
이 항목은 성격이 다른 두 기술을 나눠서 판정해야 한다.

- **[A] 선점 진입 세마포어 (In-memory Bulkhead)**
  - **구체적인 단점:** 평상시 선점만 몰리고 조회가 없을 때도 선점이 풀 10개 중 예: 8개만 쓰고 2개는 놀게 된다. 세마포어 대기 시한을 넘기면 빠른 503/429가 나간다.
  - **단점 해결 방안:** `Semaphore(8)`에 짧은 대기 시한(예: `tryAcquire(200, MILLISECONDS)`)을 두어 순간 버스트는 흡수하고, 잠긴 행 장애(500ms 이상 지속)일 때만 초과분을 차단해 나머지 커넥션 2개를 좌석 조회와 만료 스케줄러 몫으로 남긴다.
  - **손익 판정: 이득이 압도적으로 큼 (강력 추천)**
  - **근거:** Z(잠긴 행 집중)·K(잠금 장애 주입) 측정에서 좌석 조회 성공률이 53.5%로 무너진 직접 원인이 "선점이 커넥션 10개를 다 써버리는 것"이었다. 클래스 내부에 `Semaphore` 10줄만 추가하면 외부 계약·정합성 위험 전혀 없이 장애 격리 지표(좌석 조회 성공률 53.5% → 95%+)를 끌어올릴 수 있다.

- **[B] Redis 사전 거절 (Pre-filter)**
  - **구체적인 단점:**
    1. **False Positive(억지 거절) 위험:** 만료(`SeatHoldExpiryService`)나 예매 취소(`ReservationCancel`), 또는 선점 트랜잭션 롤백 시 Redis에서 좌석 ID를 지우는 작업이 네트워크 순단으로 실패하면, DB에서는 `AVAILABLE`인데 Redis가 계속 409로 막아 **영구적으로 못 파는 좌석(유령 매진)**이 생긴다.
    2. **잠긴 행(Lock)에는 무효:** Z 시나리오처럼 아직 커밋되지 않고 **트랜잭션이 잠그고만 있는 좌석**은 완료된 선점 집합에 없으므로 Redis가 걸러내지 못한다.
  - **단점 해결 방안:** 선점 확정 시에만 Redis에 넣고 TTL을 선점 만료 시간(5분)과 같게 걸며, 만료·취소 후 커밋 뒤(`afterCommit`)에 지운다.
  - **손익 판정: 손실(정합성 위험)이 더 큼 (비추천)**
  - **근거:** 이 프로젝트의 최우선 가치는 좌석 정합성(대사 위반 0, 판매 누락 0)이다. 세마포어([A])만으로도 DB 풀 고갈은 막을 수 있는데, 굳이 Redis 이중 상태를 두어 "팔 수 있는 좌석을 못 파는" 위험을 안을 이유가 없다.

#### 1-4. 요청 기한(Deadline / 경과 시간) 검사로 유령 선점 차단
- **구체적인 단점:**
  1. **클라이언트-서버 시계 오차:** 클라이언트가 보낸 시각 헤더를 믿으면 시계가 어긋난 사용자의 요청이 전부 거절될 수 있다.
  2. **커밋 직전 포기 시 헛수고:** DB 업데이트를 다 끝내고 커밋 직전에 시한 초과로 롤백하면, 그동안 쥐고 있던 좌석 잠금과 DB CPU는 이미 소모된 뒤다.
  3. **클라이언트 수신 직후 타임아웃과의 경계:** 서버가 2.8초에 커밋하고 응답을 보냈는데 클라이언트가 3.0초에 끊으면 여전히 어긋날 수 있다.
- **단점 해결 방안:**
  - 외부 시계가 아니라 `SyncSeatHoldService.hold()` 진입 시점의 `System.nanoTime()`을 재서, ① **세마포어·커넥션 획득 직후(DB 쿼리 시작 전)** 경과 시간이 예: `1,500ms`를 넘었으면 아예 쿼리를 날리지 않고 포기하고, ② **좌석 잠금 통과 직후** 경과 시간이 `2,500ms`(Gateway 시한 3초 - 여유 500ms)를 넘었으면 롤백한다.
- **손익 판정: 이득이 훨씬 큼 (추천)**
  - **근거:** 구현이 `System.nanoTime()` 비교 몇 줄로 매우 단순하고 외부 의존성이 없다. Z 측정에서 실제로 발견된 "유령 선점 A 9건, B 8건"을 0건으로 만들었다는 명확한 트러블슈팅 전후 수치를 발표에 쓸 수 있다.

#### 1-5. 회차(`Schedule`) 로컬 캐시 + 결제 토큰 서명 분리 (P2)
- **구체적인 단점:**
  1. **회차 캐시:** 운영자가 오픈 시각(`openAt`)이나 인당 매수(`maxPerUser`)를 수정했을 때 캐시 TTL 동안 반영되지 않는다.
  2. **토큰 서명 분리:** `writeTransaction`이 커밋된 뒤 `paymentTokenIssuer.issue()`에서 예외(예: 잘못된 시크릿 키 설정)가 나면 DB에는 좌석이 `HELD`로 잡혔는데 사용자는 500을 받는다.
- **단점 해결 방안:**
  - 회차 캐시는 TTL을 1~5초로 짧게 두고, 회차 수정 API 호출 시 캐시를 비운다.
  - 토큰 서명에 필요한 값(시크릿 키, 알고리즘)은 애플리케이션 기동 시점에 검증되므로 런타임 예외 가능성이 거의 없고, 설령 실패해도 같은 `X-Idempotency-Key`로 재시도하면 `replay()`가 새 토큰을 발급해 준다.
- **손익 판정: 토큰 서명 분리는 소폭 이득(코드 이동 수준), 회차 캐시는 보류**
  - **근거:** HMAC-SHA256 서명은 수십 마이크로초라 체감 지표 변화는 작지만 트랜잭션 밖으로 빼는 것이 설계상 맞다. 반면 회차 캐시는 상태 불일치 테스트 케이스(오픈 시각 직전·직후 테스트)에 영향을 줄 수 있어 신중해야 한다.

#### 1-6. 매수 한도 단일 Upsert + 엔티티 Sequence Batch Insert (P3)
- **구체적인 단점:**
  1. **매수 Upsert의 잠금 대기 함정:** 현재 코드는 먼저 `UPDATE`를 해 보고 0행일 때만 `INSERT`를 시도한다. 만약 처음부터 `INSERT ... ON CONFLICT DO UPDATE`를 쓰면, 같은 사용자가 멀티 탭으로 동시 진입할 때 unique 인덱스에 대한 speculative insertion 잠금 경합이 매번 발생한다. 또한 이미 행이 있는 사용자의 두 번째 선점에서도 불필요한 인덱스 충돌 경로를 탄다.
  2. **Sequence 변경의 파급:** `Reservation`, `ReservationSeat`, `ReservationStatusHistory`의 PK 전략을 `IDENTITY`에서 `SEQUENCE`로 바꾸면 DDL과 시퀀스 객체 생성이 필요하고, 기존 통합 테스트의 ID 가정(`1L`부터 순차 증가)이 깨질 수 있다.
- **단점 해결 방안:**
  - 매수 반영은 현재의 "선 조건부 `UPDATE` → 0행일 때만 `INSERT ... ON CONFLICT DO NOTHING` → 재 `UPDATE`" 구조를 유지하거나, PostgreSQL 함수/CTE를 쓴다.
  - 시퀀스 변경은 `ReservationSeat`에만 국소 적용하고 `allocationSize = 50`을 둔다.
- **손익 판정: 손실(변경 비용·리스크)이 더 큼 (비추천)**
  - **근거:** 선점 1건당 평균 좌석 수는 1.5석(최대 4석)이다. 1~2석 INSERT를 배치로 묶어 줄이는 시간은 1ms 미만인데 반해, 스키마 변경과 테스트 수정 비용이 크다.

---

### 2. 좌석 조회(`concert`) 경로 방안별 심층 검증

#### 2-1. P4b·P4c 본 반영 + P4d(직렬화 바이트·사전 gzip 압축 캐시)
- **구체적인 단점:**
  1. **`traceId`·`serverTime` 정적화 문제:** 공통 응답(`SuccessResponse`)은 요청마다 고유한 `traceId`와 `serverTime`을 JSON 루트에 넣는다. 전체 JSON을 통째로 캐시하면 모든 사용자의 응답에 같은 `traceId`가 찍혀 로그 추적이 깨진다.
  2. **클라이언트 `Accept-Encoding` 미지원 가능성:** 무조건 gzip 바이트를 내려주면 압축을 요청하지 않은 클라이언트(또는 기본 설정의 단순 HTTP 클라이언트)가 깨진 바이트를 받는다.
  3. **좌석 추가·추첨석 전환 시 배치 캐시 불일치:** P4b 배치 캐시(`layoutCache`)는 만료가 없다(`ttl = null`). 회차 생성 후 좌석이 늦게 생성되거나 추첨석 등급 전환(`convertToLottery`)이 일어나면 옛 등급이 그대로 보인다.
- **단점 해결 방안:**
  1. `SuccessResponse` 바깥 틀은 그대로 두고 안쪽 `data.sections` 배열만 Jackson `@JsonRawValue`(또는 `RawValue`)로 캐시된 JSON 문자열/바이트를 끼워 넣는다. 그러면 `traceId`와 `serverTime`은 요청마다 정상 생성되면서도 15,000석 직렬화 비용(CPU 57%)은 초당 1회로 사라진다.
  2. gzip은 직접 바이트를 조작하는 대신 Spring Boot의 `server.compression.enabled=true`(min-response-size: 2KB)를 켜거나, `Accept-Encoding: gzip` 헤더 유무에 따라 분기한다.
  3. 좌석 생성(`createFromVenueSeats`)과 추첨석 전환/복원 메서드 호출 시 `layoutCache.evict(scheduleId)`를 호출한다.
- **손익 판정: 이득이 압도적으로 큼 (P4b·P4c 필수, `@JsonRawValue` 기반 P4d 강력 추천)**
  - **근거:** `dev` 브랜치에는 아직 P4a만 있어 K1 L 성공률이 약 79%에 머문다. P4b·P4c가 들어가야 100%(p95 7ms)가 되며, 4코어 배포 환경에서 CPU(직렬화 57%)와 대역폭을 동시에 아끼는 핵심 열쇠다.

#### 2-2. `ETag`와 `304 Not Modified` 조건부 응답
- **구체적인 단점:**
  1. **오픈 피크(매진 전)에는 캐시 적중률이 낮다:** 매진 전에는 초당 수십 건의 선점이 일어나 1초마다 좌석 상태가 바뀐다. 사용자가 409를 맞고 재조회할 때는 보통 1~3초의 고민 시간이 지난 뒤라, 스냅숏 버전이 이미 바뀌어 있어 결국 `200 OK`(830KB)를 다시 받는다.
  2. **k6 부하 테스트 수치가 달라지지 않는다:** k6는 브라우저처럼 자동으로 이전 응답을 캐시하고 `If-None-Match`를 보내지 않는다. 시나리오 스크립트를 고치지 않으면 측정 지표가 그대로다.
- **단점 해결 방안:**
  - 매진 직후 구간(더 이상 상태가 안 바뀌는 구간)의 폴링 부하 절감용으로만 쓰거나, `ETag` 생성을 P4d 바이트 캐시의 버전 번호로 공짜로 붙인다.
- **손익 판정: 보류 (구현은 쉬우나 피크 구간 실익이 작음)**
  - **근거:** 오픈 후 3분간의 치열한 선점 구간에서는 상태가 매초 바뀌어 304 비율이 낮다. 2-1(P4d + 압축)이 먼저다.

#### 2-3. 정적 배치와 동적 상태 비트맵 분리
- **구체적인 단점:**
  1. **좌석 순번(Index) 매핑 불일치 위험:** 서버와 프런트엔드가 15,000석의 비트 순서(예: `seatId` 오름차순 vs 구역·열·번호 정렬 순)를 1비트라도 다르게 해석하면 엉뚱한 좌석이 선택 가능/불가로 표시된다.
  2. **양쪽 코드 대공사:** 백엔드 DTO, 프런트엔드 파서, 기존 API 테스트, k6 스크립트(`readSeatMap`)를 전부 다시 짜야 한다.
- **단점 해결 방안:**
  - 기존 API는 그대로 두고 `/seats/bitmap` 엔드포인트를 별도로 추가해 점진적으로 전환한다.
- **손익 판정: 현 시점에서는 손실(일정·변경 위험)이 더 큼 (비추천)**
  - **근거:** 기술적으로는 가장 이상적(830KB → 2.5KB)이지만, 본 측정과 발표를 앞둔 시점에 프런트엔드와 k6 스크립트 계약을 동시에 깨는 위험이 너무 크다.

---

### 3. 만료 스케줄러(`SeatHoldExpiry`)와 회수 경로 방안별 심층 검증

#### 3-1. 만료 배치 상한 확대(`100 → 1,000`) 또는 시간 예산 기반 드레인
- **구체적인 단점:**
  1. **긴 주기로 인한 스케줄러 스레드 점유:** 건당 약 3~5ms가 걸리면 1,000건 처리에 3~5초가 걸린다. 그사이 스케줄러 스레드 1개가 커넥션 1개를 5초 내내 연달아 획득·반납한다.
  2. **커넥션 풀이 작을 때(5개) 선점 간섭:** 풀이 5개인 상태(`dev` 기본값)에서 만료가 1개, 좌석 조회가 1~2개를 쓰면 선점이 쓸 커넥션이 모자란다.
- **단점 해결 방안:**
  - 반드시 **4-1(Hikari 풀 5 → 10 확대)**과 세트로 반영한다.
  - 또한 단순 건수 상한(1,000건)에 더해 **주기당 최대 실행 시간 상한(예: 3.5초)**을 함께 두어, DB가 느려졌을 때 다음 5초 주기와 겹치지 않게 한다.
- **손익 판정: 이득이 압도적으로 큼 (즉시 반영 추천)**
  - **근거:** 이미 측정 브랜치 X 시나리오에서 상한 1,000 적용 시 선점 p95(8ms) 저하 없이 만료 적체가 **9,050건 → 57~269건**으로 줄고 누적 만료 처리량이 **3.9배(4,400 → 17,144건)** 오르는 것이 실증됐다. 설정값(`seathold.expiry.batch-size`)과 스케줄러 루프 조건 몇 줄만 고치면 된다.

#### 3-2. 단건 만료(`expireNext`) 대신 소규모 묶음(Chunk 50건) 일괄 만료
- **구체적인 단점:**
  1. **추첨 예매 1회 연장 분기(`lotteryHook`) 처리 복잡도:** 현재 [`SeatHoldExpiryService.expire`](file:///E:/Develop/JAVA/SPARTA_MSA/high-quality-ticketing-system/reservation-service/src/main/java/com/iseonjwa/reservation/seathold/application/SeatHoldExpiryService.java#L241-L266)는 건마다 추첨 예매인지 확인해 연장이면 만료하지 않고, 만료면 `lotteryHook.onExpired`를 부른다. 묶음 SQL로 바꾸면 일반 예매와 추첨 연장 대상, 추첨 만료 대상을 메모리에서 갈라 각각 다른 쿼리로 처리해야 한다.
  2. **실패 전파(Poison Pill):** 50건 중 1건에 데이터 이상이 있어 예외가 나면 정상인 49건도 함께 롤백된다. 현재 단건 방식은 실패한 ID만 `excludedIds`에 넣고 나머지 999건을 정상 처리한다.
  3. **다중 행 잠금 데드락 위험:** 50건의 예매가 가진 여러 회차 좌석과 여러 사용자의 매수 행을 한 트랜잭션에서 잠그면 선점 트랜잭션과 데드락이 날 확률이 급격히 높아진다.
- **단점 해결 방안:**
  - 묶음 처리 도중 예외 발생 시 단건 모드로 폴백(Fallback)하고, 모든 UPDATE 대상을 ID 순으로 정렬해 잠근다.
- **손익 판정: 손실(복잡도·데드락 위험)이 더 큼 (비추천)**
  - **근거:** 3-1(단건 그대로 상한만 1,000으로 확대)만으로도 이미 초당 50건의 만료를 거뜬히 소화했다. 잘 동작하는 실패 격리(`excludedIds`)와 추첨 훅 구조를 깨면서까지 묶음 처리를 넣을 실익이 없다.

#### 3-3. 선점·만료·확정 간 전역 잠금 순서 통일
- **구체적인 단점:**
  - 만료 스케줄러는 먼저 `reservations` 테이블에서 `SKIP LOCKED`로 만료 대상을 집어야 하므로, 트랜잭션의 첫 잠금이 무조건 `reservations` 행이 된다. 반면 선점은 `reservations` 행이 아직 없어서 `quotas → schedule_seats`를 먼저 잠근다. 따라서 한 트랜잭션 안에서는 두 경로의 잠금 순서를 완벽히 같게 만들 수 없다.
- **단점 해결 방안:**
  - 사실 지금 코드에서도 **선점(`INSERT reservations`)은 새 예매 행**을 만들고, **만료(`UPDATE reservations`)는 기존 예매 행**을 잠그므로 `reservations`에서는 서로 절대 부딪히지 않는다. 둘이 만나는 곳은 `schedule_seats`와 `user_schedule_quotas` 두 테이블뿐이다.
  - 따라서 `SeatHoldExpiryService.expire()` 안에서 **`releaseQuota(매수 차감)`를 `releaseSeats(좌석 반환)`보다 먼저 호출**하도록 두 줄의 순서만 바꾸면, 선점(`quotas → schedule_seats`)과 만료(`quotas → schedule_seats`)의 공유 자원 잠금 순서가 완벽히 일치한다.
- **손익 판정: 이득이 훨씬 큼 (코드 2줄 순서 변경으로 해결)**
  - **근거:** `SeatHoldExpiryService.java`의 258~259번째 줄(`releaseSeats`와 `releaseQuota`) 호출 순서만 `releaseQuota` → `releaseSeats`로 바꾸면 선점 경로와의 공유 테이블 잠금 순서가 `quotas → schedule_seats`로 통일되어 교착 가능성을 원천 차단한다.

---

### 4. 인프라·Gateway·DB 설정 방안별 심층 검증

#### 4-1. 공유 설정 2종(`connection-timeout: 1000`, `maximum-pool-size: 10`) 본 반영
- **구체적인 단점:**
  1. 순간적인 GC 정지나 네트워크 지터로 커넥션 획득이 1.1초 걸릴 때, 예전 같으면 1.1초 만에 200으로 성공했을 요청이 즉시 500(`CannotCreateTransactionException`)으로 실패한다.
  2. 컨테이너를 2대로 스케일아웃하면 연결 수가 20개가 된다.
- **단점 해결 방안:**
  - PostgreSQL 기본 `max_connections`는 100이고 `postgres-reservation`은 `reservation-service` 전용 DB이므로 2~4대까지 늘려도 여유가 충분하다.
- **손익 판정: 이득이 압도적으로 큼 (필수 반영)**
  - **근거:** R1이 없으면 과부하 뒤 서버가 영구 먹통(B8)이 되고, P1이 없으면 선점 p99가 33ms로 튀며 만료 스케줄러와 경합한다. 이미 실측으로 검증된 필수 설정이다.

#### 4-2. Gateway 인증 차단기 `BulkheadFullException` 제외 + 백엔드 동시 처리 상한
- **구체적인 단점:**
  - 차단기에서 벌크헤드 거절만 빼고(시험 값 T) 백엔드 동시 처리 상한을 안 걸면, 좌석 조회 830KB 응답이 동시에 수백 개씩 Gateway로 밀려들어와 커널 소켓 수신 버퍼(590MiB) + 직접 버퍼(183MB)가 터지면서 **Gateway 컨테이너가 `OOMKilled`로 죽는다**(실측 확인).
- **단점 해결 방안:**
  - 두 설정을 절대 따로 넣지 않고 **반드시 한 묶음**으로 넣는다. ① `ignore-exceptions`에 `BulkheadFullException`을 추가해 Redis가 멀쩡한데 차단기가 열리는 현상을 막고, ② 동시에 좌석 조회 라우트(또는 전체)에 In-flight 요청 수 상한 필터(예: 동시 150~200건 초과 시 즉시 503)와 `-XX:MaxDirectMemorySize=128m`을 함께 설정한다.
- **손익 판정: 묶음 적용 시 이득이 큼 / 단독 적용 시 치명적 손실**
  - **근거:** 측정 브랜치에서 시험 값(T)만 넣었을 때 OOMKilled가 나는 것을 직접 확인했으므로, 동시 처리 상한과 세트로 제안해야 한다.

#### 4-3. PostgreSQL `schedule_seats` `fillfactor = 80` vs 부분 인덱스
- **구체적인 단점:**
  1. `fillfactor = 80`을 주면 테이블 페이지의 20%를 비워 두므로 초기 디스크 사용량과 Sequential Scan 시 읽는 페이지 수가 약 25% 늘어난다.
  2. 만약 가용 좌석 조회를 빠르게 하겠다고 `CREATE INDEX ... ON schedule_seats (schedule_id, id) WHERE status = 'AVAILABLE'` **부분 인덱스를 만들면, `status`가 인덱스 컬럼이 되어버려 `status`를 바꾸는 모든 UPDATE에서 HOT(Heap-Only Tuple) 업데이트가 완전히 불가능**해진다.
- **단점 해결 방안:**
  - **부분 인덱스는 만들지 않고 `fillfactor = 80`만 적용**한다. 조회는 어차피 P4c(1초 캐시)가 초당 1회로 막아 주므로 인덱스를 더 추가할 필요가 없다.
- **손익 판정: `fillfactor = 80` 단독 적용은 소폭 이득, 부분 인덱스는 손실이 더 큼**
  - **근거:** 회차당 15,000행은 테이블 크기가 수 MB에 불과해 페이지 20% 여유로 늘어나는 메모리는 무시할 수준이지만, 선점·만료 UPDATE 시 인덱스 수정을 생략하는 HOT 효과는 쓰기 부하를 줄여 준다.

---

### 5. 최종 손익 요약표 (무엇을 취하고 무엇을 버릴까)

| 방안 | 얻는 이점 (실측·구조 근거) | 감수할 손실·위험 | 최종 판정 |
|---|---|---|---|
| **3-1. 만료 배치 상한 `100 → 1,000`** | 만료 적체 9,050건 → 57~269건 해소, 선점 p95(8ms) 악화 없음 | 커넥션 풀 10(4-1)과 함께 적용 필요 | **채택 (이득 압도적)** |
| **4-1. R1(대기 1초) + P1(풀 10) 공유 설정** | 과부하 뒤 40초 내 자동 회복, 선점 p99 33ms → 6ms | DB 연결 5개 추가 사용 | **채택 (이득 압도적)** |
| **3-3. 만료 시 `releaseQuota` → `releaseSeats` 순서 변경** | 코드 2줄 이동으로 선점과 만료의 공유 테이블 잠금 순서(`quotas → seats`) 일치 | 없음 | **채택 (무비용·고효율)** |
| **1-3[A]. 선점 진입 세마포어(벌크헤드)** | 잠긴 행 폭주(Z·K) 시 좌석 조회용 커넥션 최소 2개 보장(조회 성공률 53.5% → 95%+) | 클래스 내부 세마포어 코드 약 10줄 | **채택 (이득 큼)** |
| **1-4. `nanoTime` 경과 시간 검사로 유령 선점 차단** | 클라이언트 타임아웃 뒤 서버에서 몰래 잡히는 유령 선점(8~9건) 0건화 | 경과 시간 검사 코드 몇 줄 | **채택 (이득 큼)** |
| **2-1. P4b·P4c 본 반영 + `@JsonRawValue` P4d + gzip** | `dev` 좌석 조회 성공률 79% → 100%, 4코어 직렬화 CPU(57%) 및 830KB 대역폭 절감 | 좌석 조회 담당(ISE-189)과 협업 필요 | **채택 (협업 최우선)** |
| **4-2. Gateway 차단기 보정 + In-flight 동시 상한** | 320~640명 503 급증 및 1,280명 Gateway `OOMKilled` 동시 방어 | 동시 상한 없이 차단기만 풀면 OOM 위험 | **채택 (반드시 세트로 제안)** |
| **1-1. `UPDATE ... RETURNING` + 실패 시 사후 `COUNT`** | 정상 선점(23%)에서 DB 왕복 1회 감소(약 0.5ms 단축), 캐시 교착 없음 | 409(77%)에서는 왕복 그대로, SQL 복잡도 증가 | **보류 (실익 작음)** |
| **1-2. 409 응답에 충돌 좌석 ID 포함** | 409 직후 재조회 일부 감소 | 프런트 계약 변경 + 낡은 화면으로 연속 409 유발 | **기각 (손실이 더 큼)** |
| **1-3[B]. Redis 사전 거절 (P5)** | 409 요청의 DB 진입 차단 | 캐시 해제 누락 시 좌석 영구 판매 불가 위험 | **기각 (정합성 위험 큼)** |
| **1-6. 매수 Upsert + Sequence 배치 (P3)** | 첫 선점 및 다좌석 INSERT 왕복 소폭 감소 | 스키마 변경, 멀티 탭 Upsert 잠금 경합 증가 | **기각 (손실이 더 큼)** |
| **2-3. 상태 비트맵 분리** | 응답 크기 830KB → 2.5KB | 프런트엔드·API·k6 전면 재작성 | **기각 (일정상 위험 과대)** |
| **3-2. 묶음(Chunk) 만료 처리** | 만료 DB 왕복 횟수 감소 | 추첨 연장 분기 복잡화, 다중 행 데드락·실패 전파 | **기각 (3-1만으로 충분)** |

## 이 프로젝트에서는
- PR #458 대상 브랜치: `feat/ISE-79-seat-hold-race-condition` (`SyncSeatHoldService`, `SeatHoldExpiryService`, `SeatHoldExpiryScheduler`, `JpaSeatHoldInventoryRepository`)
- 측정 브랜치: `experiment/ISE-79-k6-steps` (`ScheduleSeatQueryService`, `SeatMapReader`, `SharedLoadCache`, `reservation-service/k6/STEPS.md`)
- 발표 요약 및 후속 과제 문서: `docs/design/reservation/k6-seathold-story.md`, `docs/design/reservation/k6-p4d-review.md`, `docs/design/reservation/k6-contract-proposals.md`
- PR #458 대상 브랜치: `feat/ISE-79-seat-hold-race-condition` (`SyncSeatHoldService`, `SeatHoldExpiryService`, `SeatHoldExpiryScheduler`, `JpaSeatHoldInventoryRepository`)
- 측정 브랜치: `experiment/ISE-79-k6-steps` (`ScheduleSeatQueryService`, `SeatMapReader`, `SharedLoadCache`, `reservation-service/k6/STEPS.md`)
- 발표 요약 및 후속 과제 문서: `docs/design/reservation/k6-seathold-story.md`, `docs/design/reservation/k6-p4d-review.md`, `docs/design/reservation/k6-contract-proposals.md`

## 면접 포인트
- **"부분 인덱스와 PostgreSQL HOT 업데이트가 왜 충돌하나?"** → HOT(Heap-Only Tuple) 업데이트는 변경되는 컬럼이 어떤 인덱스에도 포함되지 않을 때만 동작한다. `WHERE status = 'AVAILABLE'` 부분 인덱스를 만들면 `status`가 인덱스 조건에 들어가므로, 좌석 상태가 바뀔 때마다 인덱스 갱신이 발생해 HOT 최적화가 깨진다. 조회 캐시(P4c)로 SELECT가 초당 1회로 줄어든 상태라면 부분 인덱스보다 HOT 업데이트를 지키는 편이 쓰기 처리량에 유리하다.
- **"타임아웃이 난 요청이 서버에서 뒤늦게 성공하는 '유령 선점'은 어떻게 막나?"** → 클라이언트·Gateway의 타임아웃(3초)과 서버 내부의 대기 시간(Tomcat 큐 + Hikari 대기 + 잠금 대기)이 어긋나면 클라이언트가 떠난 뒤 트랜잭션이 커밋된다. 진입 시각(또는 Deadline 헤더)을 전파해 트랜잭션 시작 전과 커밋 직전에 남은 시간을 확인하고, 시한이 지났으면 롤백해 좌석이 묶이는 일을 막는다.
- **"S3(`lock_timeout`)를 넣었는데도 왜 잠긴 좌석 집중 부하에서 조회 API가 실패했나?"** → `lock_timeout` 500ms는 커넥션을 이미 획득한 뒤 DB 안에서 기다리는 시간만 묶는다. 풀 크기가 10이면 잠긴 좌석으로 초당 20건(`10 ÷ 0.5초`)만 들어와도 커넥션 10개가 전부 잠금 대기에 묶여, 잠금과 무관한 다른 API까지 커넥션을 얻지 못해 실패한다. 이를 막으려면 커넥션을 잡기 전에 세마포어(벌크헤드)나 캐시 사전 거절로 차단해야 한다.

## 참고
- 측정 브랜치 `experiment/ISE-79-k6-steps`의 `reservation-service/k6/STEPS.md`
- `docs/design/reservation/k6-seathold-story.md`, `docs/design/reservation/k6-p4d-review.md`
- 앞선 관련 노트: [K1 이후 성능 개선](2026-11-10-performance-beyond-k1-results.md), [큰 좌석 응답 극복 방안](2026-11-11-overcome-large-seat-response.md), [Gateway 부하 대응 기술](2026-11-11-gateway-load-techniques-beyond-cpu.md)
