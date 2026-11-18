# 서비스 소개 겸 시연 영상

발표와 결과 제출에 쓰는 소개 겸 시연 영상이다. 완성본은 [`../2026-11-18-demo-video.mp4`](../2026-11-18-demo-video.mp4)(1분 43초, 1920×1080, 30fps)이다. 소개 영상 v2([`../2026-11-16-intro-video-v2/`](../2026-11-16-intro-video-v2/README.md))의 애니메이션 장면을 그대로 살리고, 그 사이에 로컬 스택에서 찍은 실제 화면 네 개(토스페이먼츠 결제창, 추첨 응모, AI 예매 상담, 운영자 화면)를 끼웠다.

## 어떻게 이 판이 됐나

1. 48초짜리 일반 예매 시연(판 1)을 만들었다.
2. 사용자가 "토스페이먼츠 연결과 이것저것 더, 소개와 시연을 같이, 추첨 응모·당첨도"를 요청해 다시 기획했다. 세 기획안 중 A "하린의 예매 하루"로 2분 26초 판(판 2)을 만들었다. 기획안은 [`STORYLINES.md`](STORYLINES.md)에 있다.
3. 사용자가 판 2를 보고 "애니메이션처럼 나오던 장면은 다 살리고, 애니메이션 + 시연 영상 정도로. 슬라이드 일부를 가져와 설명하는 장면은 필요 없다(발표 때 말한다)"고 정했다. 그래서 v2를 뼈대로 다시 조립했다(이 판).
4. 이어서 운영자 화면을 넣어 달라고 해 운영자 장면을 더했다.

## 사용자가 정한 것

- v2의 애니메이션 장면(오픈 직전, 작년의 기억, 탭, 대기열, 좌석, 잡았다, 결제 다시, 추첨, 공연 날, 부적, 엔드카드)은 모두 살린다.
- v2의 숫자 장면(같은 좌석 100명 → 1명, 초당 2,000건 → 0.043초)은 뺀다. 숫자는 발표 슬라이드에서 말한다.
- 판 2의 "억울한 일 셋", "이선좌의 해법 셋", "화면 뒤 구조와 숫자" 같은 슬라이드형 장면은 넣지 않는다.
- 토스페이먼츠는 결제창만 보여 준다. 테스트 모드여도 카드사 인증(휴대폰·생년월일)이 필요해서 인증 없이 닫고, 그 사실을 화면 아래에 적는다.
- 더 보여 줄 기능: AI 예매 상담, 운영자 화면.
- 부적 내레이션은 사용자가 쓴 문장 "예매를 마치면 나만의 부적도 받을 수 있습니다. 접속해서 예매를 완료하고, 부적 하나씩 받아가세요!"를 그대로 쓴다.
- 하린 대사는 v2 녹음을 다시 쓴다.

## 장면

