"""시연 장면 파일(compositions/scene-*.html), 자막(compositions/captions.html), 루트(index.html)를 만든다.

녹화 시각(tools/marks-*.json)과 목소리 길이(assets/voice/*.mp3)를 기준으로 시간표를 계산한다.
  python3 tools/build.py   (이 폴더에서)
"""
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent


def dur(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(ROOT / path)],
                         capture_output=True, text=True).stdout.strip()
    return round(float(out), 2)


def marks(name):
    d = json.loads((ROOT / f'tools/marks-{name}.json').read_text())
    return [m['t'] - d['firstFrame'] for m in d['marks'] if m['label'] == 'click']


# 내레이션(n*)과 하린(v2-h*) 대사. 자막은 내레이션만 단다(하린 대사는 말풍선)
VO = {
    'n1': '티켓 오픈 정각, 억울한 일은 늘 세 가지입니다. 손 빠른 사람이 먼저 들어가고, 내 차례인지 모르고, 결제하다 좌석이 풀립니다.',
    'n2': '이선좌는 대기열로 줄을 세우고, 같은 좌석은 한 사람에게만 팔고, 좌석 일부는 추첨으로 나눕니다.',
    'n3': '정각이 되면 예매가 열리고, 대기열을 거쳐 순서대로 좌석 선택으로 들어갑니다.',
    'n4': '고른 좌석은 5분 동안 내 자리로 잡아 둡니다.',
    'n5': '결제는 토스페이먼츠와 연결되어 있습니다.',
    'n6': '결제사 응답이 늦어도 걱정하지 마세요. 결제 결과를 다시 확인해 예매를 확정합니다.',
    'n7': '오픈 시간에 맞추기 어렵다면 추첨에 응모해 두세요. 당첨되면 좌석 배정과 결제까지 자동으로 끝납니다.',
    'n8': '궁금한 점은 예매 상담에 물어보세요. 예매 규정을 찾아 근거와 함께 답합니다.',
    'n9': '예매를 마치면 나만의 부적도 받을 수 있습니다. 접속해서 예매를 완료하고, 부적 하나씩 받아가세요!',
    'n10': '이 모든 과정은 서버 한 대 위에서 돌아갑니다. 2만 2천 명이 줄을 서도 순번 확인은 대부분 0.02초 안에, 좌석의 여덟 배가 몰린 매진에서도 중복 판매는 0건이었습니다.',
    'v2-n07': '공정하고 정확한 예매. 이선좌.',
}
HARIN = {'v2-h01': '이번엔 절대 못 놓쳐!', 'v2-h03': '잡았다!', 'v2-h04': '어? 결제가 안 되네?', 'v2-h05': '자는 사이에 당첨에, 결제까지?'}
D = {k: dur(f'assets/voice/{k}.mp3') for k in list(VO) + list(HARIN)}

