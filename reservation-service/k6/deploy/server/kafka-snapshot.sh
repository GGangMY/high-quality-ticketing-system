#!/usr/bin/env bash
# 접수형 단계 부하 중 Kafka 토픽·컨슈머 그룹 상태를 글로 남긴다(ISE-265의 Kafka-UI 캡처를 뒷받침하는 원자료). 읽기만 한다.
# 사용: kafka-snapshot.sh <출력 파일> <시작 전 대기 초> [횟수(기본 3)] [간격 초(기본 30)]   deploy-run.sh가 nohup으로 띄운다
# 남기는 것: 토픽별 파티션 수·복제 수(kafka-topics --describe), 그룹별 파티션·현재 오프셋·끝 오프셋·랙(kafka-consumer-groups --describe)
set -uo pipefail
source "$(dirname "$0")/common.sh"
OUT="$1"; DELAY="$2"; COUNT="${3:-3}"; GAP="${4:-30}"
BIN=/opt/kafka/bin
mkdir -p "$(dirname "$OUT")"
sleep "$DELAY"
kafka="$(container_of kafka)" || exit 1
{
  echo "## topics $(date +%s)"
  docker exec "$kafka" "$BIN/kafka-topics.sh" --bootstrap-server localhost:9092 --describe 2>&1 | grep -v '^\s*$'
} >> "$OUT"
for i in $(seq 1 "$COUNT"); do
  {
    echo "## groups $(date +%s) ($i/$COUNT)"
    docker exec "$kafka" "$BIN/kafka-consumer-groups.sh" --bootstrap-server localhost:9092 --describe --all-groups 2>&1 | grep -v '^\s*$'
  } >> "$OUT"
  [ "$i" = "$COUNT" ] || sleep "$GAP"
done
