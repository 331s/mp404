/* ===========================
   MP404 — main.js
   =========================== */

const form        = document.getElementById('downloadForm');
const urlInput    = document.getElementById('urlInput');
const downloadBtn = document.getElementById('downloadBtn');
const pasteBtn    = document.getElementById('pasteBtn');
const statusMsg   = document.getElementById('statusMsg');
const headerBadge = document.getElementById('headerBadge');
const featQuality = document.getElementById('featQuality');

const qualityLabels = {
    '360':  '360p SD',
    '480':  '480p SD',
    '720':  '720p HD',
    '1080': '1080p FHD',
    '1440': '1440p 2K',
    '2160': '2160p 4K',
};

/* ---------- Selectors ---------- */
function getSelectedQuality() {
    const checked = form.querySelector('input[name="quality"]:checked');
    return checked ? checked.value : '1080';
}

function getSelectedFps() {
    const checked = form.querySelector('input[name="fps"]:checked');
    return checked ? checked.value : '30';
}

function syncUI() {
    const q   = getSelectedQuality();
    const fps = getSelectedFps();
    const label = qualityLabels[q] || `${q}p`;
    if (headerBadge) headerBadge.textContent = `${q}p ${fps}fps • MP4`;
    if (featQuality) featQuality.textContent  = `${label} ${fps}fps`;
}

form.querySelectorAll('input[name="quality"], input[name="fps"]').forEach(r => {
    r.addEventListener('change', syncUI);
});

syncUI();

/* ---------- Paste button ---------- */
pasteBtn.addEventListener('click', async () => {
    try {
        const text = await navigator.clipboard.readText();
        if (text.trim()) {
            urlInput.value = text.trim();
            urlInput.focus();
            pasteBtn.style.color = 'var(--accent)';
            setTimeout(() => (pasteBtn.style.color = ''), 600);
        }
    } catch { urlInput.focus(); }
});

/* ---------- Auto-paste ---------- */
urlInput.addEventListener('focus', async () => {
    if (urlInput.value) return;
    try {
        const text = await navigator.clipboard.readText();
        if (isYouTubeURL(text.trim())) {
            urlInput.value = text.trim();
            fetchVideoInfo(text.trim());
        }
    } catch { /* izin yok */ }
});

/* ---------- URL değişince fps kontrolü ---------- */
let infoDebounce = null;
urlInput.addEventListener('input', () => {
    if (!statusMsg.hidden) hideStatus();
    clearTimeout(infoDebounce);
    const val = urlInput.value.trim();
    if (isYouTubeURL(val)) {
        infoDebounce = setTimeout(() => fetchVideoInfo(val), 600);
    } else {
        reset60fps();
    }
});

async function fetchVideoInfo(url) {
    const fps60Opt    = document.getElementById('fps60Opt');
    const fpsChecking = document.getElementById('fpsChecking');

    fps60Opt.style.display    = 'none';
    fpsChecking.style.display = 'flex';

    // 30fps'e geri dön
    const radio30 = form.querySelector('input[name="fps"][value="30"]');
    if (radio30) { radio30.checked = true; syncUI(); }

    try {
        const fd = new FormData();
        fd.append('url', url);
        const res  = await fetch('/info', { method: 'POST', body: fd });
        const data = await res.json();

        if (data.has_60fps) {
            fps60Opt.style.display = 'inline-block';
        }
    } catch { /* sessizce geç */ }
    finally {
        fpsChecking.style.display = 'none';
    }
}

function reset60fps() {
    const fps60Opt    = document.getElementById('fps60Opt');
    const fpsChecking = document.getElementById('fpsChecking');
    fps60Opt.style.display    = 'none';
    fpsChecking.style.display = 'none';
    const radio30 = form.querySelector('input[name="fps"][value="30"]');
    if (radio30) { radio30.checked = true; syncUI(); }
}

function isYouTubeURL(str) {
    return /^https?:\/\/(www\.)?(youtube\.com\/(watch|shorts)|youtu\.be\/)/.test(str);
}

/* ---------- Form submit ---------- */
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const url = urlInput.value.trim();
    if (!url) return showStatus('Lütfen bir YouTube linki girin.', 'error');
    if (!isYouTubeURL(url)) return showStatus('Geçerli bir YouTube linki giriniz.', 'error');

    setLoading(true);
    hideStatus();

    try {
        const formData = new FormData(form);
        const response = await fetch('/download', { method: 'POST', body: formData });

        if (!response.ok) {
            const text = await response.text();
            throw new Error(text || `Hata: ${response.status}`);
        }

        const blob = await response.blob();
        const contentDisposition = response.headers.get('Content-Disposition') || '';
        const filenameMatch = contentDisposition.match(/filename\*?=['"]?([^'";]+)['"]?/);
        const filename = filenameMatch ? decodeURIComponent(filenameMatch[1]) : 'video.mp4';

        const objectURL = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = objectURL;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(objectURL);

        const q   = getSelectedQuality();
        const fps = getSelectedFps();
        showStatus(`✓ İndirme tamamlandı! ${qualityLabels[q] || q + 'p'} ${fps}fps MP4 kaydedildi.`, 'success');
        urlInput.value = '';

    } catch (err) {
        showStatus('⚠ ' + (err.message || 'Bir hata oluştu, tekrar deneyin.'), 'error');
    } finally {
        setLoading(false);
    }
});

function setLoading(state) {
    downloadBtn.disabled = state;
    downloadBtn.classList.toggle('loading', state);
}
function showStatus(message, type = 'error') {
    statusMsg.textContent = message;
    statusMsg.className = `status-msg ${type}`;
    statusMsg.hidden = false;
}
function hideStatus() { statusMsg.hidden = true; }
urlInput.addEventListener('input', () => { if (!statusMsg.hidden) hideStatus(); });