# 녹화 구간: (파일, 녹화 시작, 녹화 끝). 같은 장면 안에서는 이어 붙이고, 구간 사이에 "잠시 뒤" 같은 표시를 띄운다
SCENES = [
    dict(id='s-open', chip='시연 1', title='오픈 정각, 대기열을 거쳐 좌석까지', clips=[('booking', 0.2, 8.8), ('booking', 33.8, 56.3)],
         jumps=[(1, '잠시 뒤')], harin=[('focus', 0), ('joy', ('booking', 53.4))], bubbles=[('v2-h03', ('booking', 53.5))],
         zooms=[(('booking', 34.0), 1.4, '84% 24%', ('booking', 37.9)), (('booking', 48.6), 1.6, '36% 79%', ('booking', 50.6))]),
    dict(id='s-pay', chip='시연 2', title='토스페이먼츠 결제, 응답이 늦어도 확정', clips=[('booking', 56.3, 73.8), ('booking', 88.8, 93.6)],
         jumps=[(1, '잠시 뒤')], harin=[('focus', 0), ('panic', ('booking', 68.4)), ('joy', ('booking', 90.3))],
         bubbles=[('v2-h04', ('booking', 68.6))],
         notes=[(('booking', 59.4), ('booking', 65.6), '실제 토스페이먼츠 테스트 결제창 · 영상은 카드 인증 없이 시연용 결제로 이어 갑니다')],
         zooms=[(('booking', 69.0), 1.5, '83% 60%', ('booking', 73.8))]),
    dict(id='s-lottery', chip='시연 3', title='추첨 응모, 당첨되면 자동결제', clips=[('lottery', 0.3, 7.0), ('lottery', 25.5, 32.0), ('lottery', 34.0, 45.3)],
         jumps=[(1, '응모 시작'), (2, '추첨 시각')], harin=[('relief', 0), ('joy', ('lottery', 38.5))],
         bubbles=[('v2-h05', ('lottery', 38.8))],
         zooms=[(('lottery', 38.9), 1.45, '80% 22%', ('lottery', 45.3))]),
    dict(id='s-assist', chip='시연 4', title='AI 예매 상담', clips=[('assist', 0.3, 15.2)], jumps=[], harin=[('focus', 0)], bubbles=[],
         zooms=[(('assist', 6.6), 1.3, '84% 40%', ('assist', 15.2))]),
    dict(id='s-charm', chip='시연 5', title='예매를 마치면 발권 기념 부적', clips=[('booking', 93.6, 103.0)], jumps=[], harin=[('thumbs', 0)], bubbles=[],
         zooms=[(('booking', 94.1), 1.45, '31% 73%', ('booking', 96.6))]),
]
IMG = {'focus': 'harin-bust-focus.webp', 'joy': 'harin-bust-joy.webp', 'relief': 'harin-bust-relief.webp',
       'panic': 'harin-bust-panic.webp', 'thumbs': 'harin-thumbs.webp'}
CLICKS = {k: marks(k) for k in ('booking', 'lottery', 'assist')}


def local_of(scene, ref):
    """녹화 시각(파일, 초)을 장면 안 시각으로 바꾼다. 그 녹화 구간 안에 있어야 한다"""
    src, t = ref
    acc = 0.0
    for s, a, b in scene['clips']:
        if s == src and a - 1e-6 <= t <= b + 1e-6:
            return round(acc + (t - a), 2)
        acc += b - a
    raise ValueError((scene['id'], ref))


def scene_len(scene):
    return round(sum(b - a for _, a, b in scene['clips']), 2)


CSS = '''
    @font-face { font-family: 'Pretendard'; src: url('assets/fonts/PretendardVariable.woff2') format('woff2'); font-weight: 100 900; }
    #root { position: absolute; inset: 0; background: #F4F0E6; font-family: 'Pretendard', sans-serif; overflow: hidden; color: #120F1A; }
    .blob { position: absolute; border-radius: 50%; }
    .bl1 { left: 1360px; top: 520px; width: 820px; height: 820px; background: radial-gradient(closest-side, rgba(255,210,63,0.5), rgba(255,210,63,0)); }
    .bl2 { left: 1400px; top: -260px; width: 700px; height: 700px; background: radial-gradient(closest-side, rgba(47,59,232,0.22), rgba(47,59,232,0)); }
    .head { position: absolute; left: 64px; top: 40px; display: flex; align-items: center; gap: 20px; }
    .head .no { font-size: 30px; font-weight: 800; color: #FFFFFF; background: #2F3BE8; border: 3px solid #120F1A; border-radius: 12px; box-shadow: 5px 5px 0 #120F1A; padding: 6px 16px 8px; }
    .head .t { font-size: 50px; font-weight: 900; letter-spacing: -2px; }
    .br { position: absolute; left: 64px; top: 132px; width: 1446px; border: 3px solid #120F1A; border-radius: 22px; background: #120F1A; box-shadow: 14px 14px 0 #120F1A; overflow: hidden; }
    .bar { height: 44px; display: flex; align-items: center; gap: 10px; padding: 0 18px; background: #FFD23F; border-bottom: 3px solid #120F1A; }
    .bar i { display: block; width: 14px; height: 14px; border-radius: 50%; border: 2px solid #120F1A; }
    .bar span { margin-left: 14px; font-size: 19px; font-weight: 800; color: #120F1A; }
    .screen { position: relative; width: 1440px; height: 810px; overflow: hidden; background: #FAFAFC; }
    .zoom { position: absolute; inset: 0; }
    .zoom video { position: absolute; left: 0; top: 0; width: 1440px; height: 810px; object-fit: cover; }
    .jump { position: absolute; left: 0; top: 0; width: 1440px; height: 810px; }
    .jump .in { position: absolute; left: 540px; top: 330px; width: 360px; text-align: center; font-size: 40px; font-weight: 900; color: #FFFFFF; background: #120F1A; border-radius: 999px; padding: 18px 0 22px; }
    .note { position: absolute; left: 0; top: 0; width: 1440px; height: 810px; }
    .note .in { position: absolute; left: 24px; top: 20px; font-size: 28px; font-weight: 800; color: #120F1A; background: #FFD23F; border: 3px solid #120F1A; border-radius: 12px; box-shadow: 5px 5px 0 #120F1A; padding: 8px 18px 10px; }
    .harin { position: absolute; left: 1545px; top: 600px; width: 340px; height: 440px; }
    .harin img { position: absolute; left: 0; bottom: 0; width: 340px; height: 440px; object-fit: contain; object-position: bottom; }
    .bub { position: absolute; left: 1540px; top: 380px; width: 344px; }
    .bub .in { position: relative; background: #FFFFFF; border: 3px solid #120F1A; border-radius: 22px; box-shadow: 6px 6px 0 #120F1A; padding: 20px 22px 22px; word-break: keep-all; font-size: 34px; font-weight: 900; line-height: 1.3; letter-spacing: -0.8px; color: #D11F5E; }
    .bub .in::after { content: ''; position: absolute; left: 150px; bottom: -19px; width: 30px; height: 30px; background: #FFFFFF; border-right: 3px solid #120F1A; border-bottom: 3px solid #120F1A; transform: rotate(45deg); }
'''