| 시간 | 장면 | 화면 | 소리 |
|---|---|---|---|
| 0~3.6초 | 오픈 직전 | (v2) 밤, 노트북 앞 하린, 카운트다운 | 하린 "이번엔 절대 못 놓쳐!" |
| 3.6~6.5초 | 작년의 기억 | (v2) 회색 회상, "이미 선택된 좌석입니다" 알림 | 하린 "작년엔 누르는 자리마다 다 나갔었지…" |
| 6.5~13.1초 | 탭 | (v2) 노트북 화면의 예매하기 → 이선좌 | n01 |
| 13.1~22.5초 | 대기열 | (v2) 브라우저 창 녹화, 순번 확대 | n02 |
| 22.5~28.1초 | 좌석, 잡았다 | (v2) "좌석 선택이 완료되었습니다" → 점프 | n03, 하린 "잡았다!" |
| 28.1~36.1초 | 토스 결제창 | (실제) 결제하기 → 토스페이먼츠 테스트 결제창 확대 → 닫기. 아래에 "실제 토스페이먼츠 테스트 결제창 · 영상에서는 카드 인증 없이 닫음" | 새 내레이션 "결제는 토스페이먼츠와 연결되어 있습니다." |
| 36.1~46.5초 | 결제 다시 | (v2) "결제사 연결이 원활하지 않습니다" → 다시 결제 → 확정 | 하린 "어? 결제가 안 되네?", n04 |
| 46.5~56.7초 | 추첨 | (실제) 추첨 응모 화면 → 1매 응모 → (v2) 다음 날 아침 강의실 당첨 알림 | n05, 하린 "자는 사이에 당첨에, 결제까지?" |
| 56.7~69.4초 | 예매 상담 | (실제) 예매 문의 창에 "추첨에 당첨되면 결제는 어떻게 되나요?" → 규정 근거와 함께 답변. 하린 긴장 → 안도 | 새 내레이션 "궁금한 점은 예매 상담에 물어보세요. 예매 규정을 찾아 근거와 함께 답합니다." |
| 69.4~84.6초 | 운영자 화면 | (실제) 운영 홈 → 공연·회차 → 추첨 설정 → 시연 장애 패널에서 장애 걸기·해제. 오른쪽 체크 목록 셋이 차례로 켜진다 | 새 내레이션 "운영자 화면에서는 공연과 회차, 추첨을 만들고, 시연용 결제 장애도 직접 걸어 볼 수 있습니다." |
| 84.6~91.2초 | 공연 날 | (v2) 왕관 응원봉 뒷모습 → 폰 속 티켓 → 끝 문장 | 하린 "빅빵, 기다려! 내가 간다!", n07 "공정하고 정확한 예매. 이선좌." |
| 91.2~99.2초 | 부적 | (v2) 예매 완료 QR → 부적 5장과 폭죽 | 새 내레이션(사용자 문장) |
| 99.2~103.2초 | 엔드카드 | 로고, "공정하고 정확한 예매", 음악 출처 | |

v2 대사 전문은 [`../2026-11-16-intro-video-v2/tools/narration-lines.tsv`](../2026-11-16-intro-video-v2/tools/narration-lines.tsv)에 있다. 이 판에서 쓰지 않은 v2 줄은 n06(숫자)과 n08(부적, 사용자 문장으로 바꿈)이다.

## 사실 확인

- (v2)로 적은 장면의 화면 녹화는 v2 그대로다. 프론트엔드 목(MSW) 모드 녹화이고, 사실 확인은 v2 README에 있다.
- 결제 다시 장면은 v2 목 녹화를 쓴다. "결제사 연결이 원활하지 않습니다"는 승인 서킷 브레이커가 열려야 나오는 화면이고, 최근 승인 20건 중 절반 넘게 실패해야 열려서 실제 스택에서 한 번의 녹화로 만들기 어렵다.
- (실제)로 적은 네 장면은 2026-11-18 로컬 스택을 최신 dev(`0160192f`)로 다시 빌드하고, 배포 서버와 같은 시드(`seed-showcase.sh`, `seed-demo.sh`)를 넣은 뒤 샘플 계정으로 찍었다. 결제 서비스는 `PAYMENT_PG_PROVIDER=toss`, `PAYMENT_PG_MOCK_BYPASS=true`로, Mock PG는 장애 주입이 열리는 `loadtest` 프로필(`loadtest/k6/compose.mockpg-loadtest.yml`)로 띄웠다.
- 토스페이먼츠 결제창은 실제 테스트 결제창(`payment-gateway-sandbox.tosspayments.com`)이다.
- 추첨은 `seed-demo.sh lottery`로 응모 3분 뒤 시작하는 추첨을 만들었다. 이 시드는 공연 이름을 "k6 측정 추첨"으로 만들어서, 로컬 DB에서만 그 회차(50)를 대표 공연(20)으로 옮겼다. 녹화는 쓰는 두 구간만 이어 붙여 두었다(원본 0~34초 + 263~274.3초).
- 예매 상담은 공연 정보가 아니라 예매 규정 문서를 찾아 답한다. 그래서 공연 질문 대신 규정에 있는 질문을 골랐다.
- v2 장면과 이어지도록 실제 화면 녹화 동안만 로컬 DB의 공연 20 이름을 "빅빵 2026 월드투어 (BIG BBANG)"으로 바꿨고, 녹화 뒤 원래 이름(ASTERIA)으로 되돌렸다. 결제 서비스도 녹화 뒤 Mock 모드로, Mock PG는 기본 프로필로 되돌렸다. 배포 서버와 저장소 코드는 바꾸지 않았다.
- 깔끔한 화면을 위해 로컬 DB에서만 예전 확인용 공연 9개와 리허설 회차 4개를 숨겼다.

