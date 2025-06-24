from flask import Flask, render_template_string, request, jsonify, send_file, abort, send_from_directory
import threading
import os
import time
from main import VideoDownloader
import tempfile
from pathlib import Path

app = Flask(__name__, static_folder='static', static_url_path='/static')
downloader = VideoDownloader()

# HTML template with modern, animated, attractive design
HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Universal Video Downloader</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(120deg, #89f7fe 0%, #66a6ff 100%);
            min-height: 100vh;
            margin: 0;
            font-family: 'Montserrat', Arial, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: rgba(255,255,255,0.95);
            border-radius: 25px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            padding: 40px 30px 30px 30px;
            max-width: 480px;
            width: 100%;
            animation: fadeIn 1.2s cubic-bezier(.39,.575,.56,1.000) both;
        }
        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(40px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        h1 {
            text-align: center;
            color: #2d3a4b;
            font-size: 2.2em;
            margin-bottom: 10px;
            font-weight: 700;
            letter-spacing: 1px;
        }
        .subtitle {
            text-align: center;
            color: #4e5d6c;
            font-size: 1.1em;
            margin-bottom: 30px;
            font-weight: 400;
        }
        .input-group {
            margin-bottom: 25px;
            position: relative;
        }
        label {
            font-weight: 600;
            color: #3a4a5d;
            margin-bottom: 8px;
            display: block;
        }
        input[type="url"] {
            width: 100%;
            padding: 15px 18px;
            border: 2px solid #e0e7ef;
            border-radius: 12px;
            font-size: 1em;
            transition: border-color 0.3s;
            outline: none;
            background: #f7fbff;
            box-sizing: border-box;
        }
        input[type="url"]:focus {
            border-color: #66a6ff;
        }
        .checkbox-group {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        .checkbox-group input[type="checkbox"] {
            accent-color: #66a6ff;
            margin-right: 8px;
        }
        .download-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(90deg, #66a6ff 0%, #89f7fe 100%);
            color: #fff;
            border: none;
            border-radius: 12px;
            font-size: 1.1em;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 4px 16px rgba(102,166,255,0.15);
            transition: background 0.3s, transform 0.2s;
            margin-bottom: 10px;
        }
        .download-btn:hover {
            background: linear-gradient(90deg, #89f7fe 0%, #66a6ff 100%);
            transform: translateY(-2px) scale(1.03);
        }
        .download-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .status {
            margin-top: 18px;
            padding: 14px 18px;
            border-radius: 10px;
            font-size: 1em;
            font-weight: 500;
            display: none;
            animation: fadeIn 0.7s;
        }
        .status.success {
            background: #e0ffe7;
            color: #1b7e3c;
            border: 1.5px solid #b2f2c9;
        }
        .status.error {
            background: #ffe0e0;
            color: #a12a2a;
            border: 1.5px solid #f2b2b2;
        }
        .loader {
            display: inline-block;
            width: 32px;
            height: 32px;
            border: 4px solid #66a6ff;
            border-radius: 50%;
            border-top: 4px solid #fff;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .platforms {
            display: flex;
            flex-wrap: wrap;
            gap: 7px;
            justify-content: center;
            margin-bottom: 18px;
        }
        .platform {
            background: linear-gradient(45deg, #f0f8ff, #e6f3ff);
            padding: 5px 13px;
            border-radius: 15px;
            font-size: 13px;
            border: 1.5px solid #dbeafe;
            font-weight: 500;
            color: #3a4a5d;
            box-shadow: 0 2px 6px rgba(102,166,255,0.07);
            animation: popIn 0.7s cubic-bezier(.39,.575,.56,1.000) both;
        }
        @keyframes popIn {
            0% { opacity: 0; transform: scale(0.7); }
            100% { opacity: 1; transform: scale(1); }
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #7a8ca3;
            font-size: 0.95em;
        }
        .download-link {
            display: inline-block;
            margin-top: 10px;
            padding: 10px 20px;
            background: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
        }
        .download-link:hover {
            background: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Universal Video Downloader</h1>
        <div class="subtitle">Download videos from any platform. Remove watermarks automatically!</div>
        <div class="platforms">
            <span class="platform">YouTube</span>
            <span class="platform">Instagram</span>
            <span class="platform">TikTok</span>
            <span class="platform">Facebook</span>
            <span class="platform">Twitter/X</span>
            <span class="platform">Snapchat</span>
            <span class="platform">Reddit</span>
            <span class="platform">Vimeo</span>
            <span class="platform">Twitch</span>
            <span class="platform">More...</span>
        </div>
        <form id="downloadForm" autocomplete="off">
            <div class="input-group">
                <label for="videoUrl">Paste Video URL</label>
                <input type="url" id="videoUrl" name="videoUrl" placeholder="https://..." required>
            </div>
            <div class="checkbox-group">
                <input type="checkbox" id="removeWatermark" name="removeWatermark" checked>
                <label for="removeWatermark">Remove watermark (if possible)</label>
            </div>
            <button type="submit" class="download-btn" id="downloadBtn">Download Video</button>
        </form>
        <div id="loader" class="loader" style="display:none;"></div>
        <div id="status" class="status"></div>
        <div class="footer">&copy; 2024 Universal Video Downloader. <br> For educational and personal use only.</div>
    </div>
    <script>
        const form = document.getElementById('downloadForm');
        const statusDiv = document.getElementById('status');
        const loader = document.getElementById('loader');
        const downloadBtn = document.getElementById('downloadBtn');
        
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            statusDiv.style.display = 'none';
            loader.style.display = 'block';
            downloadBtn.disabled = true;
            downloadBtn.textContent = 'Downloading...';
            
            const url = document.getElementById('videoUrl').value.trim();
            const removeWatermark = document.getElementById('removeWatermark').checked;
            
            fetch('/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, removeWatermark })
            })
            .then(res => res.json())
            .then(data => {
                loader.style.display = 'none';
                downloadBtn.disabled = false;
                downloadBtn.textContent = 'Download Video';
                statusDiv.style.display = 'block';
                
                if (data.success) {
                    statusDiv.className = 'status success';
                    let html = '✅ ' + data.message;
                    if (data.file_url) {
                        html += `<br><a href="${data.file_url}" class="download-link" download>📥 Download File</a>`;
                    }
                    statusDiv.innerHTML = html;
                } else {
                    statusDiv.className = 'status error';
                    statusDiv.textContent = '❌ ' + data.message;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                loader.style.display = 'none';
                downloadBtn.disabled = false;
                downloadBtn.textContent = 'Download Video';
                statusDiv.style.display = 'block';
                statusDiv.className = 'status error';
                statusDiv.textContent = '❌ An error occurred. Please try again.';
            });
        });
    </script>
</body>
</html>
'''

# Thread-safe download status
download_results = {}

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/download', methods=['POST'])
def download():
    """Download video endpoint with better error handling"""
    data = request.get_json()
    url = data.get('url')
    remove_watermark = data.get('removeWatermark', True)
    
    if not url:
        return jsonify({'success': False, 'message': 'No URL provided.'})
    
    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        return jsonify({'success': False, 'message': 'Please provide a valid URL starting with http:// or https://'})
    
    # Create unique session ID for this download
    session_id = str(time.time()).replace('.', '')
    status_updates = []
    
    def status_callback(msg, error=False):
        status_updates.append((msg, error))
        print(f"Status: {msg}")
    
    # Create downloader instance for this request
    current_downloader = VideoDownloader(headless=True, status_callback=status_callback)
    print(f"[DEBUG] Using download path: {current_downloader.download_path}")
    
    def download_worker():
        """Worker function to handle download"""
        try:
            # Detect platform
            platform = current_downloader.detect_platform_from_url(url)
            print(f"[DEBUG] Detected platform: {platform}")
            
            # Download video
            success = current_downloader.download_video(url)
            print(f"[DEBUG] Download success: {success}")
            
            if not success:
                print(f"[DEBUG] Download failed for URL: {url}")
                download_results[session_id] = {
                    'success': False,
                    'message': 'Download failed. Please check the URL and try again.',
                    'file_url': None
                }
                return
            
            # Find downloaded files
            files = []
            if os.path.exists(current_downloader.download_path):
                print(f"[DEBUG] Scanning directory: {current_downloader.download_path}")
                for file in os.listdir(current_downloader.download_path):
                    file_path = os.path.join(current_downloader.download_path, file)
                    print(f"[DEBUG] Found file: {file_path}")
                    if os.path.isfile(file_path):
                        # Check if file was created recently (within last 5 minutes)
                        file_mtime = os.path.getmtime(file_path)
                        if time.time() - file_mtime < 300:  # 5 minutes
                            file_size = os.path.getsize(file_path)
                            if file_size > 1024:  # At least 1KB
                                files.append({
                                    'name': file,
                                    'path': file_path,
                                    'size': file_size,
                                    'mtime': file_mtime
                                })
            print(f"[DEBUG] Video files found: {[f['name'] for f in files]}")
            
            # Sort by modification time to get the latest file
            if files:
                # Filter for video files
                video_exts = ('.mp4', '.mkv', '.webm', '.mov', '.avi', '.flv', '.m4v')
                video_files = [f for f in files if f['name'].lower().endswith(video_exts)]
                
                if video_files:
                    # Get the most recent video file
                    latest_file = max(video_files, key=lambda x: x['mtime'])
                    result_path = latest_file['path']
                    
                    # Remove watermark if requested and FFmpeg is available
                    if remove_watermark and current_downloader.ffmpeg_available:
                        status_callback('🧹 Removing watermarks...')
                        cleaned_path = current_downloader.remove_watermark_from_video(result_path, platform)
                        if cleaned_path and cleaned_path != result_path and os.path.exists(cleaned_path):
                            result_path = cleaned_path
                            status_callback('✨ Watermarks removed successfully!')
                    
                    # Store result
                    filename = os.path.basename(result_path)
                    file_url = f'/file/{filename}'
                    
                    download_results[session_id] = {
                        'success': True,
                        'message': f'Download completed: {filename}',
                        'file_url': file_url,
                        'file_path': result_path,
                        'filename': filename,
                        'size': os.path.getsize(result_path)
                    }
                else:
                    download_results[session_id] = {
                        'success': False,
                        'message': 'No video files found after download.',
                        'file_url': None
                    }
            else:
                download_results[session_id] = {
                    'success': False,
                    'message': 'No files were downloaded. The URL might be invalid or the content may be private.',
                    'file_url': None
                }
                
        except Exception as e:
            error_msg = str(e)
            print(f"Download error: {error_msg}")
            download_results[session_id] = {
                'success': False,
                'message': f'Download error: {error_msg[:100]}',
                'file_url': None
            }
    
    # Start download in background thread
    thread = threading.Thread(target=download_worker)
    thread.daemon = True
    thread.start()
    
    # Wait for download to complete (with timeout)
    timeout = 120  # 2 minutes timeout
    start_time = time.time()
    
    while session_id not in download_results:
        if time.time() - start_time > timeout:
            return jsonify({
                'success': False,
                'message': 'Download timeout. The video might be too large or the server is busy.'
            })
        time.sleep(1)
    
    # Get result
    result = download_results.pop(session_id, {
        'success': False,
        'message': 'Unknown error occurred',
        'file_url': None
    })
    
    return jsonify(result)

@app.route('/file/<filename>')
def serve_file(filename):
    """Serve downloaded files with proper headers"""
    try:
        # Security check - only allow files from download directory
        safe_filename = os.path.basename(filename)  # Remove any path traversal
        file_path = os.path.join(downloader.download_path, safe_filename)
        print(f"[DEBUG] Serving file: {file_path}")
        
        # Check if file exists and is actually a file
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            print(f"[DEBUG] File not found: {file_path}")
            abort(404)
        
        # Check file size to ensure it's not empty
        if os.path.getsize(file_path) == 0:
            print(f"[DEBUG] File is empty: {file_path}")
            abort(404)
        
        # Determine MIME type based on extension
        ext = os.path.splitext(filename)[1].lower()
        mime_types = {
            '.mp4': 'video/mp4',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
            '.mov': 'video/quicktime',
            '.avi': 'video/x-msvideo',
            '.flv': 'video/x-flv',
            '.m4v': 'video/mp4'
        }
        
        mimetype = mime_types.get(ext, 'application/octet-stream')
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        print(f"Error serving file {filename}: {e}")
        abort(404)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'download_path': downloader.download_path})

@app.route('/download')
def download_page():
    return send_from_directory(app.static_folder, 'download.html')

@app.route('/about')
def about_page():
    return send_from_directory(app.static_folder, 'about.html')

@app.route('/pricing')
def pricing_page():
    return send_from_directory(app.static_folder, 'pricing.html')

@app.route('/contact')
def contact_page():
    return send_from_directory(app.static_folder, 'contact.html')

@app.route('/terms')
def terms_page():
    return send_from_directory(app.static_folder, 'terms.html')

@app.route('/privacy')
def privacy_page():
    return send_from_directory(app.static_folder, 'privacy.html')

if __name__ == '__main__':
    # Ensure download directory exists
    os.makedirs(downloader.download_path, exist_ok=True)
    print(f"📁 Download directory: {downloader.download_path}")
    print(f"🌐 Starting server on http://localhost:5000")
    
    app.run(debug=True, port=5000, threaded=True)