def scene_html(sc):
    L = scene_len(sc)
    parts, tw = [], []
    parts.append(f'<div class="blob bl1" data-layout-allow-overflow></div><div class="blob bl2" data-layout-allow-overflow></div>')
    parts.append(f'<div class="head"><p class="no">{sc["chip"]}</p><p class="t" data-var-text>{sc["title"]}</p></div>')
    vids, acc = [], 0.0
    for i, (src, a, b) in enumerate(sc['clips']):
        vids.append(f'<video id="{sc["id"]}-v{i}" class="clip" src="assets/video/{src}.mp4" data-start="{acc:.2f}" data-duration="{b - a:.2f}" data-media-start="{a:.2f}" muted playsinline data-track-index="1"></video>')
        acc += b - a
    jumps = []
    for k, (ci, text) in enumerate(sc['jumps']):
        t = sum(b - a for _, a, b in sc['clips'][:ci])
        jid = f'{sc["id"]}-j{k}'
        jumps.append(f'<div id="{jid}" class="jump clip" data-start="{t - 0.15:.2f}" data-duration="1.2" data-track-index="3"><p class="in">{text}</p></div>')
        tw.append(f"tl.fromTo('#{jid} .in', {{ scale: 0.7, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.25, ease: 'back.out(2)' }}, {t - 0.15:.2f});")
        tw.append(f"tl.to('#{jid} .in', {{ opacity: 0, duration: 0.25, ease: 'power2.in' }}, {t + 0.75:.2f});")
    notes = []
    for k, (r1, r2, text) in enumerate(sc.get('notes', [])):
        a, b = local_of(sc, r1), local_of(sc, r2)
        nid = f'{sc["id"]}-n{k}'
        notes.append(f'<div id="{nid}" class="note clip" data-start="{a:.2f}" data-duration="{b - a:.2f}" data-track-index="4"><p class="in">{text}</p></div>')
        tw.append(f"tl.fromTo('#{nid} .in', {{ y: -20, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: 'power3.out' }}, {a:.2f});")
    for z0, s, origin, z1 in sc['zooms']:
        a, b = local_of(sc, z0), local_of(sc, z1)
        tw.append(f"tl.to('#{sc['id']}-zoom', {{ scale: {s}, transformOrigin: '{origin}', duration: 0.45, ease: 'power2.inOut' }}, {a:.2f});")
        if b < L - 0.3:
            tw.append(f"tl.to('#{sc['id']}-zoom', {{ scale: 1, duration: 0.45, ease: 'power2.inOut' }}, {b - 0.45:.2f});")
    parts.append(f'<div class="br"><div class="bar"><i style="background:#FF3D7F"></i><i style="background:#FFFFFF"></i><i style="background:#7EE0D4"></i><span data-layout-ignore>이선좌 · 콘서트 예매</span></div><div class="screen"><div id="{sc["id"]}-zoom" class="zoom" data-layout-allow-overflow>{"".join(vids)}</div>{"".join(jumps)}{"".join(notes)}</div></div>')
    hs = []
    for k, (pose, ref) in enumerate(sc['harin']):
        a = 0.0 if ref == 0 else local_of(sc, ref)
        b = L if k + 1 == len(sc['harin']) else local_of(sc, sc['harin'][k + 1][1])
        hid = f'{sc["id"]}-h{k}'
        hs.append(f'<div id="{hid}" class="harin clip" data-start="{a:.2f}" data-duration="{b - a:.2f}" data-track-index="5"><img src="assets/img/{IMG[pose]}" alt="" /></div>')
        tw.append(f"tl.fromTo('#{hid} img', {{ y: 40, scaleY: 0.9 }}, {{ y: 0, scaleY: 1, transformOrigin: '50% 100%', duration: 0.4, ease: 'back.out(2)' }}, {a:.2f});")
    parts += hs
    for k, (vo, ref) in enumerate(sc['bubbles']):
        a = local_of(sc, ref)
        bid = f'{sc["id"]}-b{k}'
        parts.append(f'<div id="{bid}" class="bub clip" data-start="{a:.2f}" data-duration="{min(D[vo] + 1.6, L - a):.2f}" data-track-index="6"><p class="in">{HARIN[vo]}</p></div>')
        tw.append(f"tl.fromTo('#{bid} .in', {{ scale: 0.7, opacity: 0, transformOrigin: '45% 110%' }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: 'back.out(2.2)' }}, {a:.2f});")
    tw.insert(0, "tl.fromTo('.head', { x: -50, opacity: 0 }, { x: 0, opacity: 1, duration: 0.4, ease: 'power4.out' }, 0.05);")
    html = f'''<template>
  <style>{CSS}  </style>
  <div id="root" data-composition-id="{sc["id"]}" data-width="1920" data-height="1080">
    {chr(10).join("    " + p for p in parts).strip()}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {chr(10).join("    " + t for t in tw).strip()}
    window.__timelines['{sc["id"]}'] = tl;
  </script>
</template>
'''
    (ROOT / f'compositions/{sc["id"]}.html').write_text(html)
    return L


