package com.iseonjwa.reservation.lottery.presentation.scheduling;

import com.iseonjwa.reservation.lottery.application.LotteryDrawService;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.concurrent.atomic.AtomicInteger;

/**
 * 전이를 조건부 UPDATE가 한 번만 반영해 인스턴스마다 돌아도 안전한 마감·추첨 스케줄러(details.md 4절).
 */
@Slf4j
@Component
@ConditionalOnProperty(name = "lottery.scheduler.enabled", havingValue = "true", matchIfMissing = true)
public class LotteryDrawScheduler {

    private final LotteryDrawService drawService;
    private final Timer drawTimer;
    private final Counter drawFailures;
    private final Timer lostSettleTimer;
    // 연속 실패가 쌓이면 시간 초과가 반복된다는 뜻이라 0이 아니면 경보 대상이다(D8)
    private final AtomicInteger consecutiveFailures;

    public LotteryDrawScheduler(LotteryDrawService drawService, MeterRegistry meterRegistry) {
        this.drawService = drawService;
        this.drawTimer = Timer.builder("lottery.draw.duration")
                .description("추첨 한 번의 실행 시간")
                .register(meterRegistry);
        this.drawFailures = Counter.builder("lottery.draw.failures")
                .description("추첨 실패 횟수")
                .register(meterRegistry);
        this.lostSettleTimer = Timer.builder("lottery.draw.lost.settle.duration")
                .description("추첨 뒤 남은 응모를 낙첨으로 바꾸는 시간")
                .register(meterRegistry);
        this.consecutiveFailures = meterRegistry.gauge("lottery.draw.consecutive.failures", new AtomicInteger());
    }

    @Scheduled(fixedDelayString = "${lottery.scheduler.close-interval:10s}")
    public void closeDueLotteries() {
        int closed = drawService.closeDueLotteries();
        if (closed > 0) {
            log.info("추첨 응모 마감: {}건", closed);
        }
    }

    // 추첨 하나가 실패해도 다음 추첨은 계속하고, 실패한 추첨은 CLOSED로 남아 다음 주기에 다시 시도된다.
    // 낙첨 마무리는 같은 주기에서 추첨 뒤에 돌아 방금 추첨한 추첨도 바로 이어 처리한다.
    @Scheduled(fixedDelayString = "${lottery.scheduler.draw-interval:10s}")
    public void drawDueLotteries() {
        drawLotteries();
        settleLostEntries();
    }

    private void drawLotteries() {
        for (Long lotteryId : drawService.findDrawDueIds()) {
            try {
                boolean drawn = drawTimer.recordCallable(() -> drawService.draw(lotteryId));
                consecutiveFailures.set(0);
                if (drawn) {
                    log.info("추첨 실행 완료: lotteryId={}", lotteryId);
                }
            } catch (Exception exception) {
                drawFailures.increment();
                consecutiveFailures.incrementAndGet();
                log.error("추첨 실행 실패: lotteryId={}", lotteryId, exception);
            }
        }
    }

    // 실패해도 이미 커밋한 청크는 남고, ENTERED가 남은 추첨은 다음 주기에 다시 집힌다
    private void settleLostEntries() {
        for (Long lotteryId : drawService.findLostPendingIds()) {
            try {
                int settled = lostSettleTimer.recordCallable(() -> drawService.settleLost(lotteryId));
                if (settled > 0) {
                    log.info("낙첨 처리 완료: lotteryId={}, 응모={}건", lotteryId, settled);
                }
            } catch (Exception exception) {
                log.error("낙첨 처리 실패: lotteryId={}", lotteryId, exception);
            }
        }
    }
}
