package com.iseonjwa.reservation.lottery.application;

import com.iseonjwa.reservation.lottery.domain.entity.Lottery;
import com.iseonjwa.reservation.lottery.domain.entity.LotteryEntryStatus;
import com.iseonjwa.reservation.lottery.domain.policy.DrawEntrant;
import com.iseonjwa.reservation.lottery.domain.policy.DrawRanker;
import com.iseonjwa.reservation.lottery.domain.policy.SeatAllocator;
import com.iseonjwa.reservation.lottery.domain.policy.SeatAllocator.DrawAllocation;
import com.iseonjwa.reservation.lottery.domain.policy.SeatAllocator.SeatAssignment;
import com.iseonjwa.reservation.lottery.domain.repository.LotteryEntryRepository;
import com.iseonjwa.reservation.lottery.domain.repository.LotteryEntryRepository.DrawResult;
import com.iseonjwa.reservation.lottery.domain.repository.LotteryRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionTemplate;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 추첨 하나를 한 트랜잭션에서 메모리로 계산해 당첨·예비만 배치로 쓰고, 낙첨은 커밋 뒤 청크 트랜잭션으로 마저 쓴다(D8, details.md 4절).
 */
@Service
@RequiredArgsConstructor
public class LotteryDrawService {

    private static final int DRAW_TIMEOUT_SECONDS = 10;
    private static final int LOST_CHUNK_SIZE = 5_000;

    private final LotteryRepository lotteryRepository;
    private final LotteryEntryRepository lotteryEntryRepository;
    private final LotterySeatPort lotterySeatPort;
    private final TransactionTemplate transactionTemplate;

    @Transactional
    public int closeDueLotteries() {
        return lotteryRepository.closeDueLotteries();
    }

    public List<Long> findDrawDueIds() {
        return lotteryRepository.findDrawDueIds();
    }

    /**
     * 추첨을 한 번만 실행하며, 이미 추첨했거나 시각 전이면 아무것도 하지 않는다.
     *
     * @return 이번 호출이 추첨을 실행했으면 true
     */
    // Note: 낙첨 일괄 갱신을 빼서 트랜잭션 시간이 응모 수가 아니라 당첨·예비 수에 비례한다. 응모 30만 행에서 낙첨 갱신이 추첨 시간의 86%였다. 상한을 넘으면 롤백되어 CLOSED로 남고 다음 주기에 다시 시도한다.
    @Transactional(timeout = DRAW_TIMEOUT_SECONDS)
    public boolean draw(Long lotteryId) {
        if (!lotteryRepository.markDrawn(lotteryId)) {
            return false;
        }

        Lottery lottery = lotteryRepository.findById(lotteryId).orElseThrow();
        List<DrawEntrant> ranked = DrawRanker.rank(
                lottery.getSeed(),
                lotteryEntryRepository.findDrawEntrants(lotteryId));
        DrawAllocation allocation = SeatAllocator.draw(
                ranked,
                lotterySeatPort.findLotterySeats(lottery.getScheduleId()),
                lottery.getWaitlistCount());

        lotteryEntryRepository.saveDrawResults(toDrawResults(ranked, allocation));

        return true;
    }

    public List<Long> findLostPendingIds() {
        return lotteryRepository.findLostPendingIds();
    }

    /**
     * 추첨이 커밋된 뒤 남은 ENTERED를 청크마다 별도 트랜잭션으로 LOST로 바꾼다.
     *
     * @return 이번 호출이 LOST로 바꾼 응모 수
     */
    // Note: 갱신 조건이 status = 'ENTERED'라 멱등이다. 도중에 실패하면 커밋한 청크는 남고, 다음 주기가 나머지를 이어서 바꾼다. 그동안 종결은 ENTERED가 남은 추첨을 건너뛴다.
    public int settleLost(Long lotteryId) {
        int total = 0;
        int updated;
        do {
            updated = transactionTemplate.execute(
                    status -> lotteryEntryRepository.markLostChunk(lotteryId, LOST_CHUNK_SIZE));
            total += updated;
        } while (updated == LOST_CHUNK_SIZE);

        return total;
    }

    private static List<DrawResult> toDrawResults(List<DrawEntrant> ranked, DrawAllocation allocation) {
        Map<Long, Integer> rankByEntryId = new HashMap<>();
        for (int i = 0; i < ranked.size(); i++) {
            rankByEntryId.put(ranked.get(i).entryId(), i + 1);
        }

        List<DrawResult> results = new ArrayList<>();
        for (SeatAssignment winner : allocation.winners()) {
            results.add(toDrawResult(winner.entrant(), LotteryEntryStatus.WON, rankByEntryId));
        }
        for (DrawEntrant waitlisted : allocation.waitlisted()) {
            results.add(toDrawResult(waitlisted, LotteryEntryStatus.WAITLISTED, rankByEntryId));
        }

        return results;
    }

    private static DrawResult toDrawResult(DrawEntrant entrant,
                                           LotteryEntryStatus status,
                                           Map<Long, Integer> rankByEntryId) {
        return new DrawResult(entrant.entryId(), status, rankByEntryId.get(entrant.entryId()));
    }
}