## 만든 방법

| 무엇 | 도구 | 파일 |
|---|---|---|
| v2 장면 | 소개 영상 v2의 장면 파일·그림·녹화·목소리를 가져왔다. 추첨 장면만 앞부분을 실제 녹화로 바꾸고 뒤 강의실 컷을 2.8초 늦췄다 | `compositions/`(open, lastyear, tap, queue, seats, gotit, pay, lottery, concert, charm, endcard), `assets/` |
| 실제 화면 녹화 | Playwright + Chrome DevTools 스크린캐스트. 1280×720 화면을 배율 1.5로 찍어 1920×1080. 화면 안에 커서와 누른 자리의 원을 그리고(`tools/cursor.js`), 클릭 순간을 기록해 효과음을 맞춘다 | `tools/record-{toss,lottery,assist,admin}.mjs`, 시각 기록 `tools/marks-*.json`, 결과 `assets/video/real-*.mp4` |
| 새 장면 | 결제 장면과 같은 틀(브라우저 창, 색 원, 하린 상반신)에 실제 녹화를 넣고 필요한 곳만 확대 | `compositions/toss.html`, `assist.html`, `admin.html` |
| 새 내레이션 | 로컬 VoiceStudio(OmniVoice). v2 내레이터 녹음 n01을 참조로 복제(`effect_preset=raw`, 품질 단계 48, `class_temperature` 0.6). whisper로 받아쓰기를 확인했다 | `assets/voice/new-*.mp3`(앞뒤 무음 제거, -16 LUFS) |
| 배경음악 | "Life of Riley" Kevin MacLeod (incompetech.com), Licensed under Creative Commons: By Attribution 4.0 License(http://creativecommons.org/licenses/by/4.0/). 엔드카드에 출처를 적었다 | `assets/music/life-of-riley.mp3` |
| 효과음 | HyperFrames 기본 효과음(클릭, 휙, 팝, 째깍, 폭죽) | 저장소에 넣지 않았다. 아래 명령으로 다시 받는다 |
| 영상 조립 | HyperFrames. 설계는 [`SPEC.md`](SPEC.md) | `index.html`, `compositions/` |
| 음량 | 렌더본을 ffmpeg `loudnorm`(목표 -16 LUFS, 피크 -2.5 dBTP)으로 맞췄다 | |

## 다시 렌더하기(이 폴더에서)

```bash
mkdir -p assets/fonts assets/sfx
cp ../../../../frontend/node_modules/pretendard/dist/web/variable/woff2/PretendardVariable.woff2 assets/fonts/
for i in "soft mouse click" "fast whoosh transition" "pop notification" "soft clock tick" "party popper confetti burst" "whoosh swipe" "pop bubble"; do npx hyperframes media-use resolve --type sfx --intent "$i" --project . --local-only; done
cp .media/audio/sfx/*.mp3 assets/sfx/
npx hyperframes check && npx hyperframes render -q delivery -o renders/demo.mp4
ffmpeg -i renders/demo.mp4 -c:v copy -af loudnorm=I=-16:TP=-2.5:LRA=11 -c:a aac -b:a 192k -ar 48000 ../2026-11-18-demo-video.mp4
```

효과음 파일 이름(`sfx_001`~`sfx_007`)은 위 순서로 받았을 때의 이름이다(v2와 같다). 녹화 스크립트는 프론트엔드 `node_modules`가 보이는 곳에서 실행하고, 샘플 계정은 환경 변수로 넘긴다. 다시 녹화하면 시각이 달라지므로 장면 파일의 `data-media-start`와 `index.html`의 클릭 효과음 시각을 새 `tools/marks-*.json`에 맞춘다.

## 남은 것

- 소리는 숫자로만 맞췄다. 귀로 들어 확인하는 것은 준현이 한다.
