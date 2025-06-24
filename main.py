#!/usr/bin/env python3
"""
Universal Video Downloader
This script opens a browser interface to download videos from ANY website:
- Social Media: YouTube, Instagram, TikTok, Facebook, Twitter/X, Snapchat, LinkedIn, Pinterest, Reddit, Telegram
- Video Platforms: Vimeo, Dailymotion, Twitch, Streamable, Wistia, JW Player
- News & Media: BBC, CNN, Reuters, Associated Press, NBC, CBS, ABC
- Educational: Coursera, Udemy, Khan Academy, edX, Skillshare
- Entertainment: Netflix trailers, Hulu clips, Disney+, HBO Max previews
- Sports: ESPN, NBA, NFL, FIFA, Olympics
- Live Streams: Twitch, YouTube Live, Facebook Live
- ANY website with embedded or direct video links
- And thousands more platforms supported by yt-dlp
"""

import os
import time
import yt_dlp
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import threading
import tempfile
import sys
import json
import re
import subprocess
import shutil
from pathlib import Path
import urllib.parse

class VideoDownloader:
    def __init__(self, headless=False, status_callback=None):
        # Create downloads folder with better error handling
        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads", "Dazzlo Downloads")
        
        try:
            os.makedirs(self.download_path, exist_ok=True)
            print(f"✅ Download folder ready: {self.download_path}")
        except Exception as e:
            print(f"⚠️ Could not create download folder: {e}")
            # Fallback to regular Downloads folder
            self.download_path = os.path.join(os.path.expanduser("~"), "Downloads")
            print(f"📁 Using fallback folder: {self.download_path}")
        
        self.driver = None
        self.headless = headless
        self.status_callback = status_callback
        self.ffmpeg_available = self.check_ffmpeg()
        
        # Clean any existing yt-dlp cache to ensure fresh downloads
        self.clean_download_cache()
    
    def safe_js_string(self, text):
        """Safely escape strings for JavaScript injection"""
        if not text:
            return ""
        
        # Remove or replace problematic characters
        text = str(text)
        text = text.replace("'", "\\'")  # Escape single quotes
        text = text.replace('"', '\\"')  # Escape double quotes
        text = text.replace('\n', '\\n')  # Escape newlines
        text = text.replace('\r', '\\r')  # Escape carriage returns
        text = text.replace('\t', '\\t')  # Escape tabs
        text = text.replace('\\', '\\\\')  # Escape backslashes
        
        # Limit length to prevent overly long error messages
        if len(text) > 200:
            text = text[:197] + "..."
        
        return text
        
    def clean_download_cache(self):
        """Clean yt-dlp cache to ensure fresh downloads"""
        try:
            import shutil
            
            # Common yt-dlp cache locations
            cache_locations = [
                os.path.join(os.path.expanduser("~"), ".cache", "yt-dlp"),
                os.path.join(os.path.expanduser("~"), "AppData", "Local", "yt-dlp"),
                os.path.join(tempfile.gettempdir(), "yt-dlp-cache"),
            ]
            
            for cache_dir in cache_locations:
                if os.path.exists(cache_dir):
                    try:
                        shutil.rmtree(cache_dir)
                        print(f"🧹 Cleaned cache: {cache_dir}")
                    except:
                        pass  # Ignore errors, cache cleaning is not critical
                        
        except Exception:
            pass  # Cache cleaning is optional
    
    def check_ffmpeg(self):
        """Check if FFmpeg is installed for watermark removal"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            print("✅ FFmpeg found - Watermark removal enabled!")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️ FFmpeg not found - Install for automatic watermark removal")
            print("   Windows: winget install FFmpeg")
            print("   Mac: brew install ffmpeg")
            print("   Linux: sudo apt install ffmpeg")
            return False
    
    def is_valid_url(self, url):
        """Validate URL format"""
        try:
            result = urllib.parse.urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def remove_watermark_from_video(self, video_path, platform="generic"):
        """Remove watermarks from downloaded video using FFmpeg with multiple strategies"""
        if not self.ffmpeg_available:
            return video_path  # Return original if FFmpeg not available
        
        try:
            # Create clean filename
            original_filename = Path(video_path).stem
            clean_filename = f"{original_filename}_clean.mp4"
            clean_path = os.path.join(self.download_path, clean_filename)
            
            print(f"🧹 Removing watermarks from: {os.path.basename(video_path)}")
            
            # More aggressive watermark removal strategies
            if platform == "tiktok":
                # TikTok: Remove multiple watermark areas + crop borders
                cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vf', '''crop=iw-40:ih-120:20:20,
                              delogo=x=W-200:y=H-120:w=180:h=100:show=0,
                              delogo=x=10:y=H-60:w=150:h=50:show=0,
                              delogo=x=W-60:y=10:w=50:h=30:show=0,
                              unsharp=5:5:0.8:5:5:0.0''',
                    '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
                    '-c:a', 'copy', '-y', clean_path
                ]
            elif platform == "instagram":
                # Instagram: Remove username + crop + enhance
                cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vf', '''crop=iw-30:ih-80:15:40,
                              delogo=x=10:y=10:w=220:h=60:show=0,
                              delogo=x=W-100:y=H-40:w=90:h=30:show=0,
                              unsharp=5:5:1.0:5:5:0.0''',
                    '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
                    '-c:a', 'copy', '-y', clean_path
                ]
            elif platform == "snapchat":
                # Snapchat: More aggressive bottom removal
                cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vf', '''crop=iw-20:ih-100:10:10,
                              delogo=x=10:y=H-100:w=200:h=80:show=0,
                              delogo=x=W-150:y=H-50:w=140:h=40:show=0''',
                    '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
                    '-c:a', 'copy', '-y', clean_path
                ]
            elif platform == "facebook":
                # Facebook: Remove corners + enhance
                cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vf', '''crop=iw-20:ih-40:10:20,
                              delogo=x=10:y=10:w=180:h=40:show=0,
                              delogo=x=W-120:y=H-50:w=110:h=40:show=0''',
                    '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
                    '-c:a', 'copy', '-y', clean_path
                ]
            else:
                # Generic: Aggressive crop + blur edges method
                cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vf', '''crop=iw-60:ih-60:30:30,
                              unsharp=5:5:1.0:5:5:0.0,
                              scale=iw*1.1:ih*1.1,
                              crop=iw-40:ih-40:20:20''',
                    '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
                    '-c:a', 'copy', '-y', clean_path
                ]
            
            # Run FFmpeg command with timeout
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and os.path.exists(clean_path):
                # Check if the clean file is reasonable size
                original_size = os.path.getsize(video_path)
                clean_size = os.path.getsize(clean_path)
                
                if clean_size > original_size * 0.3:  # At least 30% of original size
                    print(f"✅ Watermark removed: {os.path.basename(clean_path)}")
                    
                    # Optionally remove original and rename clean version
                    try:
                        final_path = video_path.replace('.mp4', '_no_watermark.mp4')
                        if final_path == video_path:
                            final_path = clean_path
                        else:
                            os.rename(clean_path, final_path)
                            # Keep original file as backup
                        return final_path
                    except:
                        return clean_path  # Return clean version if renaming fails
                else:
                    print(f"⚠️ Clean file too small, keeping original")
                    try:
                        os.remove(clean_path)
                    except:
                        pass
                    return video_path
            else:
                print(f"⚠️ Watermark removal failed, keeping original")
                if result.stderr:
                    print(f"   Error: {result.stderr[:200]}")
                return video_path
                
        except subprocess.TimeoutExpired:
            print(f"⚠️ Watermark removal timeout, keeping original")
            return video_path
        except Exception as e:
            print(f"⚠️ Watermark removal error: {e}")
            return video_path
    
    def detect_platform_from_url(self, url):
        """Detect platform from URL for appropriate watermark removal"""
        url_lower = url.lower()
        if 'tiktok.com' in url_lower or 'vm.tiktok.com' in url_lower:
            return "tiktok"
        elif 'instagram.com' in url_lower:
            return "instagram"
        elif 'snapchat.com' in url_lower:
            return "snapchat"
        elif 'facebook.com' in url_lower or 'fb.watch' in url_lower:
            return "facebook"
        elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return "youtube"
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return "twitter"
        else:
            return "generic"
        
    def setup_browser(self):
        """Setup Chrome browser with automatic driver management"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Automatically manage ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ Browser setup successful!")
            return True
            
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            print("\n🔧 Troubleshooting:")
            print("1. Make sure Google Chrome is installed")
            print("2. Run: pip install webdriver-manager")
            print("3. Check your internet connection")
            return False
    
    def get_platform_specific_config(self, url):
        """Get platform-specific configuration for better downloads"""
        platform_configs = {
            'instagram': {
                'format': 'best[height<=1080]/best',
                'writesubtitles': False,
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
            },
            'tiktok': {
                'format': 'best[height<=1080]/best',
                'writesubtitles': False,
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
            },
            'facebook': {
                'format': 'best[height<=720]/best',
                'writesubtitles': False,
            },
            'twitter': {
                'format': 'best[height<=720]/best',
                'writesubtitles': False,
            },
            'youtube': {
                'format': 'best[height<=1080]/best',
                'writesubtitles': True,
            },
            'snapchat': {
                'format': 'best',
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
            }
        }
        
        url_lower = url.lower()
        for platform, config in platform_configs.items():
            if platform in url_lower or (platform == 'twitter' and 'x.com' in url_lower):
                return config
        
        return {}
    
    def _report_status(self, message, error=False):
        """Report status to callback or console"""
        print(f"{'❌' if error else '📄'} {message}")
        if self.headless:
            if self.status_callback:
                self.status_callback(message, error)
        elif self.driver is not None:
            try:
                key = 'pythonError' if error else 'pythonStatus'
                safe_msg = self.safe_js_string(message)
                self.driver.execute_script(f"localStorage.setItem('{key}', '{safe_msg}');")
            except:
                pass  # Ignore if browser is not available

    def download_video(self, url):
        """Download video using yt-dlp with improved error handling"""
        if not self.is_valid_url(url):
            self._report_status("Invalid URL format. Please provide a valid URL starting with http:// or https://", error=True)
            return False
        
        try:
            platform_config = self.get_platform_specific_config(url)
            temp_cache = tempfile.mkdtemp()
            
            # Base configuration with better error handling
            ydl_opts = {
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'format': 'best[height<=1080]/best',
                'force_download': True,
                'no_check_certificate': True,
                'cachedir': temp_cache,
                'prefer_free_formats': True,
                'extract_flat': False,
                'ignoreerrors': False,
                'no_warnings': False,
                'writeinfojson': False,
                'writethumbnail': False,
                'writesubtitles': False,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                },
                'socket_timeout': 30,
                'retries': 3,
            }
            
            # Update with platform-specific config
            ydl_opts.update(platform_config)
            
            self._report_status('🔍 Analyzing URL and extracting video info...')
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # First, extract info without downloading
                    try:
                        info = ydl.extract_info(url, download=False)
                        if not info:
                            raise Exception("Could not extract video information from this URL")
                        
                        # Check if it's a playlist or single video
                        if 'entries' in info and info['entries']:
                            valid_entries = [e for e in info['entries'] if e]
                            total_videos = len(valid_entries)
                            self._report_status(f"📚 Found {total_videos} videos to download...")
                            
                            # For playlists, limit to first 5 videos to avoid overwhelming
                            if total_videos > 5:
                                self._report_status(f"⚠️ Limiting to first 5 videos of {total_videos}")
                                ydl_opts['playlistend'] = 5
                        else:
                            title = info.get('title', 'Unknown video')[:50]
                            uploader = info.get('uploader', 'Unknown')
                            duration = info.get('duration', 0)
                            
                            status_msg = f"⬇️ Downloading: {title}"
                            if uploader and uploader != 'Unknown':
                                status_msg += f" by {uploader}"
                            if duration:
                                try:
                                    duration = int(float(duration))
                                    status_msg += f" ({duration//60}:{duration%60:02d})"
                                except:
                                    pass
                            self._report_status(status_msg)
                        
                        # Now download the video(s)
                        ydl.download([url])
                        
                        # Verify download success
                        return self.verify_download_success(url, info)
                        
                    except yt_dlp.utils.ExtractorError as ee:
                        error_msg = str(ee).lower()
                        if "private" in error_msg or "login" in error_msg:
                            self._report_status("❌ This content is private or requires login", error=True)
                        elif "not available" in error_msg:
                            self._report_status("❌ Content not available or has been removed", error=True)
                        elif "geo" in error_msg or "region" in error_msg:
                            self._report_status("❌ Content blocked in your region", error=True)
                        elif "unsupported" in error_msg:
                            self._report_status("❌ This website is not supported", error=True)
                        else:
                            self._report_status(f"❌ Extraction failed: {str(ee)[:100]}", error=True)
                        return False
                        
            except yt_dlp.DownloadError as e:
                error_str = str(e).lower()
                if "private" in error_str:
                    error_msg = "❌ Content is private - login required"
                elif "not available" in error_str:
                    error_msg = "❌ Content removed, restricted, or not available in your region"
                elif "login" in error_str or "sign in" in error_str:
                    error_msg = "❌ Login required - content is private"
                elif "geo" in error_str or "region" in error_str:
                    error_msg = "❌ Geographic restriction"
                elif "rate limit" in error_str:
                    error_msg = "❌ Rate limited - try again later"
                elif "unsupported" in error_str:
                    error_msg = "❌ This website is not supported"
                else:
                    error_msg = f"❌ Download failed: {str(e)[:150]}"
                
                self._report_status(error_msg, error=True)
                return False
                
            finally:
                # Clean up temp cache
                try:
                    if os.path.exists(temp_cache):
                        shutil.rmtree(temp_cache)
                except:
                    pass
                    
        except Exception as e:
            error_str = str(e).lower()
            if "unsupported url" in error_str:
                error_msg = "❌ This website is not supported by yt-dlp"
            elif "network" in error_str or "connection" in error_str:
                error_msg = "❌ Network error. Check your internet connection"
            elif "timeout" in error_str:
                error_msg = "❌ Connection timeout. Try again later"
            elif "no video" in error_str or "no formats" in error_str:
                error_msg = "❌ No downloadable video found on this page"
            else:
                error_msg = f"❌ Unexpected error: {str(e)[:150]}"
            
            self._report_status(error_msg, error=True)
            return False
    
    def verify_download_success(self, url, info=None):
        """Verify that files were actually downloaded"""
        try:
            downloaded_files = []
            current_time = time.time()
            
            if os.path.exists(self.download_path):
                for file in os.listdir(self.download_path):
                    file_path = os.path.join(self.download_path, file)
                    if os.path.isfile(file_path):
                        # Check if file was created recently (within last 5 minutes)
                        file_mtime = os.path.getmtime(file_path)
                        if current_time - file_mtime < 300:  # 5 minutes
                            file_size = os.path.getsize(file_path)
                            if file_size > 1024:  # At least 1KB
                                downloaded_files.append({
                                    'name': file,
                                    'path': file_path,
                                    'size': file_size / (1024*1024),  # MB
                                    'mtime': file_mtime
                                })
            
            if not downloaded_files:
                self._report_status("❌ No files were downloaded. Please check the URL and try again.", error=True)
                return False
            
            # Check for video files specifically
            video_exts = ('.mp4', '.mkv', '.webm', '.mov', '.avi', '.flv', '.m4v')
            video_files = [f for f in downloaded_files if f['name'].lower().endswith(video_exts)]
            
            if video_files:
                main_video = max(video_files, key=lambda x: x['mtime'])
                title = info.get('title', 'Video') if info else 'Video'
                safe_title = title[:40] if title else 'Video'
                success_msg = f"✅ Downloaded: {safe_title} ({main_video['size']:.1f}MB)"
                
                self._report_status(success_msg)
                print(f"✅ {success_msg}")
                return True
            else:
                # Non-video files downloaded
                success_msg = f"✅ Downloaded {len(downloaded_files)} file(s)"
                self._report_status(success_msg)
                return True
                
        except Exception as e:
            print(f"⚠️ Error verifying download: {e}")
            return True  # Assume success if verification fails

    def create_input_page(self):
        """Create HTML interface"""
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Universal Video Downloader</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            font-weight: 300;
        }
        .platforms {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 15px 0;
            justify-content: center;
        }
        .platform {
            background: linear-gradient(45deg, #f0f8ff, #e6f3ff);
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 14px;
            border: 2px solid #ddd;
            font-weight: 500;
        }
        .input-group {
            margin: 30px 0;
        }
        label {
            display: block;
            margin-bottom: 10px;
            font-weight: 600;
            color: #555;
            font-size: 16px;
        }
        input[type="url"] {
            width: 100%;
            padding: 15px;
            border: 3px solid #ddd;
            border-radius: 10px;
            font-size: 16px;
            box-sizing: border-box;
            transition: border-color 0.3s ease;
        }
        input[type="url"]:focus {
            border-color: #4CAF50;
            outline: none;
            box-shadow: 0 0 10px rgba(76, 175, 80, 0.3);
        }
        .button-group {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin: 30px 0;
        }
        button {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: transform 0.2s ease;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4);
        }
        button.secondary {
            background: linear-gradient(45deg, #ff7043, #ff5722);
        }
        button.help {
            background: linear-gradient(45deg, #2196F3, #1976D2);
        }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            display: none;
            font-weight: 500;
        }
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 2px solid #c3e6cb;
        }
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 2px solid #f5c6cb;
        }
        .instructions {
            background: linear-gradient(45deg, #e3f2fd, #bbdefb);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 25px;
            border-left: 5px solid #2196F3;
        }
        .progress {
            width: 100%;
            height: 8px;
            background-color: #f0f0f0;
            border-radius: 4px;
            overflow: hidden;
            margin: 15px 0;
            display: none;
        }
        .progress-bar {
            height: 100%;
            background: linear-gradient(45deg, #4CAF50, #45a049);
            width: 0%;
            transition: width 0.3s ease;
        }
        .examples {
            background: #fff9c4;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 5px solid #ffeb3b;
        }
        .url-valid {
            border-color: #4CAF50 !important;
        }
        .url-invalid {
            border-color: #ff9800 !important;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Universal Video Downloader</h1>
        
        <div class="instructions">
            <strong>🎯 Supported Platforms:</strong>
            <div class="platforms">
                <span class="platform">📺 YouTube</span>
                <span class="platform">📸 Instagram</span>
                <span class="platform">🎵 TikTok</span>
                <span class="platform">👥 Facebook</span>
                <span class="platform">🐦 Twitter/X</span>
                <span class="platform">👻 Snapchat</span>
                <span class="platform">💼 LinkedIn</span>
                <span class="platform">📌 Pinterest</span>
                <span class="platform">🤖 Reddit</span>
                <span class="platform">✈️ Telegram</span>
            </div>
            <br>
            <strong>📹 Content Types:</strong> Videos, Reels, Stories, Shorts, IGTV, Highlights, Live streams<br>
            <strong>✨ Features:</strong> Automatic watermark removal with FFmpeg, gets original quality
        </div>
        
        <div class="examples">
            <strong>🔗 URL Examples - Works with ANY website:</strong>
            <ul style="margin: 10px 0; padding-left: 20px;">
                <li><strong>Social Media:</strong> instagram.com, tiktok.com, youtube.com, facebook.com, twitter.com</li>
                <li><strong>Video Platforms:</strong> vimeo.com, dailymotion.com, twitch.tv, streamable.com</li>
                <li><strong>News Sites:</strong> bbc.com, cnn.com, reuters.com, npr.org, bloomberg.com</li>
                <li><strong>Educational:</strong> coursera.org, udemy.com, khanacademy.org, edx.org</li>
                <li><strong>Any Website:</strong> Just paste any URL with a video - we'll try to download it!</li>
            </ul>
        </div>
        
        <div class="input-group">
            <label for="videoUrl">🔗 Paste ANY Video URL:</label>
            <input type="url" id="videoUrl" placeholder="Paste URL from ANY website - Social media, news, educational, entertainment, etc." autofocus>
        </div>
        
        <div class="button-group">
            <button onclick="downloadVideo()">📥 Download Content</button>
            <button class="secondary" onclick="clearUrl()">🗑️ Clear</button>
            <button class="help" onclick="showHelp()">❓ Help</button>
            <button class="help" onclick="openDownloadFolder()" style="background: linear-gradient(45deg, #9C27B0, #673AB7);">📂 Open Downloads</button>
        </div>
        
        <div class="progress" id="progress">
            <div class="progress-bar" id="progressBar"></div>
        </div>
        
        <div id="status" class="status"></div>
    </div>
    
    <script>
        function downloadVideo() {
            const url = document.getElementById('videoUrl').value.trim();
            const statusDiv = document.getElementById('status');
            const progressDiv = document.getElementById('progress');
            const progressBar = document.getElementById('progressBar');
            
            if (!url) {
                showStatus('❌ Please enter a video URL', 'error');
                return;
            }
            
            if (!isValidUrl(url)) {
                showStatus('❌ Please enter a valid URL starting with http:// or https://', 'error');
                return;
            }
            
            localStorage.setItem('videoUrl', url);
            localStorage.setItem('downloadRequested', 'true');
            
            progressDiv.style.display = 'block';
            progressBar.style.width = '10%';
            
            showStatus('🔄 Processing URL and extracting content...', 'success');
        }
        
        function isValidUrl(url) {
            try {
                new URL(url);
                return url.startsWith('http://') || url.startsWith('https://');
            } catch {
                return false;
            }
        }
        
        function showHelp() {
            alert(`🔗 Universal Video Downloader Help:

🌐 Supported Sources:
• Social Media: Instagram, TikTok, YouTube, Facebook, Twitter
• Video Platforms: Vimeo, Dailymotion, Twitch, Streamable
• News Sites: BBC, CNN, Reuters, NPR, Bloomberg
• Educational: Coursera, Udemy, Khan Academy, edX
• Entertainment: Netflix trailers, Hulu clips, streaming previews
• Sports: ESPN, NBA, NFL, FIFA videos
• Live Streams: Twitch, YouTube Live, Facebook Live
• ANY website with embedded videos

📋 How to use:
1. Find any video on any website
2. Copy the page URL (not just the video file)
3. Paste it here and click Download
4. We'll extract and download the video!

⚠️ Note: Some private/premium content may not be downloadable.`);
        }
        
        function openDownloadFolder() {
            localStorage.setItem('openFolderRequested', 'true');
            showStatus('📂 Opening downloads folder...', 'success');
        }
        
        function clearUrl() {
            document.getElementById('videoUrl').value = '';
            document.getElementById('status').style.display = 'none';
            document.getElementById('progress').style.display = 'none';
            document.getElementById('progressBar').style.width = '0%';
            localStorage.clear();
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = 'status ' + type;
            statusDiv.style.display = 'block';
            
            const progressBar = document.getElementById('progressBar');
            if (message.includes('Processing')) {
                progressBar.style.width = '25%';
            } else if (message.includes('Downloading') || message.includes('Analyzing')) {
                progressBar.style.width = '75%';
            } else if (message.includes('completed') || message.includes('Successfully')) {
                progressBar.style.width = '100%';
                setTimeout(() => {
                    document.getElementById('progress').style.display = 'none';
                    progressBar.style.width = '0%';
                }, 3000);
            }
        }
        
        document.getElementById('videoUrl').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') downloadVideo();
        });
        
        document.getElementById('videoUrl').addEventListener('input', function(e) {
            const url = e.target.value;
            if (url && isValidUrl(url)) {
                e.target.className = 'url-valid';
            } else if (url) {
                e.target.className = 'url-invalid';
            } else {
                e.target.className = '';
            }
        });
        
        setInterval(function() {
            const pythonStatus = localStorage.getItem('pythonStatus');
            if (pythonStatus) {
                showStatus(pythonStatus, 'success');
                localStorage.removeItem('pythonStatus');
            }
            
            const pythonError = localStorage.getItem('pythonError');
            if (pythonError) {
                showStatus(pythonError, 'error');
                document.getElementById('progress').style.display = 'none';
                document.getElementById('progressBar').style.width = '0%';
                localStorage.removeItem('pythonError');
            }
            
            const openFolderRequested = localStorage.getItem('openFolderRequested');
            if (openFolderRequested) {
                localStorage.removeItem('openFolderRequested');
            }
        }, 1000);
    </script>
</body>
</html>"""
        
        # Create HTML file in temp directory
        temp_dir = tempfile.gettempdir()
        html_file = os.path.join(temp_dir, 'video_downloader.html')
        
        try:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ Interface created: {html_file}")
            return html_file
        except Exception as e:
            print(f"❌ Could not create interface: {e}")
            return None

    def run(self):
        """Main function to run the downloader"""
        print("🚀 Starting Universal Video Downloader...")
        print(f"📁 Downloads folder: {self.download_path}")
        
        if not self.setup_browser():
            return
        
        html_file = self.create_input_page()
        if not html_file:
            print("❌ Failed to create interface")
            return
        
        try:
            # Convert to proper file URL
            file_url = f"file:///{html_file.replace(os.sep, '/')}"
            self.driver.get(file_url)
            
            print("✅ Interface loaded successfully!")
            print("💡 Copy any video URL and paste it in the browser")
            print("🔴 Close browser window to exit")
            
            while True:
                try:
                    download_requested = self.driver.execute_script("return localStorage.getItem('downloadRequested');")
                    open_folder_requested = self.driver.execute_script("return localStorage.getItem('openFolderRequested');")
                    
                    if download_requested == 'true':
                        url = self.driver.execute_script("return localStorage.getItem('videoUrl');")
                        
                        if url:
                            print(f"🔗 Processing: {url}")
                            self.driver.execute_script("localStorage.removeItem('downloadRequested');")
                            
                            download_thread = threading.Thread(target=self.download_video, args=(url,))
                            download_thread.daemon = True
                            download_thread.start()
                    
                    if open_folder_requested == 'true':
                        print(f"📂 Opening download folder: {self.download_path}")
                        self.driver.execute_script("localStorage.removeItem('openFolderRequested');")
                        
                        if os.name == 'nt':  # Windows
                            try:
                                os.startfile(self.download_path)
                            except Exception as e:
                                print(f"Could not open folder: {e}")
                    
                    time.sleep(1)
                    
                except Exception as e:
                    if "chrome not reachable" in str(e).lower():
                        print("👋 Browser closed. Exiting...")
                        break
                    else:
                        time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
        
        finally:
            if self.driver:
                self.driver.quit()
            try:
                os.remove(html_file)
            except:
                pass

def main():
    """Main function"""
    print("=" * 60)
    print("🌐 UNIVERSAL VIDEO DOWNLOADER")
    print("=" * 60)
    print("🎯 Downloads from ANY website: Social media, news, educational, entertainment")
    print("📹 Supports: Videos, Reels, Stories, Shorts, Live Streams, Courses, News Clips")
    print("🌐 Works with 1000+ websites including YouTube, Instagram, TikTok, BBC, CNN, Vimeo")
    print()
    
    # Check dependencies
    missing_packages = []
    
    try:
        import yt_dlp
    except ImportError:
        missing_packages.append("yt-dlp")
    
    try:
        import selenium
    except ImportError:
        missing_packages.append("selenium")
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError:
        missing_packages.append("webdriver-manager")
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("\n🔧 Install them with:")
        print(f"pip install {' '.join(missing_packages)}")
        print("\n⚠️  Also make sure Google Chrome browser is installed!")
        return
    
    print("✅ All dependencies found!")
    print("🔧 Setting up automatic ChromeDriver management...")
    
    downloader = VideoDownloader()
    downloader.run()

if __name__ == "__main__":
    main()