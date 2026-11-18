// 운영자 화면 녹화: 운영 홈 → 공연 관리 → 추첨 상세 → 시연 장애 패널(장애 걸기 → 모두 해제)
import { chromium } from '@playwright/test'
import fs from 'node:fs'
import { execFileSync } from 'node:child_process'
const REPO = '/Users/alloy/Desktop/bootcamp/high-quality-ticketing-system'
const BASE = 'http://127.0.0.1:8000'
const OUT = process.argv[2] + '/'
fs.mkdirSync(OUT, { recursive: true })
const env = Object.fromEntries(fs.readFileSync(REPO + '/.env', 'utf8').split('\n').filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1)]))
const CURSOR = fs.readFileSync(new URL('./cursor.js', import.meta.url), 'utf8')
const browser = await chromium.launch()
const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5, locale: 'ko-KR', colorScheme: 'light', timezoneId: 'Asia/Seoul' })
await ctx.addInitScript(CURSOR)
const page = await ctx.newPage()
await page.goto(BASE + '/login')
await page.getByLabel('이메일').fill(env.ADMIN_EMAIL)
await page.getByLabel('비밀번호', { exact: true }).fill(env.ADMIN_PASSWORD)
await page.getByRole('button', { name: '로그인', exact: true }).click()
await page.waitForURL((u) => !u.pathname.startsWith('/login'))
await page.goto(BASE + '/admin'); await page.getByText('빅빵').first().waitFor({ timeout: 30000 }); await page.waitForTimeout(800)
const cdp = await ctx.newCDPSession(page)
const frames = []; const dir = OUT + 'frames/'
fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir)
cdp.on('Page.screencastFrame', async (f) => { const file = dir + String(frames.length).padStart(5, '0') + '.jpg'; fs.writeFileSync(file, Buffer.from(f.data, 'base64')); frames.push({ file, t: f.metadata.timestamp }); await cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }).catch(() => {}) })
const marks = []; let t0 = Date.now() / 1000
const mark = (l) => { marks.push({ label: l, t: Date.now() / 1000 - t0 }); console.log('mark', l, (Date.now() / 1000 - t0).toFixed(2)) }
await page.mouse.move(700, 300)
t0 = Date.now() / 1000
await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 })
await page.mouse.move(700, 300)
const at = async (loc) => { await loc.evaluate((el) => el.scrollIntoView({ block: 'center', behavior: 'smooth' })); await page.waitForTimeout(800); return loc.boundingBox() }
const click = async (loc, pause = 700) => { const b = await at(loc); await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2, { steps: 26 }); await page.waitForTimeout(250); mark('click'); await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(pause) }
mark('home'); await page.waitForTimeout(1500)
await click(page.getByRole('link', { name: /빅빵/ }).first(), 300)
await page.waitForURL(/admin\/concerts\/\d+/); await page.getByText('회차').first().waitFor(); await page.waitForTimeout(1200); mark('concert')
const sched = page.getByText('회차 #50').first()
await at(sched); await page.waitForTimeout(1500); mark('schedules')
const lot = page.getByRole('link', { name: /추첨/ }).first()
if (await lot.count()) { await click(lot, 300); } else { await page.goto(BASE + '/admin/lotteries/4') }
await page.waitForURL(/admin\/lotteries\/\d+/, { timeout: 15000 }).catch(async () => { await page.goto(BASE + '/admin/lotteries/4') })
await page.getByText('추첨석').first().waitFor(); await page.waitForTimeout(2200); mark('lottery')
await page.goto(BASE + '/admin/demo/faults'); await page.getByText('PG 응답 지연').first().waitFor(); await page.waitForTimeout(1200); mark('faults')
await click(page.getByRole('button', { name: '다음 결제 1건에 걸기' }).nth(1), 1800); mark('applied')
const clear = page.getByRole('button', { name: '모두 해제' })
await click(clear, 1800); mark('cleared')
await page.waitForTimeout(800)
const stopT = Date.now() / 1000
await cdp.send('Page.stopScreencast'); await page.waitForTimeout(300)
await page.screenshot({ path: OUT + 'last.png' })
await browser.close()
let list = ''
for (let i = 0; i < frames.length; i++) { const d = i + 1 < frames.length ? frames[i + 1].t - frames[i].t : Math.max(stopT - frames[i].t, 0.5); list += `file '${frames[i].file}'\nduration ${Math.max(d, 0.001).toFixed(4)}\n` }
list += `file '${frames[frames.length - 1].file}'\n`
fs.writeFileSync(OUT + 'list.txt', list)
execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', OUT + 'list.txt', '-vf', 'fps=30,scale=1920:1080:flags=lanczos,format=yuv420p', '-c:v', 'libx264', '-crf', '14', '-preset', 'slow', OUT + 'admin-raw.mp4'])
fs.writeFileSync(OUT + 'marks.json', JSON.stringify({ firstFrame: frames[0].t - t0, marks }, null, 1))
