-- 예매에 연결된 응모를 reservation_id로 찾게 한다. 결제 결과(markPaid·markFailed·releaseForRetry)와
-- 선점 만료 훅(findWonDrawAtByReservationId)이 이 조건으로 찾는다.
-- 이 인덱스가 없으면 플래너는 (lottery_id, status, draw_rank)를 선행 열 없이 status만으로 통째로 훑는다.
-- 응모가 쌓일수록 느려졌다(로컬 응모 303만 행, 결제 결과 UPDATE 건당 7.20ms → 0.31ms).
-- 부분 인덱스로 둔다. 예매가 연결되지 않은 응모(응모 중·예비·낙첨)는 담지 않으므로 낙첨 일괄 갱신 때
-- 인덱스 항목을 만들지 않고, 크기는 일반 인덱스의 약 1/5이다.
-- Note: reservation_id = ? 조건은 IS NOT NULL을 함의하므로 플래너가 이 인덱스를 쓴다. IS NULL로 찾는 쿼리에는 쓰이지 않는다.
CREATE INDEX idx_lottery_entries_reservation_id
    ON lottery_entries (reservation_id)
    WHERE reservation_id IS NOT NULL;