# 전체 시간표: (장면 id, 길이, 내레이션 목록[(목소리, 장면 안 시각)])
timeline = []
timeline.append(('hook', 4.0, [('v2-h01', 0.7)]))
timeline.append(('problem', round(D['n1'] + 2.4, 2), [('n1', 0.3)]))
timeline.append(('solution', round(D['n2'] + 2.4, 2), [('n2', 0.4)]))
lens = {sc['id']: scene_html(sc) for sc in SCENES}
op = SCENES[0]
timeline.append(('s-open', lens['s-open'], [('n3', local_of(op, ('booking', 33.9))), ('v2-h03', local_of(op, ('booking', 53.5))), ('n4', local_of(op, ('booking', 54.5)))]))
pay = SCENES[1]
timeline.append(('s-pay', lens['s-pay'], [('n5', local_of(pay, ('booking', 59.7))), ('v2-h04', local_of(pay, ('booking', 68.6))), ('n6', local_of(pay, ('booking', 70.2)))]))
lo = SCENES[2]
timeline.append(('s-lottery', lens['s-lottery'], [('n7', 0.3), ('v2-h05', local_of(lo, ('lottery', 38.8)))]))
timeline.append(('s-assist', lens['s-assist'], [('n8', 6.4)]))
timeline.append(('s-charm', lens['s-charm'], [('n9', 0.3)]))
timeline.append(('behind', round(D['n10'] + 1.3, 2), [('n10', 0.5)]))
timeline.append(('endcard', 4.6, [('v2-n07', 0.4)]))

