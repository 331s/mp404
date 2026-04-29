from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import tempfile
import glob

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

    ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            data = ydl.extract_info(url, download=False)

        formats = data.get('formats', [])
        fps_values = set()
        for f in formats:
            fps = f.get('fps')
            if fps and f.get('vcodec') != 'none':
                fps_values.add(int(fps))

        return jsonify({
            'title':   data.get('title', ''),
            'has_60fps': any(f >= 60 for f in fps_values),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/download', methods=['POST'])
def download():
    url     = request.form.get('url', '').strip()
    quality = request.form.get('quality', '1080')

    if not url:
        return "Lütfen bir YouTube linki girin.", 400

    fps = request.form.get('fps', '30')
    if fps not in {'30', '60'}:
        fps = '30'

    if quality not in ALLOWED_QUALITIES:
        quality = '1080'

    temp_dir = tempfile.mkdtemp()

    ydl_opts = {
        'format': (
            f'bestvideo[height<={quality}][fps<={fps}][ext=mp4]+bestaudio[ext=m4a]'
            f'/bestvideo[height<={quality}][fps<={fps}]+bestaudio'
            f'/bestvideo[height<={quality}]+bestaudio'
            f'/best[height<={quality}]'
        ),
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'postprocessors': [
            {
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            },
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            },
        ],
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info  = ydl.extract_info(url, download=True)
            title = info.get('title', 'video')

        mp4_files = glob.glob(os.path.join(temp_dir, '*.mp4'))
        if not mp4_files:
            # Fallback: diğer video formatlarını ara
            video_files = glob.glob(os.path.join(temp_dir, '*.mkv')) + \
                          glob.glob(os.path.join(temp_dir, '*.webm'))
            if not video_files:
                return "Video dosyası oluşturulamadı.", 500
            mp4_files = video_files

        file_path = mp4_files[0]
        ext = os.path.splitext(file_path)[1]

        safe_title = "".join(c for c in title if c.isalnum() or c in " _-()[]").strip() or "video"
        download_name = f"{safe_title}{ext}"

        return send_file(
            file_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='video/mp4'
        )

    except yt_dlp.utils.DownloadError:
        return "İndirme hatası: Video bulunamadı veya erişim kısıtlı.", 400
    except Exception as e:
        return f"Beklenmedik bir hata oluştu: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
