// 시연 영상용 실제 화면 녹화(로컬 스택, 실제 백엔드). 한 번의 일반 예매를 처음부터 끝까지 찍는다.
// CDP 스크린캐스트 프레임을 시각과 함께 저장하고 ffmpeg로 mp4를 만든다. 장면 시각은 marks.json에 남는다.
// 실행: 저장소 루트의 .env(SAMPLE_USER_*)와 로컬 스택(http://127.0.0.1:8000)이 있어야 한다. 계정 값은 출력하지 않는다.
//   node record-demo.mjs <출력 폴더>
import { chromium } from '@playwright/test'
import fs from 'node:fs'
import { execFileSync } from 'node:child_process'

const REPO = '/Users/alloy/Desktop/bootcamp/high-quality-ticketing-system'
const BASE = 'http://127.0.0.1:8000'
const OUT = (process.argv[2] || './out') + '/'
fs.mkdirSync(OUT, { recursive: true })
const env = Object.fromEntries(fs.readFileSync(REPO + '/.env', 'utf8').split('\n').filter((l) => l.includes('='))
  .map((l) => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1)]))

// 화면 안에 그리는 커서와 누른 자리의 원. 녹화 프레임에 같이 찍힌다
const CURSOR = `
(() => {
  const add = () => {
    if (document.getElementById('__cur')) return
    const c = document.createElement('div'); c.id = '__cur'
    c.style.cssText = 'position:fixed;left:0;top:0;width:30px;height:30px;z-index:2147483647;pointer-events:none;transform:translate(-200px,-200px)'
    c.innerHTML = '<svg width="30" height="30" viewBox="0 0 24 24"><path d="M4 2l15 9-6.5 1.6L16 20l-2.6 1.3-3.4-7.3L5 18z" fill="#111" stroke="#fff" stroke-width="1.4" stroke-linejoin="round"/></svg>'
    document.documentElement.appendChild(c)
    const r = document.createElement('div'); r.id = '__ring'
    r.style.cssText = 'position:fixed;left:0;top:0;width:52px;height:52px;margin:-26px 0 0 -26px;border-radius:50%;background:rgba(59,64,216,.22);border:3px solid #3B40D8;z-index:2147483646;pointer-events:none;opacity:0'
    document.documentElement.appendChild(r)
    const pos = sessionStorage.getItem('__curpos'); if (pos) c.style.transform = pos
    addEventListener('mousemove', e => { const t = 'translate(' + (e.clientX - 4) + 'px,' + (e.clientY - 2) + 'px)'; c.style.transform = t; sessionStorage.setItem('__curpos', t) }, true)
    addEventListener('mousedown', e => { r.style.transition = 'none'; r.style.left = e.clientX + 'px'; r.style.top = e.clientY + 'px'; r.style.opacity = '1'; r.style.transform = 'scale(.6)'; requestAnimationFrame(() => { r.style.transition = 'transform .4s ease-out, opacity .4s ease-out'; r.style.transform = 'scale(1.4)'; r.style.opacity = '0' }) }, true)
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', add); else add()
})()`

// 녹화 직전에 몇 초 뒤 열리는 회차를 만든다. 오픈 카운트다운이 끝나는 장면을 찍기 위해서다
const openAt = new Date(Date.now() + Number(process.env.OPEN_IN_S || 40) * 1000)
openAt.setUTCMilliseconds(0)
const openIso = openAt.toISOString().replace('.000Z', 'Z')
const seedOut = execFileSync(REPO + '/script/deploy/seed-demo.sh', ['open', openIso, BASE], { cwd: REPO, env: { ...process.env, COMPOSE_PROJECT_NAME: 'iseonjwa' } }).toString()
const scheduleId = seedOut.match(/새 회차 id: (\d+)/)[1]
// 공연 시작은 OPEN_AT 다음 날 같은 시각(한국 시각으로 화면에 나온다)
const start = new Date(openAt.getTime() + 24 * 3600e3 + 9 * 3600e3)
const label = `${start.getUTCFullYear()}.${String(start.getUTCMonth() + 1).padStart(2, '0')}.${String(start.getUTCDate()).padStart(2, '0')}.*${String(start.getUTCHours()).padStart(2, '0')}:${String(start.getUTCMinutes()).padStart(2, '0')}`
console.log('schedule', scheduleId, 'open', openIso, 'label', label)

const browser = await chromium.launch()
const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5, locale: 'ko-KR', colorScheme: 'light', timezoneId: 'Asia/Seoul' })
await ctx.addInitScript(CURSOR)
const page = await ctx.newPage()
// 로그인은 녹화 밖에서 한다
await page.goto(BASE + '/login')
await page.getByLabel('이메일').fill(env.SAMPLE_USER_EMAIL)
await page.getByLabel('비밀번호', { exact: true }).fill(env.SAMPLE_USER_PASSWORD)
await page.getByRole('button', { name: '로그인', exact: true }).click()
await page.waitForURL((u) => !u.pathname.startsWith('/login'))
await page.goto(BASE + '/'); await page.waitForTimeout(1500)

