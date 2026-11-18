# 예매 시연 영상

발표와 결과 제출에 쓰는 서비스 시연 영상이다. 완성본은 [`../2026-11-18-demo-video.mp4`](../2026-11-18-demo-video.mp4)(48초, 1920×1080, 30fps)이다. 소개 영상(v2)이 이야기로 서비스를 알렸다면, 이 영상은 실제 화면에서 일반 예매 한 번을 처음부터 끝까지 보여 준다.

## 사용자가 정한 것

- 길이: 최대한 짧게, 너무 급하지 않게. 일반 예매 한 흐름만 담는다(추첨·결제 거절은 넣지 않음).
- 화면: 로컬 스택의 실제 화면을 녹화하고, 주소창 없는 브라우저 창 틀에 넣는다. 마우스 커서가 보인다.
- 소리: 밝고 경쾌한 새 배경음악(Kevin MacLeod, CC BY), 클릭·화면 전환·자막 팝·확정 순간에 효과음. 내레이션은 없다.
- 하린: 장면마다 오른쪽 아래에서 짧은 말풍선으로 안내한다.

## 장면

| 시간 | 단계 | 화면 | 하린 말풍선 |
|---|---|---|---|
| 0~3초 | 첫 화면 | 로고, "예매 시연", 점프하는 하린 | |
| 3~11.6초 | STEP 1 공연과 회차 고르기 | 홈의 "티켓 오픈 예정"에서 ASTERIA 공연 → 상세 → 오픈 예정 회차 선택, 카운트다운 00:00:30 | 보고 싶던 공연, 오늘 오픈해요 |
| 11.6~16.6초 | STEP 2 정각에 예매 오픈 | "잠시 뒤" 표시 후 카운트다운 00:00:03 → "지금 오픈되었습니다" → 예매하기. 카운트다운을 확대 | 3, 2, 1… / 열렸다! |
| 16.6~19.8초 | STEP 3 대기열을 거쳐 입장 | "곧 입장합니다" | 줄 선 순서대로 들어가요 |
| 19.8~29.7초 | STEP 4 원하는 좌석 고르기 | 1매 → A구역 → 1열 15번(확대) → 1매 선택 완료 | 원하는 자리를 콕! |
| 29.7~37.1초 | STEP 5 잡아 둔 5분 안에 결제 | "좌석 선택이 완료되었습니다" → 결제 화면 → 결제하기 → 결제 승인 | 고른 자리는 5분 동안 내 거예요 |
| 37.1~44.2초 | STEP 6 예매 확정, 발권 기념 부적까지 | "예매가 확정되었습니다" 티켓 → 부적 QR(확대) | 예매 끝! 부적도 받았어요 |
| 44.2~48.2초 | 엔드카드 | 로고, "공정하고 정확한 예매", 음악 출처 | |

## 사실 확인

- 화면은 꾸미지 않은 실제 동작이다. 2026-11-18 로컬 스택을 최신 dev(`0160192f`)로 다시 빌드해 띄우고, 배포 서버와 같은 시드(`script/deploy/seed-showcase.sh`, `seed-demo.sh`)를 넣은 뒤 샘플 계정으로 예매했다. 백엔드(대기열, 좌석 선점, 결제, 예매 확정)는 모두 실제로 돌았고, 결제는 시연용 Mock PG다.
- 녹화 직전에 40초 뒤 열리는 회차를 만들어(`seed-demo.sh open`) 실제 오픈 카운트다운을 찍었다. 영상에서는 기다린 약 26초(녹화 8.8~34.4초)를 잘라 내고 "잠시 뒤"로 표시했다. 이 컷 하나 말고는 녹화를 이어서 그대로 쓴다.
- 대기열은 혼자 들어가서 순번 없이 "곧 입장합니다"로 바로 지나간다. 많은 사람이 몰렸을 때 순번이 보이는 장면은 소개 영상과 발표 측정 장에 있다.
- 깔끔한 화면을 위해 로컬 DB에서만 예전 확인용 공연 9개와 리허설 회차 4개를 숨겼다(`deleted_at`). 배포 서버와 저장소 코드는 바꾸지 않았다.
- 좌석 지도는 아무도 예매하지 않은 상태라 모든 구역이 "남은 60"이다.

## 만든 방법

| 무엇 | 도구 | 파일 |
|---|---|---|
| 화면 녹화 | Playwright + Chrome DevTools 스크린캐스트. 1280×720 화면을 배율 1.5로 찍어 1920×1080. 화면 안에 커서와 누른 자리의 원을 그린다. 클릭 순간을 `marks`로 남겨 효과음을 맞췄다 | [`tools/record-demo.mjs`](tools/record-demo.mjs), 시각 기록 [`tools/marks-take3.json`](tools/marks-take3.json), 결과 `assets/video/booking.mp4`(세 번째 녹화) |
| 하린 | 소개 영상 v2의 그림을 그대로 쓴다 | `assets/img/harin-*.webp` |
| 로고 | 프론트엔드 파비콘 | `assets/img/logo.svg` |
| 배경음악 | "Carefree" Kevin MacLeod (incompetech.com), Licensed under Creative Commons: By Attribution 4.0 License(http://creativecommons.org/licenses/by/4.0/). 엔드카드에 출처를 적었다 | `assets/music/carefree.mp3`(앞 49초만 잘라 둠) |
| 효과음 | HyperFrames 기본 효과음(클릭, 휙, 팝, 상승음) | 저장소에 넣지 않았다. 아래 명령으로 다시 받는다 |
| 영상 조립 | HyperFrames(HTML을 프레임 단위로 렌더). 설계는 [`SPEC.md`](SPEC.md) | `index.html`, `compositions/` |
| 음량 | 렌더본을 ffmpeg `loudnorm`(목표 -16 LUFS, 피크 -2.5 dBTP)으로 맞췄다. 측정값 -16.0 LUFS, 피크 -1.9 dBTP | |

## 다시 렌더하기(이 폴더에서)

```bash
mkdir -p assets/fonts assets/sfx
cp ../../../../frontend/node_modules/pretendard/dist/web/variable/woff2/PretendardVariable.woff2 assets/fonts/
for i in "soft mouse click" "fast whoosh transition" "pop notification" "riser into impact"; do npx hyperframes media-use resolve --type sfx --intent "$i" --project . --local-only; done
cp .media/audio/sfx/*.mp3 assets/sfx/
npx hyperframes check && npx hyperframes render -q delivery -o renders/demo.mp4
ffmpeg -i renders/demo.mp4 -c:v copy -af loudnorm=I=-16:TP=-2.5:LRA=11 -c:a aac -b:a 192k -ar 48000 ../2026-11-18-demo-video.mp4
```

효과음 파일 이름(`sfx_001`~`sfx_004`)은 위 순서로 받았을 때의 이름이다. 다시 녹화하려면 로컬 스택과 시드를 준비하고 `tools/record-demo.mjs`를 프론트엔드 `node_modules`가 보이는 곳에서 실행한다. 새 녹화는 시각이 달라지므로 `compositions/demo.html`의 시각과 `index.html`의 효과음 시각을 `marks.json`에 맞춰 다시 정한다.

## 남은 것

- 소리는 숫자로만 맞췄다. 귀로 들어 확인하는 것은 준현이 한다.
