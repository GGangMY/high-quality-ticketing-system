// 추첨 응모 → 당첨·자동결제 녹화(로컬 실제 백엔드). 카드 등록은 시연용 Mock 빌링이다.
import { chromium } from '@playwright/test'
import fs from 'node:fs'
import { execFileSync } from 'node:child_process'
const REPO = '/Users/alloy/Desktop/bootcamp/high-quality-ticketing-system'
const BASE = 'http://127.0.0.1:8000'
const LOTTERY = process.argv[2]; const OUT = process.argv[3] + '/'
fs.mkdirSync(OUT, { recursive: true })
const env = Object.fromEntries(fs.readFileSync(REPO + '/.env', 'utf8').split('\n').filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1)]))
const CURSOR = fs.readFileSync(new URL('./cursor.js', import.meta.url), 'utf8')
const browser = await chromium.launch()
const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5, locale: 'ko-KR', colorScheme: 'light', timezoneId: 'Asia/Seoul' })
await ctx.addInitScript(CURSOR)
const page = await ctx.newPage()
await page.goto(BASE + '/login')
await page.getByLabel('이메일').fill(env.SAMPLE_USER_EMAIL)
await page.getByLabel('비밀번호', { exact: true }).fill(env.SAMPLE_USER_PASSWORD)
await page.getByRole('button', { name: '로그인', exact: true }).click()
await page.waitForURL((u) => !u.pathname.startsWith('/login'))
await page.goto(BASE + '/lotteries/' + LOTTERY); await page.waitForTimeout(1500)
const cdp = await ctx.newCDPSession(page)
const frames = []; const dir = OUT + 'frames/'
fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir)
cdp.on('Page.screencastFrame', async (f) => { const file = dir + String(frames.length).padStart(5, '0') + '.jpg'; fs.writeFileSync(file, Buffer.from(f.data, 'base64')); frames.push({ file, t: f.metadata.timestamp }); await cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }).catch(() => {}) })
const marks = []; let t0 = Date.now() / 1000
const mark = (l) => { marks.push({ label: l, t: Date.now() / 1000 - t0 }); console.log('mark', l, (Date.now() / 1000 - t0).toFixed(2)) }
await page.mouse.move(900, 500)
t0 = Date.now() / 1000
await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 })
await page.mouse.move(900, 500)
const at = async (loc) => { await loc.evaluate((el) => el.scrollIntoView({ block: 'center', behavior: 'smooth' })); await page.waitForTimeout(800); return loc.boundingBox() }
const moveTo = async (loc) => { const b = await at(loc); await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2, { steps: 26 }); await page.waitForTimeout(250) }
const click = async (loc, pause = 700) => { await moveTo(loc); mark('click'); await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(pause) }
mark('start'); await page.waitForTimeout(1500)
const reg = page.getByRole('button', { name: '카드 등록', exact: true })
if (await reg.count()) { await click(reg, 2000); mark('card') }
const apply = page.getByRole('button', { name: '1매 응모하기' })
await apply.waitFor({ state: 'visible' })
await page.waitForFunction(() => { const b = [...document.querySelectorAll('button')].find((x) => x.textContent.includes('1매 응모하기')); return b && !b.disabled }, null, { timeout: 180000, polling: 500 })
mark('open')
await click(apply, 2500); mark('applied')
// 추첨과 자동결제가 끝날 때까지 기다린다(이 구간은 편집에서 잘라 낸다)
const deadline = Date.now() + 10 * 60e3
while (Date.now() < deadline) {
  if (await page.getByText('당첨 및 결제가 완료되었습니다').count()) break
  await page.waitForTimeout(15000)
  if (await page.getByText('당첨 및 결제가 완료되었습니다').count()) break
  await page.reload(); await page.waitForTimeout(2000)
}
mark('won')
await page.waitForTimeout(1500)
const r = page.getByText('당첨 및 결제가 완료되었습니다').first()
await r.evaluate((el) => el.scrollIntoView({ block: 'center', behavior: 'smooth' })).catch(() => {})
await page.waitForTimeout(3500); mark('end')
const stopT = Date.now() / 1000
await cdp.send('Page.stopScreencast'); await page.waitForTimeout(300)
await page.screenshot({ path: OUT + 'won.png' })
await browser.close()
let list = ''
for (let i = 0; i < frames.length; i++) { const d = i + 1 < frames.length ? frames[i + 1].t - frames[i].t : Math.max(stopT - frames[i].t, 0.5); list += `file '${frames[i].file}'\nduration ${Math.max(d, 0.001).toFixed(4)}\n` }
list += `file '${frames[frames.length - 1].file}'\n`
fs.writeFileSync(OUT + 'list.txt', list)
execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', OUT + 'list.txt', '-vf', 'fps=30,scale=1920:1080:flags=lanczos,format=yuv420p', '-c:v', 'libx264', '-crf', '14', '-preset', 'slow', OUT + 'lottery-raw.mp4'])
fs.writeFileSync(OUT + 'marks.json', JSON.stringify({ firstFrame: frames[0].t - t0, marks }, null, 1))
console.log('frames', frames.length)
