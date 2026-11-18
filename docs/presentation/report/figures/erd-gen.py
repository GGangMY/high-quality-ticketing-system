"""ERD 두 장을 손으로 배치한 HTML로 만든다(1600x900, 2배로 렌더해 3200x1800 PNG).
사용: python3 erd-gen.py <출력 폴더> 뒤 Chrome headless --window-size=1600,900 --force-device-scale-factor=2로 PNG를 만든다."""
import sys, html

OUT = sys.argv[1]
INK = '#120F1A'
HEAD = {'seat': '#FFE9A8', 'book': '#DDE0FF', 'lot': '#FFD6E5', 'user': '#E8E4F0', 'pay': '#DDE0FF', 'common': '#D4F2EC', 'ghost': '#FFFFFF'}
HH, RH, PAD, W = 40, 30, 8, 262


def h(rows):
    return HH + len(rows) * RH + PAD


def card(name, x, y, kind, rows, mark=None, ghost=False):
    r = []
    for key, col, note in rows:
        badge = f'<span class="k k-{key.lower()}">{key}</span>' if key else '<span class="k"></span>'
        r.append(f'<div class="row">{badge}<span class="c">{html.escape(col)}</span><span class="n">{html.escape(note)}</span></div>')
    m = f'<span class="mk">{mark}</span>' if mark else ''
    cls = 'card ghost' if ghost else 'card'
    return (f'<div class="{cls}" style="left:{x}px;top:{y}px;width:{W}px;height:{h(rows)}px">'
            f'<div class="hd" style="background:{HEAD[kind]};font-size:{16 if len(name) > 22 else 18}px">{html.escape(name)}{m}</div>{"".join(r)}</div>')


def path(points, label=None, lx=None, ly=None, dashed=False):
    d = 'M' + ' L'.join(f'{x},{y}' for x, y in points)
    dash = ' stroke-dasharray="7 6"' if dashed else ''
    s = f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="2.2"{dash}/>'
    # N쪽(끝점)에 갈퀴
    (x1, y1), (x2, y2) = points[-2], points[-1]
    if not dashed:
        if y1 == y2:
            dx = -1 if x2 > x1 else 1
            s += f'<path d="M{x2},{y2 - 8} L{x2 + dx * 12},{y2} L{x2},{y2 + 8}" fill="none" stroke="{INK}" stroke-width="2.2"/>'
        else:
            dy = -1 if y2 > y1 else 1
            s += f'<path d="M{x2 - 8},{y2} L{x2},{y2 + dy * 12} L{x2 + 8},{y2}" fill="none" stroke="{INK}" stroke-width="2.2"/>'
    if label:
        s += f'<foreignObject x="{lx}" y="{ly}" width="140" height="26"><div class="lb">{html.escape(label)}</div></foreignObject>'
    return s


def intents(items, x=1222, y=118, w=346):
    out = [f'<div class="panel" style="left:{x}px;top:{y}px;width:{w}px"><div class="ph">설계 의도</div>']
    for mk, t, d in items:
        out.append(f'<div class="it"><span class="mk">{mk}</span><div><div class="it-t">{html.escape(t)}</div><div class="it-d">{html.escape(d)}</div></div></div>')
    out.append('</div>')
    return ''.join(out)


def legend(items, x, y):
    s = ''.join(f'<span class="lg"><i style="background:{HEAD[k]}"></i>{html.escape(t)}</span>' for k, t in items)
    return f'<div class="legend" style="left:{x}px;top:{y}px">{s}<span class="lg"><b class="fk">─&lt;</b>1:N</span><span class="lg"><b class="fk">┄</b>DB 사이 값으로만 연결</span></div>'


