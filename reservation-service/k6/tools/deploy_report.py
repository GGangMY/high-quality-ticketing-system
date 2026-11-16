"""배포 단계 측정(deploy/deploy-run.sh) 한 번의 결과를 단계 비교표 하나로 모은다.

사용: python reservation-service/k6/tools/deploy_report.py <results/deploy-session-<시각>.txt> [판정 p95 ms] [판정 오류율 %]
출력: 같은 폴더의 deploy-report-<시각>.md(표)와 .csv(그래프용, 회 × 부하 단계 한 줄씩)

한 회(deploy-<단계>-<종류>-<시각>)마다 읽는 파일
- k6 원자료 *-<회 이름>-*-raw.csv.gz: 부하 단계(stage 태그)별 선점 응답 상태, 지연, 사용자 결과(users_finished), 접수형 완료 시간
- <회 이름>-meta.txt: 단계·이미지 커밋·k6 조건·부하 시작 시각
- <회 이름>-metrics.csv: 서버 지표 10초 표본(b8_metrics.py). 부하 단계 구간으로 잘라 평균한다
- <회 이름>-invariants.txt, -server.txt: 정합성(대사)과 재시작·OOM

판정
- 사용자 오류: 마지막 응답이 201·409가 아닌 사용자(503·500·시한 초과·접수형 결과 미확정). 409로 세 번 거절된 사용자(gave_up)는
  매진에 대한 정상 응답이라 오류가 아니다. 로컬 L9의 "의도 실패"와 같은 뜻이다
- 처리 한계 단계: 사용자 오류율이 기준(기본 1%) 미만이고 선점 p95가 기준(기본 1,000ms) 미만인 가장 높은 부하 단계.
  그 아래 단계 중 하나라도 기준을 넘으면 그 단계 바로 앞까지로 본다(한 번 무너진 뒤 우연히 좋아진 단계를 세지 않는다)
"""
import csv
import gzip
import glob
import os
import re
import sys
from collections import Counter, defaultdict
from urllib.parse import parse_qsl

# 단계 설명. steps.sh와 overlays/*.yml의 머리 주석이 정본이다
STEP_NOTES = {
    "base": "개선 전(Serial GC, 풀 5, 대기 30초)",
    "g1": "GC를 G1로",
    "r1": "커넥션 대기 30초 → 1초",
    "p4a": "좌석 조회 필요한 열만",
    "p4b": "배치 캐시·선점 가능 ID만",
    "p4c": "좌석 상태 1초 공유",
    "f": "만료 SKIP LOCKED, 풀 10",
    "pre": "사전 거절(측정 브랜치)",
    "d1114": "dev 11/14(ISE-261 전, 잠금 500ms)",
    "l50": "잠금 50ms + 먼저 거절·순서(ADR 0061·0062)",
    "one": "한 문장 사전 판정(반복 4)",
    "cur": "dev 11/16(캐시 사전 거절)",
    "lim4": "cur + 동시 처리 상한 4",
    "pool8": "cur + 풀 8·상한 7",
    "aout": "접수형 Outbox",
    "adir": "접수형 직접 발행",
}
# 좌석 조회를 바꾼 단계. H(선점만)는 좌석 목록을 처음 한 번만 받아 이 단계들의 효과가 거의 드러나지 않는다
SEAT_QUERY_STEPS = {"p4a", "p4b", "p4c"}
RAMP_UP_SECONDS = 5  # k1-seathold.js와 같다. 단계 앞 5초는 stage=ramp로 태그돼 단계 집계에서 빠진다
SERVER_COLUMNS = [
    ("hold_server_p95_ms", "서버 선점 p95(ms)"),
    ("hikari_pending", "커넥션 대기 수"),
    ("res_cpu_cores", "예약 CPU(코어)"),
    ("gw_cpu_cores", "Gateway CPU(코어)"),
    ("gw_in_flight_rejected_per_s", "Gateway 상한 거절/s"),
    ("sh_held_ms_avg", "상한 자리 쥐는 시간(ms)"),
    ("sh_limit_rejected_per_s", "상한 거절/s"),
    ("sh_pre_rejected_per_s", "캐시 사전 거절/s"),
    ("sh_seat_lock_ms_avg", "좌석 잠금(ms)"),
    ("tomcat_busy_threads", "바쁜 요청 스레드"),
]


def pct(values, q):
    if not values:
        return None
    values = sorted(values)
    return values[min(len(values) - 1, int(len(values) * q))]


def fmt(value, digits=0, suffix=""):
    if value is None:
        return "-"
    return f"{value:,.{digits}f}{suffix}"


