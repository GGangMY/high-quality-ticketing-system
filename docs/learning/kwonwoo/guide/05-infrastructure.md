---
title: 인프라 구성과 배포·관측
date: 2026-11-18
updated: 2026-11-18
asker: KWON-WOO
level: 중급
tags: [infra, docker-compose, kafka, redis, postgresql, jenkins, prometheus, grafana]
---

# 인프라 구성과 배포·관측

목차: [README](README.md)

2026-11-18 `dev`(병합 커밋 `7fef096a`) 기준이다. 서버 주소와 비밀값은 적지 않는다. 접속 방법은 [`docs/guides/deploy-server-access.md`](../../../guides/deploy-server-access.md)를 본다.

## 1. 한 장 그림

> 비유: 건물 한 채(EC2 한 대)에 부서(서비스) 8개와 공용 설비(DB·Redis·Kafka·관측 도구)가 함께 들어 있다. 정문(nginx)은 하나이고, 안내 데스크(Gateway)를 거쳐야 부서로 간다. 본사(GitHub)가 새 설계도(이미지)를 내면 시설 관리자(Jenkins)가 건물을 고친다.

```
[GitHub] --main push--> [Actions images.yml] --push--> [GHCR ghcr.io/iseonjwa/*:<커밋 SHA>]
    ^ SCM 폴링                                                   | pull
[Jenkins EC2 t3.small] --SSH(사설 IP) deploy.sh--> +------------v--------------------------------------+
                                                   | 배포 EC2 m7i.xlarge (4 vCPU, 16GB) docker compose |
 브라우저 --443--> [frontend nginx] --/api/--> [gateway :8080] --lb://--> user :8081        -> postgres-user
                     \--/grafana/--> [grafana]      |                     reservation :8082 -> postgres-reservation
 k6 발생기 c6i.xlarge --8080(사설, 측정 때만)--------+                     payment :8083     -> postgres-payment
                                                   |  Redis <- gateway·user·reservation      payment -> mock-pg / Toss
                                                   |  reservation <== Kafka(KRaft 1대) ==> payment
                                                   |  assistant :8095 -> Claude API
                                                   |  config-server :8888, eureka :8761
                                                   |  prometheus, grafana, loki, alloy, alertmanager -> Slack, zipkin
                                                   +-----------------------------------------------------+
```

## 2. 서비스

공통 버전은 Java 21, Spring Boot 4.1.2, Spring Cloud 2025.1.4다(`build.gradle`). 모듈은 `settings.gradle`에 있다. 앱마다 관리 포트 9080을 따로 열어 `/actuator/health`, `/actuator/prometheus`를 낸다.

| 서비스 | 포트 | 하는 일 | 저장소 | 스택 |
|---|---|---|---|---|
| gateway | 8080 | 단일 진입점. 경로별 인증, JWT·입장 토큰 검증, 동시 처리 상한 64, Swagger UI | Redis(블랙리스트) | WebFlux, Spring Cloud Gateway |
| user-service | 8081 | 회원, 로그인, 세션, 로그인 잠금 | PostgreSQL `user`, Redis | MVC, JPA, Flyway |
| reservation-service | 8082 | 공연·회차·좌석, 대기열, 좌석 선점, 예매, 추첨. 입장 토큰·결제 토큰 발급 | PostgreSQL `reservation`, Redis, Kafka | MVC, JPA, Flyway. 커넥션 풀 5 |
| payment-service | 8083 | 결제, 환불, 빌링키 자동결제, 대사, 운영 명령 | PostgreSQL `payment`, Kafka | MVC, JPA, Flyway, Resilience4j. 커넥션 풀 20 |
| mock-pg | 8090 | 외부 PG 흉내, 장애 주입, 원장 | 없음 | MVC |
| assistant-service | 8095 | AI 상담. Claude API, 키가 없으면 문서 검색으로 답함 | 없음 | MVC |
| config-server | 8888 | `config-repo/` 폴더를 읽어 설정 배포 | 없음 | Config Server(native) |
| eureka | 8761 | 서비스 등록·조회 | 없음 | Eureka |
| frontend | 80·443 | React SPA 정적 파일, `/api/`를 Gateway로 중계 | 없음 | nginx |

