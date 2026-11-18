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
})()