CSS = f'''
* {{ box-sizing:border-box; margin:0 }}
body {{ width:1600px; height:900px; background:#F4F0E6; font-family:'Pretendard',sans-serif; color:{INK}; letter-spacing:-0.02em; position:relative; overflow:hidden }}
.t {{ position:absolute; left:40px; top:26px; font-size:34px; font-weight:800 }}
.s {{ position:absolute; left:40px; top:74px; font-size:17px; font-weight:600; color:#4B4659 }}
svg.lines {{ position:absolute; left:0; top:0 }}
.card {{ position:absolute; background:#FFFFFF; border:2.5px solid {INK}; border-radius:12px; box-shadow:5px 5px 0 {INK}; overflow:hidden }}
.card.ghost {{ border-style:dashed; box-shadow:none; background:rgba(255,255,255,.55) }}
.hd {{ height:{HH}px; display:flex; align-items:center; justify-content:space-between; padding:0 12px; font-family:'Space Grotesk','Pretendard',monospace; font-size:18px; font-weight:700; border-bottom:2px solid {INK} }}
.row {{ height:{RH}px; display:flex; align-items:center; gap:7px; padding:0 10px; font-size:16px }}
.row + .row {{ border-top:1px solid #ECE8F2 }}
.k {{ width:30px; flex:none; font-size:11.5px; font-weight:800; text-align:center; border-radius:5px; padding:1px 0 }}
.k-pk {{ background:{INK}; color:#FFD23F }} .k-fk {{ background:#2F3BE8; color:#fff }} .k-uk {{ background:#FF3D7F; color:#fff }}
.c {{ font-family:'SF Mono',Menlo,monospace; font-size:15px; font-weight:600; white-space:nowrap }}
.n {{ margin-left:auto; font-size:13px; font-weight:600; color:#6A6578; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:165px; text-align:right }}
.mk {{ display:inline-flex; width:24px; height:24px; border-radius:50%; background:#FFD23F; border:2px solid {INK}; font-size:13px; font-weight:800; align-items:center; justify-content:center; font-family:'Pretendard',sans-serif; flex:none }}
.lb {{ display:inline-block; font-size:13px; font-weight:700; background:#F4F0E6; padding:0 4px; color:#4B4659 }}
.panel {{ position:absolute; background:#FFFFFF; border:2.5px solid {INK}; border-radius:16px; box-shadow:6px 6px 0 {INK}; padding:18px 20px 8px }}
.ph {{ font-size:22px; font-weight:800; margin-bottom:10px }}
.it {{ display:flex; gap:12px; padding:11px 0; border-top:1px dashed #C9C4D6 }}
.it-t {{ font-size:17px; font-weight:800; line-height:1.3 }}
.it-d {{ font-size:15px; font-weight:500; color:#3E3A4C; line-height:1.45; margin-top:3px }}
.legend {{ position:absolute; display:flex; gap:18px; font-size:14px; font-weight:600; color:#4B4659 }}
.lg {{ display:flex; align-items:center; gap:6px }} .lg i {{ width:16px; height:16px; border:2px solid {INK}; border-radius:4px; display:inline-block }}
.fk {{ font-family:monospace; color:{INK} }}
'''


def page(title, sub, cards, lines, panel, leg):
    return (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
            f'<div class="t">{html.escape(title)}</div><div class="s">{html.escape(sub)}</div>'
            f'<svg class="lines" width="1600" height="900" viewBox="0 0 1600 900">{"".join(lines)}</svg>'
            f'{"".join(cards)}{panel}{leg}</body></html>')


# ---------- ① 예매 DB ----------
C1, C2, C3, C4 = 40, 333, 626, 919
R = {
    'concerts': (C1, 130, 'seat', [('PK', 'id', ''), ('', 'title', '공연명')]),
    'venues': (C1, 262, 'seat', [('PK', 'id', ''), ('', 'name', 'KSPO DOME')]),
    'venue_seats': (C1, 394, 'seat', [('PK', 'id', ''), ('FK', 'venue_id', ''), ('', 'section·row·no', '')]),
    'schedules': (C2, 130, 'seat', [('PK', 'id', ''), ('FK', 'concert_id', ''), ('FK', 'venue_id', ''), ('', 'open_at', '예매 오픈'), ('', 'max_per_user', '기본 4매')]),
    'schedule_seats': (C2, 358, 'seat', [('PK', 'id', ''), ('FK', 'schedule_id', ''), ('FK', 'venue_seat_id', ''), ('', 'grade', 'VIP·R·S·LOTTERY'), ('', 'status', 'AVAILABLE·HELD·SOLD')]),
    'reservations': (C3, 130, 'book', [('PK', 'id', ''), ('UK', 'reservation_no', '고객용 번호'), ('', 'user_id', '서비스 간 ID'), ('', 'status', 'HELD→CONFIRMED…'), ('', 'hold_expires_at', '선점 5분'), ('', 'source', 'GENERAL·LOTTERY')]),
    'reservation_seats': (C3, 382, 'book', [('PK', 'id', ''), ('FK', 'reservation_id', ''), ('FK', 'schedule_seat_id', '부분 UK'), ('', 'status', 'HELD·CONFIRMED…')]),
    'tickets': (C3, 566, 'book', [('PK', 'id', ''), ('FK', 'reservation_seat_id', '')]),
    'user_schedule_quotas': (C4, 130, 'book', [('PK', 'user_id + schedule_id', ''), ('', 'held_count', '≤ max_per_user')]),
    'seat_hold_requests': (C4, 262, 'book', [('PK', 'request_id', ''), ('', 'status', 'REQUESTED·HELD…')]),
    'reservation_status_histories': (C4, 394, 'book', [('FK', 'reservation_id', ''), ('', 'from → to', '상태 변화'), ('', 'reason', '거절·만료·취소')]),
    'lotteries': (C2, 610, 'lot', [('PK', 'id', ''), ('FK', 'schedule_id', ''), ('', 'seat_count', '추첨석 수'), ('', 'status', 'OPEN→DRAWN→DONE')]),
    'lottery_entries': (C4, 594, 'lot', [('PK', 'id', ''), ('FK', 'lottery_id', ''), ('', 'user_id', '응모자'), ('', 'status', 'WON·WAITLISTED…'), ('', 'draw_rank', '예비 승계 순서'), ('FK', 'reservation_id', '당첨 시')]),
}
MK1 = {'schedule_seats': '1', 'reservation_seats': '1', 'user_schedule_quotas': '2', 'seat_hold_requests': '3', 'reservation_status_histories': '4', 'lottery_entries': '5', 'lotteries': '5'}
cards1 = [card(n, x, y, k, rows, MK1.get(n)) for n, (x, y, k, rows) in R.items()]