def read_meta(path):
    text = open(path, encoding="utf-8").read()
    def field(key):
        m = re.search(rf"(?:^|\s){key}=(\S+)", text)
        return m.group(1) if m else None
    env = text.split("env_k6=", 1)[1].splitlines()[0] if "env_k6=" in text else ""
    stages = re.search(r"STAGES=([\d,]+)", env)
    seconds = re.search(r"STAGE_SECONDS=(\d+)", env)
    return {
        "step": field("step"), "kind": field("kind"), "commit": field("image_commit"),
        "start": int(field("start") or 0), "load_end": int(field("load_end") or 0),
        "stages": [int(x) for x in stages.group(1).split(",")] if stages else [],
        "stage_seconds": int(seconds.group(1)) if seconds else 60,
        "k6_exit": field("k6_exit"),
    }


def read_raw(path):
    """부하 단계별 선점 상태·지연, 사용자 결과, 접수형 완료 시간을 센다. 잘린 gz(k6 OOM)도 읽은 데까지 쓴다"""
    status = defaultdict(Counter)
    duration = defaultdict(list)
    users = defaultdict(Counter)
    completion = defaultdict(list)
    truncated = False
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        try:
            for row in reader:
                name = row["metric_name"]
                if name not in ("http_reqs", "http_req_duration", "users_finished", "async_completion"):
                    continue
                tags = dict(parse_qsl(row.get("extra_tags") or ""))
                stage = tags.get("stage")
                if not stage or stage == "ramp":
                    continue
                if name == "users_finished":
                    users[stage][tags.get("outcome", "?")] += int(float(row["metric_value"]))
                elif name == "async_completion":
                    completion[stage].append(float(row["metric_value"]))
                elif tags.get("api") == "hold":
                    if name == "http_reqs":
                        status[stage][row["status"] or "0"] += 1
                    else:
                        duration[stage].append(float(row["metric_value"]))
        except (EOFError, OSError):
            truncated = True
    return status, duration, users, completion, truncated


