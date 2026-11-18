// AI 예매 상담 녹화(로컬 실제 상담 서비스, Claude API)
import { chromium } from '@playwright/test'
import fs from 'node:fs'
import { execFileSync } from 'node:child_process'
const REPO = '/Users/alloy/Desktop/bootcamp/high-quality-ticketing-system'
const BASE = 'http://127.0.0.1:8000'
const OUT = process.argv[2] + '/'; const Q = process.argv[3] || 'ASTERIA 공연은 몇 매까지 예매할 수 있어요?'
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
await page.goto(BASE + '/concerts/20'); await page.waitForTimeout(1500)
const cdp = await ctx.newCDPSession(page)
const frames = []; const dir = OUT + 'frames/'
fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir)
cdp.on('Page.screencastFrame', async (f) => { const file = dir + String(frames.length).padStart(5, '0') + '.jpg'; fs.writeFileSync(file, Buffer.from(f.data, 'base64')); frames.push({ file, t: f.metadata.timestamp }); await cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }).catch(() => {}) })
const marks = []; let t0 = Date.now() / 1000
const mark = (l) => { marks.push({ label: l, t: Date.now() / 1000 - t0 }); console.log('mark', l, (Date.now() / 1000 - t0).toFixed(2)) }
await page.mouse.move(700, 400)
t0 = Date.now() / 1000
await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 })
await page.mouse.move(700, 400)
const click = async (loc, pause = 700) => { const b = await loc.boundingBox(); await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2, { steps: 26 }); await page.waitForTimeout(250); mark('click'); await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(pause) }
mark('start'); await page.waitForTimeout(1200)
await click(page.getByRole('button', { name: '예매 문의' }).last(), 1200); mark('opened')
const box = page.getByRole('textbox').last()
await click(box, 300)
await page.keyboard.type(Q, { delay: 70 }); mark('typed')
await page.waitForTimeout(500)
await page.keyboard.press('Enter'); mark('sent')
// 답이 다 나올 때까지: 대화 영역 글자 수가 4초 동안 그대로면 끝난 것으로 본다
const dlg = page.getByRole('dialog').last()
let last = -1, same = 0
for (let i = 0; i < 240; i++) { await page.waitForTimeout(500); const tx = await dlg.innerText().catch(() => ''); const n = tx.length; if (tx.includes('생성하는 중')) { same = 0; last = n; continue } if (n === last) { if (++same >= 6) break } else { same = 0; last = n } }
mark('answered')
await page.waitForTimeout(3000); mark('end')
const stopT = Date.now() / 1000
await cdp.send('Page.stopScreencast'); await page.waitForTimeout(300)
console.log('TEXT', (await dlg.innerText().catch(() => '')).slice(0, 800))
await page.screenshot({ path: OUT + 'answer.png' })
await browser.close()
let list = ''
for (let i = 0; i < frames.length; i++) { const d = i + 1 < frames.length ? frames[i + 1].t - frames[i].t : Math.max(stopT - frames[i].t, 0.5); list += `file '${frames[i].file}'\nduration ${Math.max(d, 0.001).toFixed(4)}\n` }
list += `file '${frames[frames.length - 1].file}'\n`
fs.writeFileSync(OUT + 'list.txt', list)
execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', OUT + 'list.txt', '-vf', 'fps=30,scale=1920:1080:flags=lanczos,format=yuv420p', '-c:v', 'libx264', '-crf', '14', '-preset', 'slow', OUT + 'assist-raw.mp4'])
fs.writeFileSync(OUT + 'marks.json', JSON.stringify({ firstFrame: frames[0].t - t0, marks }, null, 1))
