from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import tempfile
import glob
import base64

def get_ffmpeg_path():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return 'ffmpeg'

FFMPEG_PATH = get_ffmpeg_path()

COOKIE_FILE = None
_cookie_b64 = os.environ.get('YT_COOKIES_B64', '')
if _cookie_b64:
    try:
        _cookie_path = os.path.join(tempfile.gettempdir(), 'yt_cookies.txt')
        with open(_cookie_path, 'wb') as _f:
            _f.write(base64.b64decode(_cookie_b64))
        COOKIE_FILE = _cookie_path
    except Exception:
        pass

app = Flask(__name__)

ALLOWED_QUALITIES = {'360', '480', '720', '1080', '1440', '2160'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/info', methods=['POST'])
def info():
    url = request.form.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL gerekli'}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'ffmpeg_location': FFMPEG_PATH,
    }
    if COOKIE_FILE:
        ydl_opts['cookiefile'] = COOKIE_FILE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            data = ydl.extract_info(url, download=False)

        fps_values = set()
        for f in data.get('formats', []):
            fps = f.get('fps')
            if fps and f.get('vcodec') != 'none':
                fps_values.add(int(fps))

        return jsonify({
            'title': data.get('title', ''),
            'has_60fps': any(f >= 60 for f in fps_values),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/download', methods=['POST'])
def download():
    url     = request.form.get('url', '').strip()
    quality = request.form.get('quality', '1080')
    fps     = request.form.get('fps', '30')

    if not url:
        return "Lütfen bir YouTube linki girin.", 400
    if quality not in ALLOWED_QUALITIES:
        quality = '1080'
    if fps not in {'30', '60'}:
        fps = '30'

    temp_dir = tempfile.mkdtemp()

    # Geniş format zinciri — en iyisinden en geniş fallback'e
    fmt = (
        f'bestvideo[height<={quality}][fps<={fps}][ext=mp4]+bestaudio[ext=m4a]'
        f'/bestvideo[height<={quality}][fps<={fps}]+bestaudio'
        f'/bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]'
        f'/bestvideo[height<={quality}]+bestaudio'
        f'/best[height<={quality}]'
        f'/bestvideo+bestaudio'
        f'/best'
    )

    ydl_opts = {
        'format': fmt,
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'ffmpeg_location': FFMPEG_PATH,
        'postprocessors': [
            {'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'},
            {'key': 'FFmpegMetadata', 'add_metadata': True},
        ],
        'quiet': True,
        'no_warnings': True,
    }
    if COOKIE_FILE:
        ydl_opts['cookiefile'] = COOKIE_FILE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info  = ydl.extract_info(url, download=True)
            title = info.get('title', 'video')

        video_files = (
            glob.glob(os.path.join(temp_dir, '*.mp4')) +
            glob.glob(os.path.join(temp_dir, '*.mkv')) +
            glob.glob(os.path.join(temp_dir, '*.webm'))
        )
        if not video_files:
            return "Video dosyası oluşturulamadı.", 500

        file_path = video_files[0]
        ext = os.path.splitext(file_path)[1]
        safe_title = "".join(c for c in title if c.isalnum() or c in " _-()[]").strip() or "video"

        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"{safe_title}{ext}",
            mimetype='video/mp4'
        )

    except yt_dlp.utils.DownloadError as e:
        return f"İndirme hatası: {str(e)}", 400
    except Exception as e:
        return f"Beklenmedik bir hata: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
