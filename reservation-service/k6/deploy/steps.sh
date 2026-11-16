# 배포 서버 단계 측정의 단계 정의다. build-images.sh와 deploy-run.sh가 읽는다(source).
# 단계마다 덮어쓰기 파일 overlays/<단계>.yml이 하나씩 있다. 코드가 바뀌는 단계만 이미지가 다르다.
# 단계 설명과 각 단계에서 무엇이 바뀌는지: STEPS.md "배포 단계 측정" 단계 표

# 측정 순서. 앞 8개는 ISE-79(K1 단계), 뒤는 ISE-261 이후와 덧붙인 비교(접수형 ISE-296, 풀 ISE-237)다.
# 끝의 base·cur는 같은 단계를 한 번 더 재서 측정 시간대에 따른 흔들림을 본다(사용자 결정, 2026-11-16)
STEP_ORDER="base g1 r1 p4a p4b p4c f pre d1114 l50 one cur lim4 pool8 aout adir base cur"

# 단계 → 이미지 태그
declare -A STEP_IMAGE=(
  [base]=base [g1]=base [r1]=base [p4a]=p4a [p4b]=p4b [p4c]=p4c [f]=f [pre]=pre
  [d1114]=d1114 [l50]=l50 [one]=one [cur]=cur [lim4]=cur [pool8]=cur [aout]=cur [adir]=cur
)

# 이미지 태그 → 측정한 커밋. 이미지 라벨(k6steps.commit)에 남기고, 측정 전에 서버의 이미지와 맞는지 확인한다
# d1114: ISE-261 직전 dev(11/14, ISE-17 머지). l50: 잠금 대기 50ms와 구조 개선(ADR 0061·0062). one: 성능 개선 반복 4(한 문장 사전 판정).
# cur: dev 11/16(#661·#662 머지, 캐시 사전 거절 포함)
# Note: l50·one은 ISE-261 브랜치의 중간 커밋이라 dev에는 squash로만 남았다. 로컬 태그 k6steps/<태그>로 지켜 둔다(build-images.sh)
declare -A IMAGE_COMMIT=(
  [base]=6704969 [p4a]=50a365d [p4b]=d44c729 [p4c]=d3820f5 [f]=5e9e42a [pre]=660abb06
  [d1114]=0f69c1aa [l50]=1806af22 [one]=14cad0dd [cur]=fafa1e42
)
IMAGE_TAGS="base p4a p4b p4c f pre d1114 l50 one cur"

IMAGE_REPO=iseonjwa-k6steps/reservation-service