### 왜 서비스가 셋(user·reservation·payment)뿐인가

처음 SA 안은 대기열과 추첨도 서비스로 나누는 5개 구성이었다. AI 교차 검토와 팀 논의에서 둘 다 reservation 안의 모듈로 합쳤다(`docs/sa-review/01-sa-1st-review.md`, SA MASTER 14장 #1).

- 추첨: 당첨 선점이 일반 선점과 같은 좌석 행을 한 트랜잭션에서 바꾼다. 나누면 분산 트랜잭션이 된다.
- 대기열: 자기 데이터가 Redis 카운터뿐이고, 멈추면 예매도 멈춘다. 떼어 내도 장애가 격리되지 않는다. AI는 분리를 권했지만 이 근거로 거부했다.
- 결제: 돈과 외부 PG를 다루고 실패 양상이 달라 따로 뒀다.

## 3. 인프라 컨테이너

| 구성 | 값 | 고른 이유 |
|---|---|---|
| PostgreSQL 17 × 3 | 서비스마다 컨테이너 하나(user, reservation, payment) | Database per Service. 다른 서비스 테이블을 직접 읽지 못하게 물리적으로 막는다 |
| Redis 8 | 1대, AOF 켬, `noeviction` | 대기열 순번과 인증 블랙리스트. 메모리가 차도 키를 몰래 지우면 순번이 사라지므로 차라리 쓰기를 거절하게 했다 |
| Kafka 4.1.1 | 브로커 1대, KRaft(ZooKeeper 없음), 복제 1 | 결제 결과·명령과 접수형 선점 전달. 장비가 한 대라 복제를 늘려도 장애 격리가 안 된다(한계로 기록) |
| Config Server | native 프로필, 저장소 안 `config-repo/` | 서비스 설정 파일을 한 곳에 모은다. 같은 저장소 폴더라 설정 변경도 PR로 리뷰하고, 별도 설정 저장소가 필요 없다(ADR 0003). AI는 "서비스 3개에 과하고 기동 순서 문제가 는다"며 `.env`+프로필을 권했지만, 설정 파일을 통합하자는 팀 의견으로 거부했다(`docs/ai-judgments/kangmin/2026-10-26-config-server.md`). 대가로 설정을 바꾸면 해당 앱을 재시작해야 한다 |
| Eureka | 1대 | Gateway가 `lb://서비스명`으로 부른다. 배포에서는 조회 주기와 LoadBalancer 캐시를 5초로 줄였다(ISE-244) |

기동 순서는 config-server(healthy) → eureka → 나머지다. 앱은 `spring.config.import`로 Config Server를 읽고, 못 읽으면 기동을 멈춘다(fail-fast).

### Kafka 토픽

배포에서 쓰는 토픽은 6개다. 근거 전체는 [`docs/presentation/performance/2026-11-16-kafka-topics-partitions.md`](../../../presentation/performance/2026-11-16-kafka-topics-partitions.md)에 있다.

| 토픽 | 보내는 곳 → 받는 곳 | 키 | 파티션 | 이유 |
|---|---|---|---|---|
| `seat-hold.request` | reservation → reservation(접수형 선점) | `{scheduleId}:{section}` | 6 | 같은 구역 요청을 한 줄로 세워 행 잠금 경합을 줄인다. 회차만 키로 쓰면 인기 회차가 소비자 하나에 묶인다(ADR 0056) |
| `payment.command` | reservation → payment(환불, 자동결제) | `reservationId` | 3 | 소비자가 PG 응답을 기다리는 동안 다른 명령이 멈췄다. 1개일 때 자동결제가 초당 3.2건에 그쳐 3으로 올렸다(ADR 0051) |
| `payment.result` | payment → reservation(결제 결과) | `reservationId` | 1(자동 생성) | 같은 예매의 결과 순서를 지킨다. 파티션 수를 정한 기록은 없다 |
| `*.dlq` 3개 | 공통 오류 처리기 | 원래 키 | 1(자동 생성) | 처리 못 한 메시지를 버리지 않고 모은다 |

## 4. 컨테이너 메모리와 JVM

배포(`compose.deploy.yml`)는 컨테이너마다 메모리 상한을 걸고 G1 GC를 명시한다. 상한 합계는 약 13,504MiB로 장비 메모리 15,701MiB의 86%다. 메모리 예산 표는 [`docs/design/infra/deployment.md`](../../../design/infra/deployment.md)에 있다.

| 컨테이너 | 배포 메모리 상한 | JVM 힙 |
|---|---|---|
| gateway | 1024m | 256m~512m, Direct 128m |
| reservation-service | 1152m | 384m~768m |
| payment-service | 1024m | 256m~512m, Metaspace·CodeCache·Direct 상한 |
| user-service | 640m | 192m~384m |
| postgres-reservation | 1024m | - |
| kafka | 1536m | 512m~1g |

왜 G1을 명시하나: 컨테이너 메모리가 약 1,792MB보다 작으면 JVM이 Serial GC를 고른다. Serial GC는 스레드 하나로 청소하며 앱을 오래 멈춘다. local 측정에서 부하 시간의 약 75%가 GC 정지였다(ISE-193, [04 부하 테스트](04-load-test.md) 3절).

왜 힙 밖 메모리까지 상한을 거나: payment-service가 힙은 여유가 있는데 하루 5번 죽었다. 원인은 Metaspace·스레드 스택·Direct 버퍼 같은 힙 밖 메모리가 cgroup 상한을 넘은 것이었다(TS-71). 힙 상한만으로는 컨테이너 총량을 지킬 수 없다.

## 5. 로컬과 배포의 차이

| 항목 | 로컬 `compose.yml` | 배포 `+ compose.deploy.yml` |
|---|---|---|
| 이미지 | 루트 `Dockerfile`로 직접 빌드 | `ghcr.io/iseonjwa/<서비스>:<40자 SHA>`를 받기만 함(`build: !reset null`) |
| 프로필 | `local` | `prod`. mock-pg만 장애 주입 API를 열려고 `loadtest` |
| JVM | 힙 64m~256m, GC 지정 없음 | 서비스별 힙, G1 명시 |
| 외부 포트 | 127.0.0.1에만 | nginx 80·443. Gateway 8080은 보안 그룹이 부하 발생기에만 연다. 관리 UI는 SSH 터널로만 |
| 추적 샘플링 | 0.1 | 1.0(시연용), 측정 모드는 0.01 |
| 재시작 | 없음 | `unless-stopped`, 로그 20m×5 |

측정할 때는 `loadtest/deploy/compose.measure.yml`을 더한다. Prometheus가 k6 결과를 remote write로 받고 추적 샘플링을 낮춘다.

## 6. 배포 파이프라인

> 비유: 본사가 설계도를 확정(main 병합)하면 공장(Actions)이 부품(이미지)을 만들어 창고(GHCR)에 넣는다. 시설 관리자(Jenkins)가 창고를 주기적으로 보고, 새 부품이 다 오면 건물에 가서 교체한다. 교체 뒤 점검(스모크)에 실패하면 직전 부품으로 되돌린다.

1. 기능 브랜치 → `dev` PR → `dev` → `main` 릴리스 PR. main 병합이 곧 릴리스다.
2. GitHub Actions: PR과 push마다 `./gradlew verifyWorkspace`(`build.yml`). main push 때 `images.yml`이 이미지 9개(앱 8, frontend 1)를 커밋 SHA 태그로 GHCR에 올린다. `latest` 태그는 쓰지 않는다.
3. Jenkins(별도 EC2)가 main을 SCM 폴링한다. 웹훅을 쓰지 않는 이유는 Jenkins를 인터넷에 공개하지 않기 위해서다(ADR 0044).
4. 이미지 9개가 GHCR에 다 올라올 때까지 30초마다 확인하고 최대 20분 기다린다.
5. 배포 EC2에 사설 IP로 SSH 접속해 `script/deploy/deploy.sh <SHA>`를 실행한다.
6. `deploy.sh`: 설정 검사 → 옛 이미지 정리 → pull 재시도 → `docker compose up -d --wait` → 스모크 → JIT 예열(ISE-264). 실패하면 직전 성공 SHA로 되돌린다.
7. 결과를 슬랙 배포 채널에 알린다. 2026-11-11에 자동 되돌림이 실제로 한 번 동작했다.

### 왜 이 구성인가 (ADR 0044, 0047)

- 이미지를 커밋 SHA로 고정하면 "지금 서버에 무엇이 떠 있나"가 SHA 하나로 정해지고, 되돌림도 SHA만 바꾸면 된다. `latest`는 같은 이름이 다른 내용을 가리켜 되돌릴 기준이 없다.
- 빌드는 Actions가, 배포는 Jenkins가 한다. 배포 EC2에서 직접 빌드하면 5~10분이 걸리고 떠 있는 서비스와 CPU를 다툰다. 노트북에서 빌드하면 사람마다 결과가 다르다. Jenkins를 배포 EC2에 함께 두면 메모리가 0.5~1GB 더 든다. AI는 "이미지만 자동, 배포는 수동"을 권했지만 자동 배포를 골랐다(ADR 0044).
- EC2 한 대에 docker compose로 시작했다. 처음부터 RDS·ElastiCache로 나누는 안은 리허설 전 이틀 안에 끝내기 어렵고 비용이 늘어 미뤘다. 분리는 서버를 멈춘 기간에 검토하기로 했고, 결과 기록은 없다(ADR 0047).
- 한계: 장비 한 대라 그 장비가 죽으면 전부 멈춘다. Kafka 복제도 1이다. 발표에서 이 점을 숨기지 않는다.

## 7. 서버 사양

| 장비 | 사양 | 용도 |
|---|---|---|
| 배포 EC2 | m7i.xlarge(4 vCPU, 메모리 15,701MiB) | 컨테이너 약 20개. 11/5에 m7i-flex.xlarge에서 바꿨다. flex는 vCPU당 기준 성능이 40%이고 최대 성능은 "대부분의 시간"만 보장해, 지속 부하 측정에서 CPU가 흔들린다(`docs/design/infra/deployment.md`) |
| Jenkins EC2 | t3.small | 배포만 |
| 부하 발생기 | c6i.xlarge(4 vCPU, 8GiB), `grafana/k6:1.0.0` | 같은 VPC 사설 IP로 Gateway를 친다. 한 번에 한 명만 쓴다([`docs/guides/loadgen.md`](../../../guides/loadgen.md)) |

발생기를 서버와 다른 장비에 둔 이유: 같은 장비에서 k6를 돌리면 k6가 CPU와 메모리를 함께 먹어 서버 한계와 발생기 한계를 구분할 수 없다. local 측정에서 실제로 k6 메모리 때문에 결과를 버린 적이 있다(TS-69).

## 8. HTTPS와 공개 주소

- 도메인 없이 Let's Encrypt의 IP 주소 인증서를 쓴다(수명 약 6일, certbot 자동 갱신, 만료 알림 스크립트, ISE-278).
- nginx가 80을 443으로 넘긴다. `/api/`는 Gateway로, `/grafana/`는 Grafana로 중계한다.
- 공개 주소는 서버 `.env`의 `PUBLIC_URL` 한 곳에만 둔다. Grafana 주소와 슬랙 알림 링크가 이 값에서 나온다. 파일마다 주소를 고치던 방식을 거부하고 한 곳으로 모은 판단이 있다(`docs/ai-judgments/README.md` 11/16 행).
- Swagger UI는 Gateway의 `/api/docs`다. 서비스별 문서를 Gateway가 모아서 보여 준다. 내부 API(`/internal/**`)는 문서에서 빼고 Gateway가 404로 막는다(ADR 0063).

## 9. 관측

> 비유: 건물 계기판(Prometheus·Grafana), 출입 기록부(Loki), 택배 추적번호(Zipkin), 화재 경보(Alertmanager → 슬랙).

| 도구 | 하는 일 | 설정 |
|---|---|---|
| Prometheus | 5초마다 앱 8개의 `/actuator/prometheus` 수집, 경보 규칙 평가 | `infra/prometheus.yml`, 규칙 `infra/prometheus/rules/` |
| Grafana | 대시보드 6개: 개발 기반, 대기열, 좌석 선점, 결제, 추첨, 요청 로그 | `infra/grafana/dashboards/` |
| Loki + Alloy | Alloy가 Docker 소켓으로 앱 8개 로그를 모아 Loki로. 7일 보관. 건별 결제 이상 로그도 알림 규칙으로 | `infra/loki/`, `infra/alloy/config.alloy` |
| Zipkin | 요청 추적. 메모리 저장, 스팬 10만 개 상한(TS-54) | compose |
| Alertmanager | 슬랙 성능 모니터링 채널로 알림. critical이 울리면 같은 경보의 warning은 억제 | `infra/alertmanager/` |

로그 수집을 ELK가 아니라 Loki로 고른 이유는 메모리다. ELK는 약 2GB가 더 들고, Loki·Alloy·Alertmanager는 합쳐 약 0.9GB(가정)다. 앱이 Loki로 직접 보내지 않고 Alloy가 컨테이너 로그를 읽어 가게 해, Loki가 멈춰도 앱은 영향을 받지 않는다(ADR 0045).

알림 규칙은 CI에서 `promtool`·`amtool`로 단위 테스트한다(`prometheus-rules.yml`). 알림은 실제 장애로 울려 봐야 믿을 수 있다는 교훈이 있다(TS-37: 지표 태그 `job`이 Prometheus 라벨과 겹쳐 경보가 안 울렸다).

요청 로그는 운영에서 5xx, 끊긴 요청, 200ms 이상만 남긴다(ADR 0052). 모든 요청을 남기면 Gateway CPU가 로그 직렬화에 쓰였다. 줄인 뒤 같은 부하에서 CPU가 78%에서 66%로 내려가고 처리량이 늘었다([04 부하 테스트](04-load-test.md) 5절).

## 면접 포인트

- "왜 Kubernetes가 아니라 docker compose인가" → 팀 5명, 4주, 장비 한 대 조건에서 전체 MSA를 재현 가능하게 띄우는 것이 목적이었다. 대신 메모리 상한, healthcheck, 커밋 SHA 이미지, 자동 되돌림으로 운영 기본기를 갖췄다. 다중 장비와 자동 확장은 한계로 남겼다.
- "Config Server를 왜 썼나" → 앱 8개가 Kafka·Redis·타임아웃 같은 공통 설정을 함께 쓴다. `config-repo/application.yml`에 공통값을, 서비스·프로필(local·prod·loadtest) 파일에 차이만 둔다. 설정 변경도 코드처럼 PR로 리뷰된다. 대가는 기동 순서 의존과 재시작 필요다.
- "부하 발생기를 왜 따로 두었나" → 발생기 한계와 서버 한계를 구분하려고 했다. 같은 장비에서 재면 둘이 섞인다.

## 참고

- `compose.yml`, `compose.deploy.yml`, `Jenkinsfile`, `script/deploy/deploy.sh`, `docker-bake.hcl`
- [`docs/design/infra/`](../../../design/infra/README.md): deployment, observability, load-test, single-host-msa-resource-isolation
- ADR 0003, 0006, 0040, 0044, 0045, 0046, 0047, 0050, 0052, 0063