def bot(n):
    x, y, k, rows = R[n]; return y + h(rows)


R1 = C1 + W; R2 = C2 + W; R3 = C3 + W
M1 = C1 + W // 2; M2 = C2 + W // 2; M3 = C3 + W // 2
G12 = (R1 + C2) // 2; G34a = R3 + 10; G34b = R3 + 22
L1 = [
    path([(R1, 178), (C2, 178)]),                                     # concerts → schedules
    path([(R1, 310), (G12, 310), (G12, 235), (C2, 235)]),             # venues → schedules
    path([(M1, bot('venues')), (M1, 394)]),                           # venues → venue_seats
    path([(R1, 480), (C2, 480)]),                                     # venue_seats → schedule_seats
    path([(M2, bot('schedules')), (M2, 358)]),                        # schedules → schedule_seats
    path([(R2, 480), (C3, 480)]),                                     # schedule_seats → reservation_seats
    path([(M3, bot('reservations')), (M3, 382)]),                     # reservations → reservation_seats
    path([(M3, bot('reservation_seats')), (M3, 566)]),                # reservation_seats → tickets
    path([(C4, 310), (R3, 310)]),                                     # seat_hold_requests → reservations
    path([(R3, 340), (G34a, 340), (G34a, 460), (C4, 460)]),           # reservations → histories
    path([(R2, 700), (C4, 700)]),                                     # lotteries → lottery_entries
    path([(C4, 790), (G34b, 790), (G34b, 210), (R3, 210)]),           # lottery_entries → reservations
]
P1 = intents([
    ('1', '판매 판정은 DB가 한다', 'schedule_seats를 AVAILABLE일 때만 HELD로 바꾸는 조건부 UPDATE, reservation_seats의 부분 유니크(HELD·CONFIRMED)가 마지막 방어선'),
    ('2', '매수 한도는 한 행에서', '사용자·회차 행을 먼저 만든 뒤 조건부 UPDATE로 같은 사용자의 동시 요청을 줄 세움'),
    ('3', '접수형도 상태를 남긴다', '요청 행과 outbox를 한 트랜잭션에 써서 실패·재조회를 판단(SA 피드백 반영)'),
    ('4', '판매 기록은 지우지 않는다', '상태 변화를 이력으로 남겨 정산·분쟁의 근거로 씀'),
    ('5', '추첨석은 등급으로 분리', 'LOTTERY 등급이라 같은 DB에서도 일반 선점과 부딪치지 않음, draw_rank로 예비 당첨자 승계'),
])
LG1 = legend([('seat', '공연·좌석'), ('book', '선점·예매'), ('lot', '추첨')], 40, 858)
open(f'{OUT}/2026-11-18-erd-reservation.html', 'w', encoding='utf-8').write(page(
    'ERD ① 예매 DB (reservation)', '공연·좌석, 대기열 선점·예매, 추첨이 한 DB에 있다. 감사 컬럼과 일부 컬럼 생략(전체는 SA MASTER 12장)', cards1, L1, P1, LG1))