def read_metrics(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def server_avg(rows, column, begin, end):
    values = [float(r[column]) for r in rows
              if r.get(column) not in (None, "") and begin <= int(r["epoch"]) < end]
    return sum(values) / len(values) if values else None


def read_invariants(path):
    if not os.path.exists(path):
        return None, None
    text = open(path, encoding="utf-8").read()
    found = dict(re.findall(r"^\s*(\w+)\s*\|\s*(\d+)\s*$", text, re.M))
    checks = ("double_sold_seats", "quota_mismatch_users", "seat_status_mismatches")
    if not all(c in found for c in checks):
        return None, found.get("held_seats")
    return sum(int(found[c]) for c in checks), found.get("held_seats")


def analyze(results, name):
    meta = read_meta(os.path.join(results, f"{name}-meta.txt"))
    raws = glob.glob(os.path.join(results, f"*-{name}-*-raw.csv.gz"))
    if not raws:
        raise FileNotFoundError(f"{name}의 k6 원자료가 없다")
    status, duration, users, completion, truncated = read_raw(raws[0])
    metrics = read_metrics(os.path.join(results, f"{name}-metrics.csv"))
    violations, held_seats = read_invariants(os.path.join(results, f"{name}-invariants.txt"))
    server = open(os.path.join(results, f"{name}-server.txt"), encoding="utf-8").read() \
        if os.path.exists(os.path.join(results, f"{name}-server.txt")) else ""
    restarts = re.search(r"reservation_restarts=(\d+) oom=(\w+)", server)
    gw = re.search(r"gateway_restarts=(\d+) oom=(\w+)", server)

    stages = []
    for i, rate in enumerate(meta["stages"]):
        key = str(rate)
        c = status.get(key, Counter())
        total = sum(c.values())
        u = users.get(key, Counter())
        user_total = sum(u.values())
        window = meta["stage_seconds"] - (RAMP_UP_SECONDS if i > 0 else 0)
        begin = meta["start"] + i * meta["stage_seconds"] + (RAMP_UP_SECONDS if i > 0 else 0)
        end = meta["start"] + (i + 1) * meta["stage_seconds"]
        server_end = end + 10  # 10초 표본의 마지막 칸까지
        stages.append({
            "rate": rate,
            "hold_requests": total,
            "hold_per_s": total / window if window else None,
            "s201": c["201"], "s202": c["202"], "s409": c["409"], "s503": c["503"],
            "s5xx_other": sum(v for k, v in c.items() if k.startswith("5") and k != "503"),
            "s0": c["0"],
            "p50": pct(duration.get(key), 0.50), "p95": pct(duration.get(key), 0.95), "p99": pct(duration.get(key), 0.99),
            "users": user_total,
            "user_error_pct": 100 * u["error"] / user_total if user_total else None,
            "user_held": u["held"], "user_gave_up": u["gave_up"],
            "async_p95": pct(completion.get(key), 0.95),
            "server": {col: server_avg(metrics, col, begin, server_end) for col, _ in SERVER_COLUMNS},
        })
    return {
        "name": name, "meta": meta, "stages": stages, "truncated": truncated,
        "violations": violations, "held_seats": held_seats,
        "res_restarts": restarts.group(1) if restarts else None, "res_oom": restarts.group(2) if restarts else None,
        "gw_restarts": gw.group(1) if gw else None, "gw_oom": gw.group(2) if gw else None,
    }


def capacity(run, p95_limit, error_limit):
    best = None
    for st in run["stages"]:
        ok = (st["user_error_pct"] is not None and st["user_error_pct"] < error_limit
              and st["p95"] is not None and st["p95"] < p95_limit)
        if not ok:
            break
        best = st
    return best


def label(run, seen):
    step = run["meta"]["step"]
    seen[step] += 1
    return step if seen[step] == 1 else f"{step}({seen[step]}회째)"


def main():
    # Windows 콘솔(cp949)에서도 진행 문구가 깨지지 않게 한다
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    session = sys.argv[1]
    p95_limit = float(sys.argv[2]) if len(sys.argv) > 2 else 1000.0
    error_limit = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    results = os.path.dirname(os.path.abspath(session))
    stamp = re.search(r"deploy-session-(\d{8}-\d{6})", session)
    stamp = stamp.group(1) if stamp else "manual"
    lines = [l.strip() for l in open(session, encoding="utf-8") if l.strip()]
    failed = [l for l in lines if l.startswith("FAILED")]
    runs, skipped = [], []
    for name in (l for l in lines if not l.startswith("FAILED")):
        try:
            runs.append(analyze(results, name))
            print(f"[report] {name}: 읽음", file=sys.stderr)
        except (FileNotFoundError, IndexError, ValueError) as e:
            skipped.append(f"{name}: {e}")
    if not runs:
        sys.exit("읽을 회가 없다")

    rates = sorted({st["rate"] for r in runs for st in r["stages"]})
    seen = Counter()
    labels = [label(r, seen) for r in runs]
    out = []
    w = out.append
    w(f"# 배포 단계 측정 결과 ({stamp})\n")
    w(f"- 목록: `{os.path.basename(session)}`, 회 {len(runs)}개. 판정 기준: 사용자 오류율 < {error_limit:g}%, 선점 p95 < {p95_limit:,.0f}ms")
    w("- 사용자 오류: 마지막 응답이 201·409가 아닌 사용자(503·500·시한 초과·접수형 결과 미확정). 409로 세 번 거절된 사용자는 매진에 대한 정상 응답이라 넣지 않는다")
    w("- 부하 단계 값은 초당 도착 사용자 수다. 사용자 하나는 409를 받으면 최대 2번 더 보내 매진 뒤 선점 요청은 약 3배다. 단계 앞 5초(올리는 구간)는 빠진다")
    if any(r["meta"]["step"] in SEAT_QUERY_STEPS and r["meta"]["kind"] == "H" for r in runs):
        w("- 주의: p4a·p4b·p4c는 좌석 조회 개선이다. H는 좌석 목록을 처음 한 번만 받으므로 이 단계들의 효과는 거의 보이지 않는다(S로 따로 잰다)")
    if failed:
        w(f"- 실패한 회: {', '.join(failed)}")
    if skipped:
        w(f"- 읽지 못한 회: {'; '.join(skipped)}")
    w("")

    w("## 1. 요약\n")
    w("| 단계 | 바뀐 것 | 커밋 | 처리 한계 단계(/s) | 그때 선점 처리량(/s) | 그때 p95(ms) | 최고 단계 사용자 오류율 | 201 합계 | 정합성 위반 | 예약 재시작·OOM |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for lab, r in zip(labels, runs):
        cap = capacity(r, p95_limit, error_limit)
        top = r["stages"][-1] if r["stages"] else None
        total201 = sum(st["s201"] for st in r["stages"])
        viol = "-" if r["violations"] is None else ("0" if r["violations"] == 0 else f"**{r['violations']}**")
        flags = f"{r['res_restarts'] or '-'}·{r['res_oom'] or '-'}"
        note = STEP_NOTES.get(r["meta"]["step"], "")
        if r["truncated"]:
            note += " (k6 원자료 잘림)"
        w(f"| {lab} | {note} | `{r['meta']['commit']}` | {cap['rate'] if cap else '없음'} | {fmt(cap['hold_per_s'] if cap else None)} | "
          f"{fmt(cap['p95'] if cap else None)} | {fmt(top['user_error_pct'] if top else None, 1, '%')} | {total201:,} | {viol} | {flags} |")
    w("")

    def matrix(title, getter, digits, suffix=""):
        w(f"## {title}\n")
        w("| 단계 | " + " | ".join(f"{x}/s" for x in rates) + " |")
        w("|---|" + "---|" * len(rates))
        for lab, r in zip(labels, runs):
            by_rate = {st["rate"]: st for st in r["stages"]}
            w(f"| {lab} | " + " | ".join(fmt(getter(by_rate[x]) if x in by_rate else None, digits, suffix) for x in rates) + " |")
        w("")

    matrix("2. 부하 단계별 사용자 오류율", lambda st: st["user_error_pct"], 1, "%")
    matrix("3. 부하 단계별 선점 p95(ms, k6가 본 값)", lambda st: st["p95"], 0)
    matrix("4. 부하 단계별 선점 처리량(초당 응답 수)", lambda st: st["hold_per_s"], 0)
    matrix("5. 부하 단계별 503 비율(선점 요청 기준)", lambda st: 100 * st["s503"] / st["hold_requests"] if st["hold_requests"] else None, 1, "%")
    matrix("6. 상한 자리 쥐는 시간 평균(ms, ISE-261 이후 이미지만)", lambda st: st["server"]["sh_held_ms_avg"], 2)
    if any(st["async_p95"] is not None for r in runs for st in r["stages"]):
        matrix("7. 접수형 접수 → 처리 완료 p95(ms)", lambda st: st["async_p95"], 0)

    w("## 8. 회별 자세히\n")
    for lab, r in zip(labels, runs):
        m = r["meta"]
        w(f"### {lab} — {STEP_NOTES.get(m['step'], '')}\n")
        w(f"- 회 이름 `{r['name']}`, 이미지 커밋 `{m['commit']}`, k6 종료 코드 {m['k6_exit'] or '-'}, "
          f"활성 선점 좌석 {r['held_seats'] or '-'}, Gateway 재시작·OOM {r['gw_restarts'] or '-'}·{r['gw_oom'] or '-'}")
        w("")
        head = ["부하(/s)", "선점 요청", "201", "202", "409", "503", "그 밖 5xx", "응답 없음", "p50", "p95", "p99", "사용자", "오류율"]
        head += [title for _, title in SERVER_COLUMNS]
        w("| " + " | ".join(head) + " |")
        w("|" + "---|" * len(head))
        for st in r["stages"]:
            cells = [str(st["rate"]), f"{st['hold_requests']:,}", f"{st['s201']:,}", f"{st['s202']:,}", f"{st['s409']:,}",
                     f"{st['s503']:,}", f"{st['s5xx_other']:,}", f"{st['s0']:,}", fmt(st["p50"]), fmt(st["p95"]), fmt(st["p99"]),
                     f"{st['users']:,}", fmt(st["user_error_pct"], 1, "%")]
            cells += [fmt(st["server"][col], 2) for col, _ in SERVER_COLUMNS]
            w("| " + " | ".join(cells) + " |")
        w("")

    md = os.path.join(results, f"deploy-report-{stamp}.md")
    with open(md, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    csv_path = os.path.join(results, f"deploy-report-{stamp}.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["run", "step", "commit", "rate", "hold_requests", "hold_per_s", "s201", "s202", "s409", "s503",
                         "s5xx_other", "s0", "p50_ms", "p95_ms", "p99_ms", "users", "user_error_pct", "async_p95_ms",
                         *[col for col, _ in SERVER_COLUMNS]])
        for lab, r in zip(labels, runs):
            for st in r["stages"]:
                writer.writerow([lab, r["meta"]["step"], r["meta"]["commit"], st["rate"], st["hold_requests"],
                                 st["hold_per_s"], st["s201"], st["s202"], st["s409"], st["s503"], st["s5xx_other"], st["s0"],
                                 st["p50"], st["p95"], st["p99"], st["users"], st["user_error_pct"], st["async_p95"],
                                 *[st["server"][col] for col, _ in SERVER_COLUMNS]])
    print(md)
    print(csv_path)


if __name__ == "__main__":
    main()
