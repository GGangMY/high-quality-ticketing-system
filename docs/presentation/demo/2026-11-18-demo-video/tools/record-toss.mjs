// 토스페이먼츠 테스트 결제창 장면만 녹화한다(좌석 확보까지는 녹화 밖). 카드 인증은 하지 않고 닫는다.
import { chromium } from '@playwright/test'
import fs from 'node:fs'
import { execFileSync } from 'node:child_process'
const REPO = '/Users/alloy/Desktop/bootcamp/high-quality-ticketing-system'
const BASE = 'http://127.0.0.1:8000'
const OUT = process.argv[2] + '/'; const SCHEDULE = process.argv[3] || '2026\\.11\\.19.*15:21'
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
await page.goto(BASE + '/concerts/20'); await page.waitForTimeout(800)
await page.getByRole('radio', { name: new RegExp(SCHEDULE) }).click()
await page.getByRole('complementary').getByRole('link', { name: '예매하기' }).click()
await page.waitForURL(/seats/, { timeout: 60000 }); await page.waitForTimeout(1200)
await page.getByRole('radiogroup', { name: '매수' }).getByRole('radio', { name: '1매' }).click()
await page.getByRole('radio', { name: /^A구역/ }).click(); await page.waitForTimeout(600)
await page.getByRole('button', { name: /A구역 1열 4번/ }).click()
await page.getByRole('button', { name: '1매 선택 완료' }).click()
await page.getByRole('dialog').getByRole('button', { name: '결제하러 가기' }).click()
await page.waitForURL(/payment/); await page.waitForTimeout(1500)
await page.mouse.move(700, 400)
const cdp = await ctx.newCDPSession(page)
const frames = []; const dir = OUT + 'frames/'
fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir)
cdp.on('Page.screencastFrame', async (f) => { const file = dir + String(frames.length).padStart(5, '0') + '.jpg'; fs.writeFileSync(file, Buffer.from(f.data, 'base64')); frames.push({ file, t: f.metadata.timestamp }); await cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }).catch(() => {}) })
const marks = []; let t0 = Date.now() / 1000
const mark = (l) => { marks.push({ label: l, t: Date.now() / 1000 - t0 }); console.log('mark', l, (Date.now() / 1000 - t0).toFixed(2)) }
t0 = Date.now() / 1000
await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 })
await page.mouse.move(700, 400)
const click = async (loc, pause = 300) => { const b = await loc.boundingBox(); await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2, { steps: 26 }); await page.waitForTimeout(250); mark('click'); await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(pause) }
mark('start'); await page.waitForTimeout(700)
await click(page.getByRole('button', { name: /원 결제하기$/ }), 200); mark('toss-open')
await page.frameLocator('iframe[src*="tosspayments"]').getByText('결제 방법을 선택해주세요').waitFor({ timeout: 30000 }).catch(() => {})
mark('toss-shown'); await page.waitForTimeout(3800)
await page.mouse.move(935, 65, { steps: 24 }); await page.waitForTimeout(300)
mark('click'); await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(2200); mark('end')
const stopT = Date.now() / 1000
await cdp.send('Page.stopScreencast'); await page.waitForTimeout(300)
await browser.close()
let list = ''
for (let i = 0; i < frames.length; i++) { const d = i + 1 < frames.length ? frames[i + 1].t - frames[i].t : Math.max(stopT - frames[i].t, 0.5); list += `file '${frames[i].file}'\nduration ${Math.max(d, 0.001).toFixed(4)}\n` }
list += `file '${frames[frames.length - 1].file}'\n`
fs.writeFileSync(OUT + 'list.txt', list)
execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', OUT + 'list.txt', '-vf', 'fps=30,scale=1920:1080:flags=lanczos,format=yuv420p', '-c:v', 'libx264', '-crf', '14', '-preset', 'slow', OUT + 'toss-raw.mp4'])
fs.writeFileSync(OUT + 'marks.json', JSON.stringify({ firstFrame: frames[0].t - t0, marks }, null, 1))