# ---------- ② 결제·사용자 DB ----------
Q = {
    'users': (40, 150, 'user', [('PK', 'id', ''), ('UK', 'email', '로그인 ID'), ('', 'password_hash', 'BCrypt'), ('', 'role', 'USER·ADMIN')]),
    'reservations': (40, 380, 'ghost', [('PK', 'id', '예매 DB')]),
    'payments': (333, 130, 'pay', [('PK', 'id', ''), ('UK', 'reservation_id', '예매당 하나'), ('', 'user_id', '서비스 간 ID'), ('', 'amount', '토큰 금액과 검증'), ('', 'method', 'CARD·BILLING'), ('', 'status', 'UNKNOWN 포함 6개'), ('UK', 'pg_order_id', 'PG 호출 전 저장'), ('', 'next_check_at', '재조회 시각')]),
    'payment_status_histories': (626, 130, 'pay', [('FK', 'payment_id', ''), ('', 'from → to', '상태 변화'), ('', 'actor', '누가 바꿨나')]),
    'refunds': (626, 300, 'pay', [('PK', 'id', ''), ('UK', 'payment_id', '결제당 1건'), ('UK', 'pg_refund_id', 'PG 멱등키'), ('', 'status', 'UNKNOWN 포함 5개')]),
    'billing_keys': (333, 470, 'pay', [('PK', 'id', ''), ('', 'user_id', 'ACTIVE 1개'), ('', 'billing_key_enc', '암호화'), ('', 'card_last4', '끝 4자리')]),
    'outbox_events': (919, 130, 'common', [('UK', 'event_id', ''), ('', 'topic', 'payment.result…'), ('', 'payload', 'jsonb'), ('', 'status', 'PENDING→SENT')]),
    'processed_events': (919, 330, 'common', [('PK', 'event_id + group', '소비자별')]),
    'idempotency_records': (919, 446, 'common', [('PK', 'user_id + idem_key', ''), ('', 'response_body', '같은 응답'), ('', 'expires_at', '24시간')]),
}
MK2 = {'payments': '1', 'refunds': '3', 'billing_keys': '4', 'reservations': '5', 'outbox_events': '2', 'processed_events': '2', 'idempotency_records': '2'}
cards2 = [card(n, x, y, k, rows, MK2.get(n), ghost=(k == 'ghost')) for n, (x, y, k, rows) in Q.items()]
cards2.append('<div class="zone" style="position:absolute;left:919px;top:618px;width:250px;font-size:14px;font-weight:700;color:#4B4659;line-height:1.4">공통 테이블은 예매 DB와 결제 DB에 각각 있다</div>')
cards2.append('<div style="position:absolute;left:40px;top:118px;font-size:14px;font-weight:800;color:#4B4659">user DB</div>')
cards2.append('<div style="position:absolute;left:333px;top:100px;font-size:14px;font-weight:800;color:#4B4659">payment DB</div>')
L2 = [
    path([(595, 175), (626, 175)]),                                   # payments → histories
    path([(595, 345), (626, 345)]),                                   # payments → refunds (1:0..1)
    path([(302, 200), (333, 200)], None, dashed=True),
    path([(302, 250), (318, 250), (318, 560), (333, 560)], None, dashed=True),
    path([(302, 405), (333, 405)], None, dashed=True),
]
P2 = intents([
    ('1', '결과를 모르면 모른다고 둔다', 'PG 호출 전에 pg_order_id를 저장해, 응답이 없어도 UNKNOWN으로 두고 next_check_at에 다시 조회'),
    ('2', '이벤트는 DB와 함께', 'outbox에 같은 트랜잭션으로 쓰고 릴레이가 발행, processed_events로 중복 처리, 멱등 기록으로 재전송에 같은 응답'),
    ('3', '환불도 한 번만', '결제당 환불 1건 유니크와 PG 멱등키로 중복 요청에도 PG 환불은 한 번'),
    ('4', '카드 정보는 암호화', '빌링키는 AES-256-GCM으로 저장, 키는 환경 변수로만 주입'),
    ('5', 'DB 사이 FK 없음', '서비스마다 DB를 나누고 user_id·reservation_id는 값으로만 연결, 정합성은 이벤트와 대사로 맞춤'),
])
LG2 = legend([('user', 'user DB'), ('pay', 'payment DB'), ('common', '공통')], 40, 858)
open(f'{OUT}/2026-11-18-erd-payment-user.html', 'w', encoding='utf-8').write(page(
    'ERD ② 결제·사용자 DB와 공통 테이블', '결제는 PG를 부르기 전에 주문 번호부터 저장한다. 감사 컬럼과 일부 컬럼 생략(전체는 SA MASTER 12장)', cards2, L2, P2, LG2))
print('ok')
