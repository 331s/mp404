<div align="center">

<br>

# <span>MP4</span>04

**YouTube videolarını istediğin çözünürlük ve kare hızında indir.**

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-black?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-FF0000?style=flat-square&logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-required-007808?style=flat-square&logo=ffmpeg&logoColor=white)](https://ffmpeg.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

<br>

</div>

---

## ✨ Özellikler

- 🎬 **6 çözünürlük seçeneği** — 360p / 480p / 720p HD / 1080p FHD / 1440p 2K / 2160p 4K
- ⚡ **Akıllı FPS algılama** — Video 60fps destekliyorsa seçenek otomatik görünür, desteklemiyorsa görünmez
- 🎞️ **Gerçek format seçimi** — `bestvideo+bestaudio` pipeline, FFmpeg ile MP4'e birleştirilir
- 📋 **Akıllı yapıştır** — Panoda YouTube linki varsa otomatik algılar
- 🔒 **Gizlilik odaklı** — Dosyalar sunucuda saklanmaz, işlem sonrası silinir
- 🎨 **Sinematik dark UI** — Animasyonlu film şeridi, elektrik mavisi estetik

---

## 🚀 Kurulum

### Gereksinimler

- Python 3.8+
- FFmpeg (sistem genelinde kurulu olmalı)

### 1. Repoyu klonla

```bash
git clone https://github.com/331s/mp404.git
cd mp404
```

### 2. Sanal ortam oluştur

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Bağımlılıkları yükle

```bash
pip install flask yt-dlp
```

### 4. FFmpeg kurulumu

```bash
# Windows (winget)
winget install ffmpeg

# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg
```

### 5. Çalıştır

```bash
python app.py
```

Tarayıcıda aç: `http://127.0.0.1:5000`

---

## 📁 Proje Yapısı

```
mp404/
├── app.py                  # Flask backend
├── templates/
│   └── index.html          # Ana sayfa
└── static/
    ├── css/
    │   └── style.css       # Stiller
    └── js/
        └── main.js         # Frontend mantığı
```

---

## 🎛️ Kalite Seçenekleri

| Çözünürlük | Etiket | Tahmini Boyut (dk başına) |
|------------|--------|--------------------------|
| 360p | SD | ~10 MB |
| 480p | SD | ~18 MB |
| 720p | HD | ~35 MB |
| 1080p | FHD | ~70 MB |
| 1440p | 2K | ~130 MB |
| 2160p | 4K | ~250 MB |

> Boyutlar video codec, içerik türü ve sahne karmaşıklığına göre değişir.

---

## ⚙️ Nasıl Çalışır?

```
YouTube URL
    │
    ▼
/info endpoint → yt-dlp format listesini çeker (indirmeden)
    │
    ├─ 60fps stream var mı? → Evet: FPS butonu göster
    │                       → Hayır: Sadece 30fps göster
    ▼
Kullanıcı çözünürlük + fps seçer
    │
    ▼
yt-dlp → bestvideo[height<=X][fps<=Y] + bestaudio indirir
    │
    ▼
FFmpeg → Ses ve videoyu MP4 konteynerinde birleştirir
    │
    ▼
Flask → Dosyayı tarayıcıya gönderir (send_file)
    │
    ▼
Tarayıcı → Otomatik indirir, sunucudan silinir
```

---

## 🔌 API Endpoint'leri

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `GET`  | `/` | Ana sayfa |
| `POST` | `/info` | Video format bilgisini döner (60fps kontrolü) |
| `POST` | `/download` | Videoyu indir ve gönder |

### `/info` — İstek / Yanıt

```json
// POST /info
// body: url=https://youtube.com/watch?v=...

// Yanıt
{
  "title": "Video Başlığı",
  "has_60fps": true
}
```

---

## 🛠️ Teknolojiler

| Katman | Teknoloji |
|--------|-----------|
| Backend | Python, Flask |
| İndirici | yt-dlp |
| Dönüştürücü | FFmpeg |
| Frontend | Vanilla HTML / CSS / JS |
| Fontlar | Audiowide, JetBrains Mono, Manrope |

---

## 331 Studios ile İlgili Projeler

| Proje | Açıklama |
|-------|----------|
| [MP331](https://github.com/331s/mp331) | YouTube → MP3 dönüştürücü (128–320 kbps) |
| [MP404](https://github.com/331s/mp404) | YouTube → MP4 indirici (360p–4K, 60fps) |

---

## ⚠️ Yasal Uyarı

Bu proje yalnızca **kişisel ve eğitim amaçlı** geliştirilmiştir. Telif hakkıyla korunan içeriklerin izinsiz indirilmesi YouTube'un [Kullanım Koşulları](https://www.youtube.com/static?template=terms)'nı ihlal edebilir. Sorumluluk kullanıcıya aittir.

---

<div align="center">

Geliştirici: **331 Studios** &nbsp;•&nbsp; Barış

</div>
