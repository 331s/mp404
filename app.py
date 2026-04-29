from flask import Flask, render_template, request, send_file, jsonify
import os, tempfile, glob, base64, subprocess, sys, json

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

EXTRACTOR = "youtube:player_client=tv,mweb;formats=missing_pot"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/version")
def version():
    r = subprocess.run([YTDLP_PATH, "--version"], capture_output=True, text=True)
    return jsonify({"yt_dlp": r.stdout.strip(), "ffmpeg": FFMPEG_PATH, "cookie": COOKIE_FILE is not None})

@app.route("/info", methods=["POST"])
def info():
    url = request.form.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL gerekli"}), 400
    cmd = [YTDLP_PATH, "--no-playlist", "--extractor-args", EXTRACTOR, "-J", "--no-warnings"]
    if COOKIE_FILE:
        cmd += ["--cookies", COOKIE_FILE]
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return jsonify({"error": result.stderr[:300]}), 400
    try:
        data = json.loads(result.stdout)
        fps_values = {int(f["fps"]) for f in data.get("formats", []) if f.get("fps") and f.get("vcodec") not in (None, "none")}
        return jsonify({"title": data.get("title", ""), "has_60fps": any(f >= 60 for f in fps_values)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/download", methods=["POST"])
def download():
    url     = request.form.get("url", "").strip()
    quality = request.form.get("quality", "1080")
    fps     = request.form.get("fps", "30")
    if not url: return "Lutfen bir YouTube linki girin.", 400
    if quality not in ALLOWED_QUALITIES: quality = "1080"
    if fps not in {"30", "60"}: fps = "30"

    temp_dir = tempfile.mkdtemp()
    out_tmpl = os.path.join(temp_dir, "%(title)s.%(ext)s")

    cmd = [
        YTDLP_PATH, "--no-playlist",
        "--extractor-args", EXTRACTOR,
        "-f", f"bestvideo[height<={quality}][fps<={fps}]+bestaudio/bestvideo[height<={quality}]+bestaudio/best",
        "--merge-output-format", "mp4",
        "--ffmpeg-location", FFMPEG_PATH,
        "-o", out_tmpl,
        "--no-warnings", "--ignore-errors",
    ]
    if COOKIE_FILE:
        cmd += ["--cookies", COOKIE_FILE]
    cmd.append(url)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    video_files = (
        glob.glob(os.path.join(temp_dir, "*.mp4")) +
        glob.glob(os.path.join(temp_dir, "*.mkv")) +
        glob.glob(os.path.join(temp_dir, "*.webm"))
    )
    if not video_files:
        return f"Hata: {result.stderr or result.stdout}", 400

    file_path = video_files[0]
    ext  = os.path.splitext(file_path)[1]
    name = os.path.splitext(os.path.basename(file_path))[0]
    safe = "".join(c for c in name if c.isalnum() or c in " _-()[]").strip() or "video"
    return send_file(file_path, as_attachment=True, download_name=f"{safe}{ext}", mimetype="video/mp4")

if __name__ == "__main__":
    app.run(debug=True)
