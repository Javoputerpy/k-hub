window.addEventListener('DOMContentLoaded', () => {
    // 1. Auth Sync
    fetch('/api/me').then(r => r.json()).then(data => {
        if (!data.logged_in) {
            document.getElementById('auth-modal').style.display = 'flex';
        } else {
            const btn = document.getElementById('login-trigger');
            if(btn) btn.style.display = 'none';
            const userBtn = document.getElementById('user-profile-btn');
            if(userBtn) {
                userBtn.style.display = 'flex';
                document.getElementById('username-display').innerText = data.user.name.split(' ')[0];
            }
            window.K_USER = data;
        }
    }).catch(e => console.error(e));

    // 2. Global Interactions
    const skipBtn = document.getElementById('auth-skip-btn');
    if (skipBtn) skipBtn.addEventListener('click', () => { document.getElementById('auth-modal').style.display = 'none'; });

    window.verifyOTP = async function() {
        const otp = document.getElementById('otp-input').value;
        if(!otp || otp.length < 6) return alert("Enter 6-digit code");
        
        const res = await fetch('/api/auth/otp', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({otp})
        }).then(r => r.json());

        if(res.ok) window.location.reload();
        else alert(res.error);
    }

    const langBtn = document.getElementById('lang-btn');
    if (langBtn) {
        langBtn.addEventListener('change', async (e) => {
            const current = e.target.value;
            await fetch('/api/set_lang', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({lang: current})});
            window.location.reload();
        });
    }

    const loginTrigger = document.getElementById('login-trigger');
    if(loginTrigger) loginTrigger.addEventListener('click', () => { document.getElementById('auth-modal').style.display = 'flex'; });

    // 3. Router Orchestration
    const path = window.location.pathname;
    if (path.includes('roadmap')) fetchTimeline('/api/roadmap', 'roadmap-content', s => `
        <div class="data-row">
            <span style="font-weight:600; color:${s.done ? 'var(--cyan)' : 'var(--text-main)'}">${s.title}</span>
            <span>${s.done ? '✅ DONE' : '⏳ PENDING'}</span>
        </div>`);
    else if (path.includes('labs')) fetchTimeline('/api/labs', 'labs-content', l => `
        <div class="card"><h3>${l.name}</h3><p>${l.desc}</p></div>`);
    else if (path.includes('scholarships')) fetchTimeline('/api/scholarships', 'scholarships-content', s => `
        <div class="card" style="border-left:4px solid var(--gold);">
            <div style="font-size:0.7rem; color:var(--text-muted); margin-bottom:8px;">${s.badge}</div>
            <h3 style="margin-bottom:8px; color:var(--text-main);">${s.name}</h3>
            <p>${s.detail}</p>
        </div>`);
});

async function fetchTimeline(api, elId, formatter) {
    try {
        const res = await fetch(api);
        const data = await res.json();
        const box = document.getElementById(elId);
        if(box) box.innerHTML = data.map(formatter).join('');
    } catch(e) { console.error('Fetch error:', api, e); }
}

function initPredictor() {
    const btn = document.getElementById('predict-btn');
    if(!btn) return;
    btn.addEventListener('click', async () => {
        btn.innerText = 'Calculating...';
        try {
            const res = await fetch('/api/predict', { method: 'POST', headers:{'Content-Type':'application/json'} });
            const data = await res.json();
            document.getElementById('predict-result').innerHTML = `
                <div class="card" style="text-align:center; padding: 40px;">
                    <div style="font-size: 4rem; font-family: var(--font-heading); color: var(--${data.color}); text-shadow: 0 0 20px var(--${data.color});">
                        ${data.score}%
                    </div>
                    <div style="margin-top: 24px; text-align:left;" class="grid-2">
                        <div><h4 style="color:var(--cyan); margin-bottom:12px;">✅ Strengths</h4><ul style="padding-left:20px; color:var(--text-muted);"><li>${data.strengths.join('</li><li>')}</li></ul></div>
                        <div><h4 style="color:var(--red); margin-bottom:12px;">⚠️ Weaknesses</h4><ul style="padding-left:20px; color:var(--text-muted);"><li>${data.weaknesses.join('</li><li>')}</li></ul></div>
                    </div>
                </div>`;
        } catch(e) { console.error(e); }
        btn.innerText = 'ANALYZE MY PROFILE';
    });
}

function initSOP() {
    const btn = document.getElementById('sop-btn');
    if(!btn) return;
    btn.addEventListener('click', async () => {
        btn.innerText = 'Generating with AI...';
        try {
            const res = await fetch('/api/sop', { method: 'POST', headers:{'Content-Type':'application/json'} });
            const data = await res.json();
            document.getElementById('sop-result').innerHTML = `<div class="card" style="margin-top:24px;"><p>${data.sop.replace(/\n/g, '<br>')}</p></div>`;
        } catch(e) { console.error(e); }
        btn.innerText = 'GENERATE DRAFT';
    });
}

function showNotification(msg) {
    const div = document.createElement('div');
    div.style.cssText = 'position:fixed; bottom:30px; right:30px; background:var(--cyan); color:white; padding:12px 24px; border-radius:12px; z-index:10000; font-weight:700; box-shadow:0 10px 30px rgba(0,0,0,0.2); animation: slideIn 0.3s ease-out;';
    div.innerText = msg;
    document.body.appendChild(div);
    setTimeout(() => {
        div.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => div.remove(), 300);
    }, 3000);
}

// Add animations
const style = document.createElement('style');
style.innerHTML = `
@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
@keyframes slideOut { from { transform: translateX(0); opacity: 1; } to { transform: translateX(100%); opacity: 0; } }
`;
document.head.appendChild(style);
