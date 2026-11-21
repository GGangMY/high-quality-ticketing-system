# 발표 자료 PDF 모음

발표 자료로 쓴 문서(md, html)를 PDF로 뽑은 확인용 인쇄본이다. 내용의 정본은 아니다. 정본은 각 원본 파일(`docs/presentation/` 아래 같은 이름의 `.md`·`.html`)과 그 문서가 링크한 설계·ADR·트러블슈팅 문서다. 내용을 고치려면 원본을 고친 뒤 PDF를 다시 만든다.

- 원본 경로와 PDF 경로는 같은 상대 경로다(확장자만 다름). 예: `performance/2026-11-17-scale-evidence.md` → `pdf/performance/2026-11-17-scale-evidence.pdf`.
- 그림(PNG·SVG)은 PDF로 바꾸지 않았다. 원본 그림 파일을 그대로 쓴다.
- 움직임 HTML(`deployment/2026-11-05-deploy-flow-motion.html`)과 노션 백업 JSON·개요(`brochure/notion-backup/`)는 제외했다.

| 폴더 | 문서 | PDF | 원본 |
|---|---|---|---|
| (루트) | 발표 소스: Gateway 과부하를 측정으로 좁혀 간 기록 (11/9~11/12) | [PDF](2026-11-12-gateway-overload-source.pdf) | `2026-11-12-gateway-overload-source.md` |
| ai-verification | AI가 만든 코드를 어떻게 검증했나 (발표 한 장) | [PDF](ai-verification/2026-11-13-ai-code-review-method.pdf) | `ai-verification/2026-11-13-ai-code-review-method.md` |
| ai-verification | AI 대표 사례 후보 (2026-11-13) | [PDF](ai-verification/2026-11-13-case-candidates.pdf) | `ai-verification/2026-11-13-case-candidates.md` |
| ai-verification | 사례 가안 1. Gateway CPU 포화: AI 추천을 거부하고 실험으로 닫은 뒤 동시 처리 상한 64를 고름 | [PDF](ai-verification/2026-11-13-gateway-overload-ai-rejection.pdf) | `ai-verification/2026-11-13-gateway-overload-ai-rejection.md` |
| ai-verification | 사례 가안 2. 좌석 동시성: AI의 전제 검토는 테스트로 확인해 받고, 측정 도구 제안은 거부함 | [PDF](ai-verification/2026-11-13-seat-concurrency-ai-premise-and-tool.pdf) | `ai-verification/2026-11-13-seat-concurrency-ai-premise-and-tool.md` |
| ai-verification | AI 활용·검증 대표 사례 | [PDF](ai-verification/README.pdf) | `ai-verification/README.md` |
| architecture | 결제 거절 뒤 보상(SAGA) 한 장 요약 | [PDF](architecture/2026-11-14-saga-payment-declined.pdf) | `architecture/2026-11-14-saga-payment-declined.md` |
| architecture | 아키텍처 | [PDF](architecture/README.pdf) | `architecture/README.md` |
| brand | 다이어그램 스타일 | [PDF](brand/diagram-style.pdf) | `brand/diagram-style.md` |
| brand | 아이콘·색 | [PDF](brand/README.pdf) | `brand/README.md` |
| brochure | 10기 다른 조 브로셔 분석 (5조 이선좌 브로셔 반영용) | [PDF](brochure/2026-11-16-10th-brochure-review.pdf) | `brochure/2026-11-16-10th-brochure-review.md` |
| brochure | 단기심화 8기 최종 발표회 브로셔 검토 (우리 브로셔에 가져올 것) | [PDF](brochure/2026-11-16-8th-brochure-review.pdf) | `brochure/2026-11-16-8th-brochure-review.md` |
| brochure | 최종 발표회 브로셔 초안 (5조 이선좌) | [PDF](brochure/2026-11-16-brochure-draft.pdf) | `brochure/2026-11-16-brochure-draft.md` |
| brochure | 이선좌 : 빠른 손 아니어도 추첨으로, 선착순도 같은 좌석은 딱 한 명 | [PDF](brochure/2026-11-16-brochure-notion.pdf) | `brochure/2026-11-16-brochure-notion.md` |
| brochure | 준현 님 판 표기 수정 목록 (블록 단위) | [PDF](brochure/2026-11-16-notion-fix-list.pdf) | `brochure/2026-11-16-notion-fix-list.md` |
| brochure | Notion 브로셔 재구성안 v3 (준현 님 재개편본 → 짧은 메인 + 썸네일 카드 하위 페이지) | [PDF](brochure/2026-11-16-notion-restructure-plan-v3.pdf) | `brochure/2026-11-16-notion-restructure-plan-v3.md` |
| brochure | Notion 브로셔 재구성안 (준현 님 재개편본 → 메인 + 썸네일 하위 페이지) | [PDF](brochure/2026-11-16-notion-restructure-plan.pdf) | `brochure/2026-11-16-notion-restructure-plan.md` |
| brochure | 브로셔 작업을 AI에게 시키는 법 (프롬프트 컨설팅) | [PDF](brochure/2026-11-16-prompt-guide.pdf) | `brochure/2026-11-16-prompt-guide.md` |
| brochure | 브로셔 재디자인 설계 (메인은 이미지, 상세는 하위 페이지) | [PDF](brochure/2026-11-16-redesign-plan.pdf) | `brochure/2026-11-16-redesign-plan.md` |
| brochure/cards | cards-gallery | [PDF](brochure/cards/cards-gallery.pdf) | `brochure/cards/cards-gallery.html` |
| brochure/census | 전수조사 A: 발표 자료·ADR·트러블슈팅 사실 원장 | [PDF](brochure/census/A-presentation-decisions.pdf) | `brochure/census/A-presentation-decisions.md` |
| brochure/census | B. 설계·SA·가이드 문서 전수조사 (사실 원장) | [PDF](brochure/census/B-design-sa.pdf) | `brochure/census/B-design-sa.md` |
| brochure/census | 사실 원장 C: AI 판단 기록과 학습 노트 전수조사 | [PDF](brochure/census/C-ai-learning.pdf) | `brochure/census/C-ai-learning.md` |
| brochure/census | D. 코드·측정 원자료·이력 전수조사 (브로셔 사실 원장) | [PDF](brochure/census/D-code-measure-history.pdf) | `brochure/census/D-code-measure-history.md` |
| brochure/census | E. 저장소 밖 기록 전수조사 (docs/context, 메모리, 세션, Linear) | [PDF](brochure/census/E-context-sessions.pdf) | `brochure/census/E-context-sessions.md` |
| brochure/census | 통합 원장 (브로셔·발표 자료의 정본 소재) | [PDF](brochure/census/LEDGER.pdf) | `brochure/census/LEDGER.md` |
| brochure | 브로셔 디자인 규칙 (design-kit) | [PDF](brochure/design-kit.pdf) | `brochure/design-kit.md` |
| brochure/drafts/fable | decisions-gallery | [PDF](brochure/drafts/fable/decisions-gallery.pdf) | `brochure/drafts/fable/decisions-gallery.html` |
| brochure | 브로셔 붙여 넣기 | [PDF](brochure/notion-paste.pdf) | `brochure/notion-paste.html` |
| brochure | 최종 발표회 브로셔 | [PDF](brochure/README.pdf) | `brochure/README.md` |
| brochure/stories | 01 Gateway: 입구가 먼저 무너졌다 | [PDF](brochure/stories/1-gateway.pdf) | `brochure/stories/1-gateway.md` |
| brochure/stories | 02 대기열: 줄은 공정하게, 순번 조회는 싸게 | [PDF](brochure/stories/2-queue.pdf) | `brochure/stories/2-queue.md` |
| brochure/stories | 03 좌석 선점: 같은 좌석은 한 명, 병목은 계속 옮겨 갔다 | [PDF](brochure/stories/3-seat.pdf) | `brochure/stories/3-seat.md` |
| brochure/stories | 04 결제: 결과를 모를 때, 돈은 한 번만 | [PDF](brochure/stories/4-payment.pdf) | `brochure/stories/4-payment.md` |
| brochure/stories | 05 추첨·자동결제: 빠른 손 아니어도, 당첨되면 결제까지 | [PDF](brochure/stories/5-lottery.pdf) | `brochure/stories/5-lottery.md` |
| considerations | 주요 고려점 | [PDF](considerations/README.pdf) | `considerations/README.md` |
| demo | 시연 | [PDF](demo/README.pdf) | `demo/README.md` |
| deployment | 배포와 운영 | [PDF](deployment/README.pdf) | `deployment/README.md` |
| (루트) | 증명 형식 견본: 다른 조에서 가져온 형식과 우리 적용 위치 | [PDF](evidence-formats.pdf) | `evidence-formats.md` |
| final-script | 발표 대본 전·후 비교 (검토용 초안) | [PDF](final-script/2026-11-18-script-before-after.pdf) | `final-script/2026-11-18-script-before-after.md` |
| final-script | 화면 글 수정 전·후 비교 (v2 대본에 맞춤, 2026-11-19) | [PDF](final-script/2026-11-19-screen-text-before-after.pdf) | `final-script/2026-11-19-screen-text-before-after.md` |
| final-script | 발표 대본 v2 첨삭 제안 (2026-11-19) | [PDF](final-script/2026-11-19-script-v2-proposal.pdf) | `final-script/2026-11-19-script-v2-proposal.md` |
| final-script | 이선좌 예상 질문집 | [PDF](final-script/expected-qna.pdf) | `final-script/expected-qna.html` |
| final-script | 최종 발표 대본 정리 (이어하기 메모, 2026-11-19 갱신) | [PDF](final-script/README.pdf) | `final-script/README.md` |
| final-script/reviews | 대본 검수 공통 지시문 (2026-11-19) | [PDF](final-script/reviews/00-brief.pdf) | `final-script/reviews/00-brief.md` |
| final-script/reviews | 기술 정확성과 꼬리질문 방어 검수 리포트 (Opus) | [PDF](final-script/reviews/01-opus-technical.pdf) | `final-script/reviews/01-opus-technical.md` |
| final-script/reviews | 흐름과 서사 검수 리포트 (Fable 5.2) | [PDF](final-script/reviews/02-fable-flow.pdf) | `final-script/reviews/02-fable-flow.md` |
| final-script/reviews | 문체와 어휘 검수 리포트 (Sonnet 5.5) | [PDF](final-script/reviews/03-sonnet-style.pdf) | `final-script/reviews/03-sonnet-style.md` |
| final-script/reviews | 시간 배분과 화면·말 분업 검수 리포트 (Haiku 5.5) | [PDF](final-script/reviews/04-haiku-time-screen.pdf) | `final-script/reviews/04-haiku-time-screen.md` |
| final-script/reviews | 검수 리포트 사실 대조 (검증) | [PDF](final-script/reviews/05-verify.pdf) | `final-script/reviews/05-verify.md` |
| final-script/reviews | 이선좌 최종 발표 대본 v2 | [PDF](final-script/reviews/final-script-v2.pdf) | `final-script/reviews/final-script-v2.html` |
| final-script | 이선좌 발표 대본 | [PDF](final-script/script-viewer.pdf) | `final-script/script-viewer.html` |
| overview | 발표 소스: Linear로 담당·상태·선후 관계를 보이게 한 협업 (10/26~) | [PDF](overview/2026-11-13-linear-collaboration-source.pdf) | `overview/2026-11-13-linear-collaboration-source.md` |
| overview | 프로젝트 소개 | [PDF](overview/README.pdf) | `overview/README.md` |
| performance | Gateway 동시 처리 상한: 섞인 트래픽에서 안전망 값 정하기 (발표 소스, 2026-11-13) | [PDF](performance/2026-11-13-safety-net-limit-source.pdf) | `performance/2026-11-13-safety-net-limit-source.md` |
| performance | Gateway 과부하 개선 전·후 한 장 (발표용, 2026-11-14) | [PDF](performance/2026-11-14-gateway-overload-one-page.pdf) | `performance/2026-11-14-gateway-overload-one-page.md` |
| performance | 11/15 O1 측정에서 찾은 병목과 개선 후보 정리 (발표·면접용) | [PDF](performance/2026-11-15-bottleneck-improvement-study.pdf) | `performance/2026-11-15-bottleneck-improvement-study.md` |
| performance | Gateway 동시 처리 상한 64가 섞인 트래픽에서 정상 요청까지 거절한 문제 (11/15, ISE-230·ISE-264) | [PDF](performance/2026-11-15-gateway-inflight-limit-troubleshooting.pdf) | `performance/2026-11-15-gateway-inflight-limit-troubleshooting.md` |
| performance | Synthetic 사용자 대 균일 사용자: 같은 서버에서 무엇이 달라졌나 (발표 소스, 2026-11-15) | [PDF](performance/2026-11-15-o1-synthetic-vs-uniform-source.pdf) | `performance/2026-11-15-o1-synthetic-vs-uniform-source.md` |
| performance | 장비 한 대가 감당한 몫: 우리 측정 숫자를 실서비스 규모와 맞대는 법 (발표 소스) | [PDF](performance/2026-11-15-scale-comparison.pdf) | `performance/2026-11-15-scale-comparison.md` |
| performance | 11/15 배포 서버 측정·분석·개선 트러블슈팅 일지 (발표·면접 소스) | [PDF](performance/2026-11-15-troubleshooting-journal.pdf) | `performance/2026-11-15-troubleshooting-journal.md` |
| performance | 규모 근거 측정: 매진·추첨 간섭·대기열 2만 2천 명 (2026-11-17, 배포 서버) | [PDF](performance/2026-11-17-scale-evidence.pdf) | `performance/2026-11-17-scale-evidence.md` |
| performance/img/2026-11-15 | 11/15 배포 서버 측정 그래프 | [PDF](performance/img/2026-11-15/README.pdf) | `performance/img/2026-11-15/README.md` |
| performance | 성능 측정 | [PDF](performance/README.pdf) | `performance/README.md` |
| (루트) | 발표 자료 | [PDF](README.pdf) | `README.md` |
| (루트) | 발제 필수 산출물 점검과 남은 일 | [PDF](required-deliverables.pdf) | `required-deliverables.md` |
| troubleshooting | 트러블슈팅 | [PDF](troubleshooting/README.pdf) | `troubleshooting/README.md` |

총 67개.