const cdp = await ctx.newCDPSession(page)
const frames = []
const dir = OUT + 'frames/'
fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir)
cdp.on('Page.screencastFrame', async (f) => {
  const file = dir + String(frames.length).padStart(5, '0') + '.jpg'
  fs.writeFileSync(file, Buffer.from(f.data, 'base64'))
  frames.push({ file, t: f.metadata.timestamp })
  await cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }).catch(() => {})
})
const marks = []
let t0 = 0
const mark = (label) => { marks.push({ label, t: Date.now() / 1000 - t0 }); console.log('mark', label, (Date.now() / 1000 - t0).toFixed(2)) }
await page.mouse.move(900, 600)
t0 = Date.now() / 1000
await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 })
await page.mouse.move(900, 600)

const at = async (loc) => {
  await loc.evaluate((el) => el.scrollIntoView({ block: 'center', behavior: 'smooth' }))
  await page.waitForTimeout(800)
  return loc.boundingBox()
}
const moveTo = async (loc, steps = 26) => { const b = await at(loc); await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2, { steps }); await page.waitForTimeout(250) }
const click = async (loc, pause = 600) => { await moveTo(loc); mark('click'); await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(pause) }

mark('home')
await page.waitForTimeout(1500)
const card = page.getByRole('link', { name: /2026 ASTERIA WORLD TOUR/ }).first()
await click(card, 300)
await page.waitForURL(/concerts\/\d+/); await page.waitForTimeout(1200); mark('detail')
await click(page.getByRole('radio', { name: new RegExp(label) }), 900); mark('countdown')
const book = page.getByRole('complementary').getByRole('link', { name: '예매하기' })
await moveTo(page.getByRole('complementary').getByText('예매하기').first())
await book.waitFor({ state: 'visible', timeout: 180000 }); mark('enabled')
await page.waitForTimeout(500)
await click(book, 200); mark('book')
await page.waitForURL(/queue/, { timeout: 15000 }).then(() => mark('queue')).catch(() => {})
await page.waitForURL(/seats/, { timeout: 60000 }); mark('seats')
await page.waitForTimeout(1400)
await click(page.getByRole('radiogroup', { name: '매수' }).getByRole('radio', { name: '1매' }))
await click(page.getByRole('radio', { name: /^A구역/ }), 900); mark('section')
await click(page.getByRole('button', { name: /A구역 1열 15번/ }), 900); mark('picked')
await click(page.getByRole('button', { name: '1매 선택 완료' }), 1600); mark('held')
await click(page.getByRole('dialog', { name: '좌석 선택이 완료되었습니다' }).getByRole('button', { name: '결제하러 가기' }), 300)
await page.waitForURL(/payment/); await page.waitForTimeout(1300); mark('payment')
// 실제 토스페이먼츠 테스트 결제창을 띄웠다가 닫는다(카드 인증은 하지 않는다)
await click(page.getByRole('button', { name: /원 결제하기$/ }), 200); mark('toss-open')
await page.frameLocator('iframe[src*="tosspayments"]').getByText('결제 방법을 선택해주세요').waitFor({ timeout: 30000 }).catch(() => {})
mark('toss-shown')
await page.waitForTimeout(3800)
await page.mouse.move(935, 65, { steps: 24 }); await page.waitForTimeout(300)
mark('click'); await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(1500); mark('toss-closed')
// 다음 승인 한 건에 결제사 응답 지연(4초)을 건다. 결제 서비스는 2초에 결과를 모름으로 두고, 재확인으로 확정한다
execFileSync('docker', ['run', '--rm', '--network', 'iseonjwa_default', 'curlimages/curl:8.10.1', '-s', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', JSON.stringify({ target: 'APPROVE', mode: 'DELAY', delayMs: 4000, count: 1 }), 'http://mock-pg:8090/mock-pg/faults'])
await click(page.getByRole('button', { name: '토스연동 건너뛰고 결제하기' }), 200); mark('mock-pay')
await page.getByRole('heading', { level: 1, name: '예매가 확정되었습니다' }).waitFor({ timeout: 120000 }); mark('confirmed')
await page.waitForTimeout(2200)
const qr = page.getByText('발권 기념 행운 부적').first()
await qr.evaluate((el) => el.scrollIntoView({ block: 'center', behavior: 'smooth' }))
await page.waitForTimeout(1500); mark('qr')
await page.waitForTimeout(1500)
await click(page.getByRole('link', { name: '이 기기에서 열기' }).first(), 300)
await page.waitForURL(/charm/, { timeout: 20000 }); mark('charm')
await page.waitForTimeout(5000)
const stopT = Date.now() / 1000
await cdp.send('Page.stopScreencast')
await page.waitForTimeout(300)
await browser.close()

let list = ''
for (let i = 0; i < frames.length; i++) {
  // 마지막 프레임은 녹화를 멈춘 시각까지 보인다(화면이 멈춰 있으면 새 프레임이 오지 않는다)
  const d = i + 1 < frames.length ? frames[i + 1].t - frames[i].t : Math.max(stopT - frames[i].t, 0.5)
  list += `file '${frames[i].file}'\nduration ${Math.max(d, 0.001).toFixed(4)}\n`
}
list += `file '${frames[frames.length - 1].file}'\n`
fs.writeFileSync(OUT + 'list.txt', list)
execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', OUT + 'list.txt', '-vf', 'fps=30,scale=1920:1080:flags=lanczos,format=yuv420p', '-c:v', 'libx264', '-crf', '14', '-preset', 'slow', OUT + 'booking-raw.mp4'])
fs.writeFileSync(OUT + 'marks.json', JSON.stringify({ firstFrame: frames[0].t - t0, scheduleId, openIso, marks }, null, 1))
console.log('frames', frames.length)
