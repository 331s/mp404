from flask import Flask, render_template, request, Response, jsonify, send_file
import os, tempfile, base64, subprocess, sys, shutil, json, glob

def get_ffmpeg_path():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"

FFMPEG_PATH = get_ffmpeg_path()
YTDLP_PATH  = os.path.join(os.path.dirname(sys.executable), "yt-dlp")
if not os.path.exists(YTDLP_PATH):
    YTDLP_PATH = "yt-dlp"
NODE_PATH = shutil.which("node") or shutil.which("nodejs") or ""

COOKIE_FILE = None
_b64 = os.environ.get("YT_COOKIES_B64", "")
if _b64:
    try:
        _path = os.path.join(tempfile.gettempdir(), "yt_cookies.txt")
        with open(_path, "wb") as f:
            f.write(base64.b64decode(_b64))
        COOKIE_FILE = _path
    except Exception as e:
        print(f"Cookie hatasi: {e}")

ALLOWED_QUALITIES = {"360", "480", "720", "1080", "1440", "2160"}
app = Flask(__name__)

def base_args():
    args = ["--js-runtimes", f"node:{NODE_PATH}" if NODE_PATH else "node",
            "--no-warnings", "--no-playlist"]
    if COOKIE_FILE:
        args += ["--cookies", COOKIE_FILE]
    return args

def safe_filename(title):
    return "".join(c for c in title if c.isalnum() or c in " _-()[]").strip() or "video"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/version")
def version():
    r = subprocess.run([YTDLP_PATH, "--version"], capture_output=True, text=True)
    return jsonify({"yt_dlp": r.stdout.strip(), "node": NODE_PATH, "cookie": COOKIE_FILE is not None})

@app.route("/info", methods=["POST"])
def info():
    """Video bilgisi + 60fps tespiti — tek istekte"""
    url = request.form.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL gerekli"}), 400
    cmd = [YTDLP_PATH] + base_args() + ["-J", url]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return jsonify({"error": r.stderr[:300]}), 400
    try:
        data = json.loads(r.stdout)
        fps_values = {
            int(f["fps"])
            for f in data.get("formats", [])
            if f.get("fps") and f.get("vcodec") not in (None, "none")
        }
        return jsonify({
            "title": data.get("title", ""),
            "has_60fps": any(f >= 60 for f in fps_values),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/download", methods=["POST"])
def download():
    url     = request.form.get("url", "").strip()
    quality = request.form.get("quality", "1080")
    fps     = request.form.get("fps", "30")
    if not url: return "URL gerekli", 400
    if quality not in ALLOWED_QUALITIES: quality = "1080"
    if fps not in {"30", "60"}: fps = "30"

    fmt = (
        f"bestvideo[height<={quality}][fps<={fps}][ext=mp4]+bestaudio[ext=m4a]"
        f"/bestvideo[height<={quality}][fps<={fps}]+bestaudio"
        f"/bestvideo[height<={quality}]+bestaudio/best"
    )

    temp_dir = tempfile.mkdtemp()
    out_tmpl = os.path.join(temp_dir, "%(title)s.%(ext)s")

    cmd = [
        YTDLP_PATH, "-f", fmt,
        "--no-playlist",
        "--js-runtimes", f"node:{NODE_PATH}" if NODE_PATH else "node",
        "--no-warnings", "--concurrent-fragments", "4",
        "--merge-output-format", "mp4",
        "--ffmpeg-location", FFMPEG_PATH,
        "--add-metadata",          # başlık, sanatçı, yıl MP4'e gömülür
        "-o", out_tmpl,
    ]
    if COOKIE_FILE:
        cmd += ["--cookies", COOKIE_FILE]
    cmd.append(url)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    files = glob.glob(os.path.join(temp_dir, "*.mp4")) + \
            glob.glob(os.path.join(temp_dir, "*.mkv")) + \
            glob.glob(os.path.join(temp_dir, "*.webm"))
    if not files:
        return f"Hata: {result.stderr or result.stdout}", 400

    file_path = files[0]
    ext  = os.path.splitext(file_path)[1]
    name = os.path.splitext(os.path.basename(file_path))[0]
    safe = safe_filename(name)

    def stream_file():
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                yield chunk
        shutil.rmtree(temp_dir, ignore_errors=True)

    return Response(
        stream_file(),
        mimetype="video/mp4",
        headers={
            "Content-Disposition": f'attachment; filename="{safe}{ext}"',
            "Content-Length": str(os.path.getsize(file_path)),
        }
    )

if __name__ == "__main__":
    app.run(debug=True)
