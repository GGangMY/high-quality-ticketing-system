# 하린 캐릭터 원본

소개 영상 v2([`../../demo/2026-11-16-intro-video-v2/`](../../demo/2026-11-16-intro-video-v2/README.md))의 주인공 하린을 그린 원본 그림이다. 영상 폴더에는 영상에 쓴 것만 있어서, 인물 시트와 오려 내기 전 그림, 쓰지 않은 장면 그림까지 여기에 모았다. 브로셔·발표 자료·Notion 커버처럼 하린이 다시 필요한 곳에서 같은 인물로 이어 그릴 때 참조로 쓴다.

모두 codex CLI 기본 이미지 생성으로 만든 웹툰·일러스트풍이고, 프롬프트 전문은 [`codex-image-prompts.md`](../../demo/2026-11-16-intro-video-v2/tools/codex-image-prompts.md)에 있다. 파일은 원본 PNG를 무손실 WebP로 바꿨다(화질은 같고 용량이 줄고, 오려 낸 그림의 투명 배경은 그대로다).

인물: 20대 초반 대학생, 어깨까지 오는 짙은 갈색 단발과 앞머리, 분홍(`#FF2D78`) 오버사이즈 후드, 하늘색 청바지, 흰 운동화.

## sheets: 인물 시트 (1536×1024, 포즈 C는 1024×1536)

| 파일 | 내용 |
|---|---|
| [harin-sheet-a.webp](sheets/harin-sheet-a.webp) | 앞·3/4·옆·뒤 전신 4면. 다른 그림의 얼굴·옷 기준 |
| [harin-sheet-b.webp](sheets/harin-sheet-b.webp) | 표정 6개 반신(긴장, 낙담, 환호, 당황, 안도, 놀람) |
| [harin-pose-c.webp](sheets/harin-pose-c.webp) | 두 팔을 번쩍 든 점프 전신. 스쿼시 앤 스트레치용 |

## cutouts: 오려 낸 하린 (투명 배경)

시트에서 평면 바탕을 지워 낸 것이다(`cutout.py`). 영상에는 이 중 일부를 `assets/img/harin-*.webp`로 줄여 썼다.

| 파일 | 내용 |
|---|---|
| front, back | 앞·뒤 전신 |
| bust-tense, bust-focus, bust-dejected, bust-joy, bust-panic, bust-relief, bust-surprise | 표정별 반신. `bust-focus`는 영상용으로 다시 그린 판 |
| jump, jump-fists | 점프(`jump-fists`는 주먹을 쥔 판) |
| thumbs | 엄지척 |

## keys: 장면 그림 (1536×1024)

영상 장면의 바탕이 되는 키 비주얼이다. 위아래 80px은 16:9로 자를 때 버리는 여백이다. 같은 번호가 둘이면 앞의 것이 첫 판이고 뒤의 것이 영상에 쓴 판이다.

| 파일 | 장면 |
|---|---|
| key-01-before-open → key-01-desk | 오픈 직전 밤, 하린의 방 (뒤 판은 노트북 앞) |
| key-02-last-year → key-02-desk-lastyear | 작년의 기억, 흑백 회상 |
| key-03-got-it | 잡았다, 노란 바탕 점프. 영상에서는 오려 낸 점프 컷으로 대신했다 |
| key-04-concert-day → key-04-concert-day-crown | 공연 날 뒷모습 (뒤 판은 응원봉이 왕관 모양) |
| key-05-charm-burst | 예매 완료 폰과 부적 카드. 영상에서는 앱 부적 코드로 그린 카드로 대신했다 |
| key-06-classroom | 다음 날 아침 강의실 |
| key-07-tap → key-07-laptop | 예매 버튼을 누르는 장면 (뒤 판은 노트북) |
