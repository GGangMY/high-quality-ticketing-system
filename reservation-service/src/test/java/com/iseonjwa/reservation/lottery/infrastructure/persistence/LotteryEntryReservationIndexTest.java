package com.iseonjwa.reservation.lottery.infrastructure.persistence;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.jpa.repository.Query;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertTrue;

// 결제 결과·선점 만료가 reservation_id로 응모를 찾을 때 부분 인덱스를 타는지 실행 계획으로 확인한다.
// 쿼리 문장은 리포지토리의 @Query 값을 그대로 읽어 와서, 쿼리가 바뀌면 이 테스트도 바뀐 쿼리를 검사한다.
@SpringBootTest(properties = {"spring.config.import=", "spring.cloud.config.enabled=false", "eureka.client.enabled=false"})
@ActiveProfiles("test")
@Transactional
class LotteryEntryReservationIndexTest {
    private static final String INDEX = "idx_lottery_entries_reservation_id";
    private static final int ENTRIES_PER_LOTTERY = 20_000;
    private static final int WINNERS_PER_LOTTERY = 1_000;

    @Autowired
    JdbcTemplate jdbc;

    private Long reservationId;

    // Note: 행이 적으면 플래너가 순차 스캔을 고르므로 실행 계획을 비교할 수 없다. 추첨 두 개에 응모를 넣고
    // 통계를 갱신한다. ANALYZE 결과도 트랜잭션과 함께 롤백된다
    @BeforeEach
    void setUp() {
        Long venueId = jdbc.queryForObject(
                "INSERT INTO venues (name, created_at, updated_at) VALUES ('KSPO DOME', now(), now()) RETURNING id",
                Long.class);
        Long concertId = jdbc.queryForObject(
                "INSERT INTO concerts (title, version, created_at, updated_at) VALUES ('콘서트', 0, now(), now())"
                        + " RETURNING id",
                Long.class);
        for (int i = 0; i < 2; i++) {
            Long scheduleId = jdbc.queryForObject(
                    "INSERT INTO schedules (concert_id, venue_id, starts_at, open_at, version, created_at, updated_at)"
                            + " VALUES (?, ?, now() + interval '10 day', now() - interval '1 day', 0, now(), now())"
                            + " RETURNING id",
                    Long.class, concertId, venueId);
            Long lotteryId = jdbc.queryForObject("""
                    INSERT INTO lotteries (schedule_id, source_grade, seat_count, waitlist_count, max_per_entry,
                                           entry_start_at, entry_end_at, draw_at, seed, status, created_at, updated_at)
                    VALUES (?, 'S', 1000, 500, 2, now() - interval '2 hour', now() - interval '1 hour',
                            now() - interval '10 minute', ?, 'DRAWN', now(), now())
                    RETURNING id""",
                    Long.class, scheduleId, new byte[32]);
            reservationId = jdbc.queryForObject("""
                    INSERT INTO reservations (reservation_no, request_id, user_id, schedule_id, status,
                                              quantity, total_amount, hold_expires_at, source, created_at, updated_at)
                    VALUES (?, ?, 1, ?, 'HELD', 1, 165000, now() + interval '5 minute', 'GENERAL', now(), now())
                    RETURNING id""",
                    Long.class, "R-INDEX-" + i, UUID.randomUUID(), scheduleId);
            jdbc.update("""
                    INSERT INTO lottery_entries (lottery_id, request_id, user_id, quantity, status, draw_rank,
                                                 reservation_id, created_at, updated_at)
                    SELECT ?, gen_random_uuid(), n, 1,
                           CASE WHEN n <= ? THEN 'WON' ELSE 'LOST' END,
                           CASE WHEN n <= ? THEN n END,
                           CASE WHEN n = 1 THEN ?::bigint END,
                           now(), now()
                    FROM generate_series(1, ?) n""",
                    lotteryId, WINNERS_PER_LOTTERY, WINNERS_PER_LOTTERY, reservationId, ENTRIES_PER_LOTTERY);
        }
        jdbc.execute("ANALYZE lottery_entries");
        jdbc.execute("ANALYZE lotteries");
    }

    @ParameterizedTest
    @ValueSource(strings = {"markPaid", "markFailed", "releaseForRetry", "findWonDrawAtByReservationId"})
    void 예매_id로_응모를_찾는_쿼리는_부분_인덱스를_쓴다(String methodName) {
        String plan = explain(queryOf(methodName));

        assertTrue(plan.contains(INDEX), methodName + " 실행 계획이 " + INDEX + "를 쓰지 않는다:\n" + plan);
    }

    // 바인딩 변수 대신 값을 넣어 실제 호출과 같은 맞춤 계획을 세우게 한다
    private String explain(String query) {
        String sql = query
                .replace(":reservationId", reservationId.toString())
                .replace(":reason", "'PG_DECLINED'")
                .replace(":maxAttempts", "3");
        return String.join("\n", jdbc.queryForList("EXPLAIN " + sql, String.class));
    }

    private static String queryOf(String methodName) {
        Method method = Arrays.stream(SpringDataLotteryEntryRepository.class.getDeclaredMethods())
                .filter(candidate -> candidate.getName().equals(methodName))
                .findFirst()
                .orElseThrow(() -> new IllegalStateException("리포지토리에 메서드가 없다: " + methodName));
        return method.getAnnotation(Query.class).value();
    }
}
