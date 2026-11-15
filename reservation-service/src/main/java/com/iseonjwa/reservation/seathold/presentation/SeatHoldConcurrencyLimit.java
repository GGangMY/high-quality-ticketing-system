package com.iseonjwa.reservation.seathold.presentation;

import com.iseonjwa.common.response.BusinessException;
import com.iseonjwa.common.response.CommonErrorCode;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.Gauge;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import java.util.function.Supplier;

/**
 * 선점 API가 동시에 처리하는 요청 수의 상한(ADR 0060 3번). 자리를 얻지 못한 요청은 DB 커넥션을 잡기 전에 503
 * {@code SERVICE_UNAVAILABLE}로 거절한다. 잠긴 좌석을 기다리는 선점이 커넥션 풀을 다 쥐어 좌석 조회처럼 상관없는
 * API까지 막히는 번짐과, 응답 시한(3초)이 지난 뒤 서버가 좌석을 잡는 유령 선점을 끊는다.
 *
 * <p>{@code seat-hold.max-concurrent}가 0이면 끈다(기본). 값은 커넥션 풀 크기보다 작게 두어 다른 API의 자리를 남긴다.
 * {@code seat-hold.max-concurrent-wait}만큼은 자리를 기다린다. 순간 몰림은 받아 주고, 그보다 오래 밀릴 요청만 거절한다.
 */
@Component
public class SeatHoldConcurrencyLimit {
    private final Semaphore permits;
    private final Duration wait;
    private final Counter rejected;
    private final Timer waited;

    public SeatHoldConcurrencyLimit(@Value("${seat-hold.max-concurrent:0}") int maxConcurrent,
            @Value("${seat-hold.max-concurrent-wait:200ms}") Duration wait, MeterRegistry meterRegistry) {
        if (maxConcurrent < 0 || wait.isNegative()) {
            throw new IllegalArgumentException("선점 동시 처리 상한과 대기는 0 이상이어야 합니다: " + maxConcurrent + ", " + wait);
        }
        this.permits = maxConcurrent == 0 ? null : new Semaphore(maxConcurrent, true);
        this.wait = wait;
        this.rejected = Counter.builder("seathold.concurrency.rejected")
                .description("선점 동시 처리 상한을 넘어 503으로 거절한 요청 수")
                .register(meterRegistry);
        // Note: 상한 값을 정하려면 거절 수만으로는 모자란다. 사용 중인 자리가 상한에 늘 붙어 있는지, 자리를 얼마나
        // 기다렸는지를 함께 봐야 "상한이 작아서 거절"인지 "처리 가능량을 넘어서 거절"인지 가를 수 있다
        this.waited = Timer.builder("seathold.concurrency.wait")
                .description("선점 동시 처리 상한의 자리를 기다린 시간(얻었든 못 얻었든)")
                .serviceLevelObjectives(Duration.ofMillis(1), Duration.ofMillis(10), Duration.ofMillis(50),
                        Duration.ofMillis(100), Duration.ofMillis(200))
                .register(meterRegistry);
        if (permits != null) {
            Gauge.builder("seathold.concurrency.in_use", permits, held -> maxConcurrent - held.availablePermits())
                    .description("선점 동시 처리 상한에서 지금 쓰고 있는 자리 수")
                    .register(meterRegistry);
        }
    }

    // Note: 대기를 짧게 둔다. 길면 그동안 톰캣 스레드를 쥐어 커넥션 대기(1초)를 앞으로 옮긴 것뿐이 된다.
    // 0으로 두면 순간 몰림까지 잘라, 상한 없이도 다 처리하던 초당 300건에서 16~19%를 거절했다. 200ms는 0~1.4%였다(ADR 0060)
    public <T> T run(Supplier<T> hold) {
        if (permits == null) {
            return hold.get();
        }
        if (!acquire()) {
            rejected.increment();
            throw new BusinessException(CommonErrorCode.SERVICE_UNAVAILABLE);
        }
        try {
            return hold.get();
        } finally {
            permits.release();
        }
    }

    private boolean acquire() {
        var started = System.nanoTime();
        try {
            return permits.tryAcquire(wait.toNanos(), TimeUnit.NANOSECONDS);
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            return false;
        } finally {
            waited.record(System.nanoTime() - started, TimeUnit.NANOSECONDS);
        }
    }
}