hosts, audio, caps, kinds = [], [], [], []
t = 0.0
starts = {}
for sid, L, vos in timeline:
    starts[sid] = t
    hosts.append(f'      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{t:.2f}" data-duration="{L:.2f}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>')
    for vo, at in vos:
        g = t + at
        audio.append(f'      <audio id="vo-{vo}" class="clip" src="assets/voice/{vo}.mp3" data-start="{g:.2f}" data-duration="{D[vo]:.2f}" data-track-index="2" data-volume="1"></audio>')
        if vo in VO and vo != 'v2-n07':  # 끝 문장은 엔드카드 글자와 같아서 자막을 달지 않는다
            caps.append((g, D[vo], VO[vo]))
    t += L
TOTAL = round(t, 2)

# 효과음: 화면 속 클릭(피크가 한 프레임 뒤), 장면 전환 휙, 당첨·확정 상승음
sfx = []
for sc in SCENES:
    base = starts[sc['id']]
    acc = 0.0
    for src, a, b in sc['clips']:
        for c in CLICKS[src]:
            if a <= c <= b:
                sfx.append(('sfx_001', base + acc + (c - a) - 0.04, 0.37, 1.4))
        acc += b - a
for sid in [s for s, _, _ in timeline][1:]:
    sfx.append(('sfx_002', starts[sid] - 0.13, 0.57, 0.7))
sfx.append(('sfx_004', starts['s-pay'] + local_of(pay, ('booking', 90.33)) - 3.44, 4.3, 0.3))
sfx.append(('sfx_003', starts['s-lottery'] + local_of(lo, ('lottery', 38.5)) - 0.2, 1.4, 0.75))
for i, (f, s, d, v) in enumerate(sorted(sfx, key=lambda x: x[1])):
    audio.append(f'      <audio id="sfx-{i}" class="clip" src="assets/sfx/{f}.mp3" data-start="{s:.2f}" data-duration="{d}" data-track-index="{3 + i % 3}" data-volume="{v}"></audio>')

# 자막 한 장면: 내레이션마다 한 묶음
cap_items, cap_tw = [], []
for i, (g, d, text) in enumerate(caps):
    cap_items.append(f'    <div id="cap{i}" class="cap clip" data-start="{g:.2f}" data-duration="{d + 0.3:.2f}" data-track-index="1"><p class="in">{text}</p></div>')
    cap_tw.append(f"    tl.fromTo('#cap{i} .in', {{ y: 16, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.25, ease: 'power3.out' }}, {g:.2f});")
(ROOT / 'compositions/captions.html').write_text(f'''<template>
  <style>
    @font-face {{ font-family: 'Pretendard'; src: url('assets/fonts/PretendardVariable.woff2') format('woff2'); font-weight: 100 900; }}
    #root {{ position: absolute; inset: 0; font-family: 'Pretendard', sans-serif; pointer-events: none; }}
    .cap {{ position: absolute; left: 160px; top: 880px; width: 1600px; text-align: center; }}
    .cap .in {{ display: inline-block; max-width: 1500px; background: rgba(18,15,26,0.86); color: #FFFFFF; font-size: 34px; font-weight: 700; line-height: 1.4; letter-spacing: -0.5px; padding: 12px 28px 14px; border-radius: 16px; word-break: keep-all; }}
  </style>
  <div id="root" data-composition-id="captions" data-width="1920" data-height="1080">
{chr(10).join(cap_items)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join(cap_tw)}
    window.__timelines['captions'] = tl;
  </script>
</template>
''')

(ROOT / 'index.html').write_text(f'''<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      @font-face {{ font-family: 'Pretendard'; src: url('assets/fonts/PretendardVariable.woff2') format('woff2'); font-weight: 100 900; }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #F4F0E6; font-family: 'Pretendard', sans-serif; }}
      #root {{ position: relative; width: 100%; height: 100%; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
{chr(10).join(hosts)}
      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{TOTAL}" data-track-index="9" data-track-kind="captions" data-width="1920" data-height="1080"></div>

      <audio id="bgm" class="clip" src="assets/music/carefree.mp3" data-start="0" data-duration="{TOTAL}" data-media-start="0" data-track-index="11" data-volume="0.32" data-fade-in="0.3" data-fade-out="3"></audio>
{chr(10).join(audio)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
''')
print('total', TOTAL)
for sid, L, vos in timeline:
    print(f'{starts[sid]:7.2f} {sid:10s} {L:6.2f}', ' '.join(f'{v}@{a:.1f}+{D[v]:.1f}' for v, a in vos))
