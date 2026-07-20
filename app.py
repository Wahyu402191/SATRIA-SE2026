from flask import Flask, render_template, request, jsonify, send_file, session, Response, redirect, url_for, flash
from flask_session import Session
from jinja2 import ChoiceLoader, FileSystemLoader
from youtube_scraper import YouTubeScraper
from sentiment_analyzer import SentimentAnalyzer
from data_storage import DataStorage
from media_massa_analyzer import MediaMassaAnalyzer
from media_massa_storage import MediaMassaStorage
from se_news_storage import SeNewsStorage
from se_news_analyzer import SeNewsAnalyzer
from auth_storage import AuthStorage
import os
from dotenv import load_dotenv
import pandas as pd
from io import BytesIO
import json
import base64
import time
from queue import Queue
import threading
from datetime import datetime, date
from zoneinfo import ZoneInfo
import hashlib

try:
    from livereload import Server
except ImportError:
    Server = None

load_dotenv()

app = Flask(__name__)

# Support multiple template folders
base_dir = os.path.dirname(os.path.abspath(__file__))
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(base_dir, 'templates')),
    FileSystemLoader(os.path.join(base_dir, 'templates_media_massa')),
    FileSystemLoader(os.path.join(base_dir, 'templates_news')),
])
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here-change-this-in-production')
# Server-side sessions: the default Flask session lives entirely in a signed
# browser cookie (~4KB limit), which a base64 profile photo would blow past
# instantly. SESSION_TYPE alone is a no-op without Flask-Session installed
# and initialized — Session(app) below is what actually makes it apply.
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(base_dir, 'flask_session')
app.config['SESSION_PERMANENT'] = False
Session(app)

# Hoisted to module level (not just inside `if __name__ == '__main__':`) so it's
# available under gunicorn too, which never executes that block.
debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'

# YouTube components
API_KEY = os.getenv('YOUTUBE_API_KEY', '').strip()
if not API_KEY or API_KEY == 'your_api_key_here':
    print("[WARNING] YOUTUBE_API_KEY belum dikonfigurasi di file .env")
    print("[WARNING] Scraping tidak akan berfungsi tanpa API Key yang valid.")
scraper = YouTubeScraper(API_KEY)
analyzer = SentimentAnalyzer()
storage = DataStorage()

# Media Massa components
media_analyzer = MediaMassaAnalyzer()
media_storage = MediaMassaStorage()

# Berita SE2026 components (auto-discovery via Google News RSS)
se_news_storage = SeNewsStorage()
se_news_analyzer = SeNewsAnalyzer()

# Auth (user accounts)
auth_storage = AuthStorage()

# Jinja2 template filter untuk MD5 (untuk Gravatar)
@app.template_filter('md5')
def md5_filter(s):
    """Generate MD5 hash for Gravatar"""
    return hashlib.md5(s.lower().encode('utf-8')).hexdigest()

# Jinja2 template filter untuk avatar color berdasarkan karakter pertama email
@app.template_filter('avatar_color')
def avatar_color_filter(email):
    """Generate consistent color for avatar based on first character of email"""
    if not email:
        return '#2874A6'  # default blue
    
    first_char = email[0].upper()
    
    # Color palette - 36 colors untuk 0-9 dan A-Z
    colors = [
        '#E74C3C', '#E67E22', '#F39C12', '#F1C40F', '#27AE60',  # 0-4
        '#16A085', '#2ECC71', '#3498DB', '#2874A6', '#5DADE2',  # 5-9
        '#9B59B6', '#8E44AD', '#34495E', '#2C3E50', '#E91E63',  # A-E
        '#FF5722', '#FF9800', '#FFC107', '#FFEB3B', '#CDDC39',  # F-J
        '#8BC34A', '#4CAF50', '#009688', '#00BCD4', '#03A9F4',  # K-O
        '#2196F3', '#3F51B5', '#673AB7', '#9C27B0', '#E91E63',  # P-T
        '#F44336', '#FF5252', '#FF4081', '#E040FB', '#7C4DFF',  # U-Y
        '#536DFE'  # Z
    ]
    
    # Map character to index
    if first_char.isdigit():
        idx = int(first_char)
    elif first_char.isalpha():
        idx = ord(first_char) - ord('A') + 10
    else:
        idx = 8  # default
    
    return colors[idx % len(colors)]

# Store data in memory (in production, use database)
app_data = {
    'scraped_data': None,
    'analysis_results': None
}

# Media massa data
media_data = {
    'analysis_results': None,
    'selected_month': None
}

# Progress tracking
progress_data = {
    'current': 0,
    'total': 0,
    'status': 'idle',
    'message': ''
}

# ═══════════════════════════════════════════════════════════════════════════
# LANDING & SELECTION ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/')
def landing():
    """Landing page - Dashboard awal aplikasi"""
    return render_template('landing.html')

@app.route('/selection')
def selection():
    """Selection page - Pilihan aplikasi"""
    return render_template('selection.html')

# ═══════════════════════════════════════════════════════════════════════════
# AUTH ROUTES — login/register/logout/profile
# ═══════════════════════════════════════════════════════════════════════════

# Endpoints reachable without being logged in. Everything else is gated by
# require_login() below (the landing page stays public on purpose — it's
# just branding/marketing; "masuk aplikasi" is what actually needs a login).
_PUBLIC_ENDPOINTS = {'landing', 'login', 'do_login', 'register', 'do_register', 'logout', 'static'}


@app.before_request
def require_login():
    if request.endpoint is None or request.endpoint in _PUBLIC_ENDPOINTS:
        return
    if 'user_id' not in session:
        return redirect(url_for('login', next=request.path))


@app.route('/login', methods=['GET'])
def login():
    if 'user_id' in session:
        return redirect(url_for('selection'))
    return render_template('login.html', next=request.args.get('next', ''))


@app.route('/login', methods=['POST'])
def do_login():
    email = (request.form.get('email') or '').strip()
    password = request.form.get('password') or ''
    next_url = request.form.get('next') or url_for('selection')

    user = auth_storage.get_by_email(email) if email else None
    if not user or not auth_storage.verify_password(user, password):
        flash('Email atau kata sandi salah.', 'error')
        return render_template('login.html', next=next_url, prefill_email=email), 401

    session['user_id'] = user['id']
    session['user_name'] = user['name']
    session['user_email'] = user['email']
    session['user_photo'] = user.get('profile_photo')
    auth_storage.touch_last_login(user['id'])

    if not next_url.startswith('/'):
        next_url = url_for('selection')
    return redirect(next_url)


@app.route('/register', methods=['GET'])
def register():
    if 'user_id' in session:
        return redirect(url_for('selection'))
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def do_register():
    name = (request.form.get('name') or '').strip()
    email = (request.form.get('email') or '').strip()
    instansi = (request.form.get('instansi') or '').strip()
    password = request.form.get('password') or ''
    password_confirm = request.form.get('password_confirm') or ''

    form_back = {'name': name, 'email': email, 'instansi': instansi}

    if not name or not email or not password:
        flash('Nama, email, dan kata sandi wajib diisi.', 'error')
        return render_template('register.html', **form_back), 400
    if len(password) < 6:
        flash('Kata sandi minimal 6 karakter.', 'error')
        return render_template('register.html', **form_back), 400
    if password != password_confirm:
        flash('Konfirmasi kata sandi tidak cocok.', 'error')
        return render_template('register.html', **form_back), 400
    if auth_storage.get_by_email(email):
        flash('Email ini sudah terdaftar. Silakan masuk.', 'error')
        return render_template('register.html', **form_back), 400

    user = auth_storage.create_user(name, email, password, instansi)
    session['user_id'] = user['id']
    session['user_name'] = user['name']
    session['user_email'] = user['email']
    session['user_photo'] = user.get('profile_photo')
    auth_storage.touch_last_login(user['id'])
    return redirect(url_for('selection'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/profile', methods=['GET'])
def profile():
    user = auth_storage.get_by_id(session['user_id'])
    return render_template('profile.html', user=user)


@app.route('/profile', methods=['POST'])
def update_profile():
    name = (request.form.get('name') or '').strip()
    instansi = (request.form.get('instansi') or '').strip()
    if not name:
        flash('Nama tidak boleh kosong.', 'error')
        return redirect(url_for('profile'))

    auth_storage.update_profile(session['user_id'], name, instansi)
    session['user_name'] = name

    new_password = request.form.get('new_password') or ''
    if new_password:
        if len(new_password) < 6:
            flash('Kata sandi baru minimal 6 karakter.', 'error')
            return redirect(url_for('profile'))
        auth_storage.update_password(session['user_id'], new_password)
        flash('Profil dan kata sandi berhasil diperbarui.', 'success')
    else:
        flash('Profil berhasil diperbarui.', 'success')

    return redirect(url_for('profile'))


@app.route('/profile/upload-photo', methods=['POST'])
def upload_profile_photo():
    """Upload profile photo"""
    try:
        data = request.get_json()
        photo_base64 = data.get('photo')
        
        if not photo_base64:
            return jsonify({'success': False, 'message': 'Tidak ada foto yang diunggah'}), 400
        
        # Validate base64 image
        if not photo_base64.startswith('data:image/'):
            return jsonify({'success': False, 'message': 'Format foto tidak valid'}), 400

        # Safety net behind the client-side resize — a raw/unresized photo
        # can still be multi-MB, which is wasteful to store and re-send on
        # every page load (it rides along in the session file + navbar).
        if len(photo_base64) > 2_000_000:
            return jsonify({'success': False, 'message': 'Ukuran foto terlalu besar (maks ~1.5MB)'}), 400

        # Update database
        auth_storage.update_profile_photo(session['user_id'], photo_base64)
        
        # Update session
        session['user_photo'] = photo_base64
        
        return jsonify({'success': True, 'message': 'Foto profil berhasil diperbarui'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/profile/remove-photo', methods=['POST'])
def remove_profile_photo():
    """Remove profile photo"""
    try:
        auth_storage.update_profile_photo(session['user_id'], None)
        session.pop('user_photo', None)
        return jsonify({'success': True, 'message': 'Foto profil berhasil dihapus'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ═══════════════════════════════════════════════════════════════════════════
# YOUTUBE DASHBOARD ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/youtube/')
def youtube_index():
    """YouTube dashboard - Beranda"""
    return render_template('index.html')

@app.route('/youtube/analysis')
def youtube_analysis():
    """YouTube dashboard - Analisis"""
    return render_template('analysis.html')

@app.route('/youtube/comments')
def youtube_comments():
    """YouTube dashboard - Komentar"""
    return render_template('comments.html')

@app.route('/youtube/comparison')
def youtube_comparison():
    """YouTube dashboard - Perbandingan"""
    return render_template('comparison.html')

@app.route('/youtube/about')
def youtube_about():
    """YouTube dashboard - Tentang"""
    return render_template('about.html')

@app.route('/youtube/trend')
def youtube_trend():
    """YouTube dashboard - Trend"""
    return render_template('trend.html')

@app.route('/youtube/scrape', methods=['POST'])
def scrape_comments():
    try:
        # Check API key first
        if not API_KEY or API_KEY == 'your_api_key_here':
            return jsonify({'error': 'YouTube API Key belum dikonfigurasi. Buka file .env dan isi YOUTUBE_API_KEY dengan API Key yang valid dari Google Cloud Console (https://console.cloud.google.com).'}), 400

        data = request.get_json()
        video_url = data.get('video_url', '').strip()
        max_comments = int(data.get('max_comments', 100))
        include_replies = data.get('include_replies', False)
        
        # Limit to 100000
        max_comments = min(max_comments, 100000)
        
        if not video_url:
            return jsonify({'error': 'URL video tidak boleh kosong'}), 400
        
        # Extract video ID
        video_id = scraper.extract_video_id(video_url)
        if not video_id:
            return jsonify({'error': 'URL video tidak valid'}), 400
        
        # Get video info
        video_info = scraper.get_video_info(video_id)
        
        # Check available comments in video
        available_comments = int(video_info.get('comments', 0)) if video_info else 0
        
        # Reset progress
        progress_data['current'] = 0
        progress_data['total'] = max_comments
        progress_data['status'] = 'scraping'
        progress_data['message'] = 'Memulai scraping...'
        progress_data['available'] = available_comments
        
        # Progress callback
        def update_progress(current, total):
            progress_data['current'] = current
            progress_data['total'] = total
            progress_data['available'] = available_comments
            progress_data['message'] = f'Mengambil komentar {current}/{total}...'
        
        # Scrape comments (with or without replies)
        comments_data = scraper.get_comments(
            video_id, 
            max_results=max_comments, 
            include_replies=include_replies,
            progress_callback=update_progress
        )
        
        if not comments_data:
            progress_data['status'] = 'error'
            progress_data['message'] = 'Tidak ada komentar ditemukan'
            return jsonify({'error': 'Tidak ada komentar ditemukan'}), 404
        
        # Check if we got less than requested
        got_less = len(comments_data) < max_comments
        warning_message = None
        if got_less and available_comments > 0:
            warning_message = f'Video ini hanya memiliki {len(comments_data)} komentar dari {max_comments} yang diminta. Semua komentar yang tersedia sudah diambil.'
        
        # Save to database (and backup JSON)
        filename = storage.save_comments(
            video_id, 
            video_info, 
            comments_data,
            video_url=video_url,
            include_replies=include_replies,
            requested_comments=max_comments
        )
        
        # Store in app_data
        app_data['scraped_data'] = {
            'video_id': video_id,
            'video_url': video_url,
            'video_info': video_info,
            'comments': comments_data,
            'total_comments': len(comments_data),
            'saved_filename': filename,
            'include_replies': include_replies,
            'requested_comments': max_comments,
            'available_comments': available_comments
        }
        app_data['analysis_results'] = None  # Reset analysis
        
        # Update progress
        progress_data['status'] = 'completed'
        progress_data['current'] = len(comments_data)
        progress_data['message'] = f'Selesai! {len(comments_data)} komentar berhasil diambil'
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'video_info': video_info,
            'total_comments': len(comments_data),
            'requested_comments': max_comments,
            'available_comments': available_comments,
            'comments': comments_data,
            'saved_filename': filename,
            'include_replies': include_replies,
            'warning': warning_message
        })
        
    except Exception as e:
        progress_data['status'] = 'error'
        progress_data['message'] = f'Error: {str(e)}'
        return jsonify({'error': str(e)}), 500

@app.route('/youtube/progress')
def youtube_get_progress():
    """Endpoint to get scraping progress"""
    return jsonify(progress_data)

@app.route('/youtube/analyze', methods=['POST'])
def analyze():
    try:
        # Get comments from request or app_data
        request_data = request.json or {}
        comments = request_data.get('comments')
        
        # If no comments in request, try to get from scraped_data
        if not comments:
            if 'scraped_data' in app_data and app_data['scraped_data']:
                comments = app_data['scraped_data'].get('comments')
        
        if not comments:
            return jsonify({'error': 'Tidak ada komentar untuk dianalisis'}), 400
        
        # Get selected methods (updated with new ML methods)
        selected_methods = request_data.get('methods', ['naive_bayes', 'svm', 'lstm', 'indobert'])
        
        # Analyze sentiment (FAST - no wordcloud yet)
        results = analyzer.analyze_multiple_methods(comments, selected_methods)
        
        # Save analysis results to database
        if 'scraped_data' in app_data and app_data['scraped_data']:
            video_id = app_data['scraped_data'].get('video_id')
            if video_id:
                storage.save_analysis_results(video_id, results.get('comments', []), selected_methods)
        
        # Generate confusion matrix images if multiple methods
        confusion_matrix_images = {}
        if len(selected_methods) > 1 and 'confusion_matrices' in results:
            confusion_matrix_images = analyzer.generate_confusion_matrix_images(results['confusion_matrices'])
        
        # Store results (wordcloud will be generated on demand)
        app_data['analysis_results'] = results
        app_data['wordclouds'] = None  # Lazy loading
        app_data['confusion_matrix_images'] = confusion_matrix_images
        
        response = {
            'success': True,
            'summary': results['summary'],
            'preprocessing_examples': results.get('preprocessing_examples', [])
        }
        
        # Add accuracy if available
        if 'accuracy' in results:
            response['accuracy'] = results['accuracy']
        
        # Add confusion matrices if available
        if confusion_matrix_images:
            response['confusion_matrices'] = confusion_matrix_images
        
        return jsonify(response)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/youtube/generate_wordcloud', methods=['POST'])
def generate_wordcloud():
    """Generate wordcloud on demand (lazy loading)"""
    try:
        if 'analysis_results' not in app_data or not app_data['analysis_results']:
            return jsonify({'error': 'Belum ada hasil analisis'}), 400
        
        # Generate wordcloud only when requested
        if app_data.get('wordclouds') is None:
            results = app_data['analysis_results']
            wordclouds = analyzer.generate_wordcloud(results['comments'])
            app_data['wordclouds'] = wordclouds
        
        wordclouds = app_data['wordclouds']
        
        return jsonify({
            'success': True,
            'wordcloud_positive': wordclouds.get('positive'),
            'wordcloud_negative': wordclouds.get('negative'),
            'positive_count': wordclouds.get('positive_count', 0),
            'negative_count': wordclouds.get('negative_count', 0)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/youtube/saved_files', methods=['GET'])
def get_saved_files():
    try:
        files = storage.get_saved_files()
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        print(f"Error getting saved files: {e}")
        return jsonify({'success': True, 'files': []})

@app.route('/youtube/load_file/<filename>', methods=['GET'])
def load_file(filename):
    data = storage.load_comments(filename)
    if data:
        # Store in app_data
        app_data['scraped_data'] = {
            'video_id': data['video_id'],
            'video_info': data['video_info'],
            'comments': data['comments'],
            'total_comments': data['total_comments'],
            'saved_filename': filename
        }
        return jsonify({'success': True, 'data': data})
    return jsonify({'success': False, 'error': 'File tidak ditemukan'}), 404

@app.route('/youtube/delete_file/<filename>', methods=['DELETE'])
def delete_file(filename):
    if storage.delete_file(filename):
        return jsonify({'success': True, 'message': 'File berhasil dihapus'})
    return jsonify({'success': False, 'error': 'File tidak ditemukan'}), 404

@app.route('/youtube/get_scraped_data', methods=['GET'])
def get_scraped_data():
    if app_data['scraped_data']:
        return jsonify({
            'success': True,
            'data': app_data['scraped_data']
        })
    return jsonify({'success': False, 'error': 'Belum ada data scraping'}), 404

@app.route('/youtube/get_analysis_results', methods=['GET'])
def get_analysis_results():
    if app_data['analysis_results']:
        return jsonify({
            'success': True,
            'results': app_data['analysis_results'],
            'video_info': app_data['scraped_data']['video_info'] if app_data['scraped_data'] else None
        })
    return jsonify({'success': False, 'error': 'Belum ada hasil analisis'}), 404

@app.route('/youtube/export', methods=['GET'])
def export_data():
    try:
        if not app_data.get('analysis_results'):
            return jsonify({'error': 'Tidak ada data untuk di-export. Lakukan analisis terlebih dahulu.'}), 400

        results  = app_data['analysis_results']
        scraped  = app_data.get('scraped_data') or {}
        video_info = scraped.get('video_info')

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:

            # ── Sheet 1: Info Video ──────────────────────────────────────
            if video_info:
                df_info = pd.DataFrame([{
                    'Video ID'      : scraped.get('video_id', ''),
                    'Judul Video'   : video_info.get('title', ''),
                    'Channel'       : video_info.get('channel', ''),
                    'Views'         : video_info.get('views', 0),
                    'Likes'         : video_info.get('likes', 0),
                    'Total Komentar': video_info.get('comments', 0),
                }])
                df_info.to_excel(writer, sheet_name='Info Video', index=False)

            # ── Sheet 2: Komentar + Sentimen ─────────────────────────────
            comments_raw = results.get('comments', [])
            if comments_raw:
                df_comments = pd.DataFrame(comments_raw)
                # Reorder columns: teks dulu, lalu sentimen
                prio = ['author', 'text', 'likes',
                        'naive_bayes_sentiment', 'naive_bayes_score',
                        'svm_sentiment',         'svm_score',
                        'lstm_sentiment',        'lstm_score',
                        'indobert_sentiment',    'indobert_score']
                cols = [c for c in prio if c in df_comments.columns] + \
                       [c for c in df_comments.columns if c not in prio]
                df_comments = df_comments[cols]
                df_comments.to_excel(writer, sheet_name='Komentar & Sentimen', index=False)

            # ── Sheet 3: Ringkasan per Metode ────────────────────────────
            summary_rows = []
            for method, stats in results.get('summary', {}).items():
                pos   = int(stats.get('positive', 0))
                neg   = int(stats.get('negative', 0))
                neu   = int(stats.get('neutral',  0))
                total = pos + neg + neu
                if total == 0:
                    continue
                summary_rows.append({
                    'Metode'              : method,
                    'Positif'             : pos,
                    'Negatif'             : neg,
                    'Netral'              : neu,
                    'Total'               : total,
                    'Pct Positif (%)'     : round(pos / total * 100, 2),
                    'Pct Negatif (%)'     : round(neg / total * 100, 2),
                    'Pct Netral (%)'      : round(neu / total * 100, 2),
                })
            if summary_rows:
                df_summary = pd.DataFrame(summary_rows)
                df_summary.to_excel(writer, sheet_name='Ringkasan Metode', index=False)

            # ── Sheet 4: Agreement Rate ──────────────────────────────────
            accuracy = results.get('accuracy')
            if accuracy:
                acc_rows = [{'Metode': m.replace('_',' ').title(),
                             'Agreement Rate (%)': v}
                            for m, v in accuracy.items()]
                pd.DataFrame(acc_rows).to_excel(writer, sheet_name='Agreement Rate', index=False)

        output.seek(0)
        video_id = scraped.get('video_id', 'export')
        filename = f'SATRIA_SE2026_{video_id}.xlsx'

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Export gagal: {str(e)}'}), 500

@app.route('/youtube/export_pdf', methods=['GET'])
def export_pdf():
    """Generate PDF laporan analisis sentimen"""
    try:
        if not app_data.get('analysis_results'):
            return jsonify({'error': 'Belum ada hasil analisis.'}), 400

        results  = app_data['analysis_results']
        scraped  = app_data.get('scraped_data') or {}
        video_info = scraped.get('video_info') or {}

        # Build HTML for PDF
        from datetime import datetime
        now = datetime.now().strftime('%d %B %Y, %H:%M')
        title = video_info.get('title', 'Tidak diketahui')
        channel = video_info.get('channel', '-')
        total = len(results.get('comments', []))

        summary = results.get('summary', {})
        accuracy = results.get('accuracy', {})

        # Summary table rows
        summary_rows = ''
        for method, stats in summary.items():
            t = stats['positive'] + stats['negative'] + stats['neutral']
            if t == 0:
                continue
            pp = round(stats['positive']/t*100, 1)
            np_ = round(stats['negative']/t*100, 1)
            ep = round(stats['neutral']/t*100, 1)
            acc = accuracy.get(method.lower().replace(' ','_'), '-')
            acc_str = f"{acc}%" if isinstance(acc, (int,float)) else '-'
            summary_rows += f"""
            <tr>
                <td>{method}</td>
                <td class="num">{stats['positive']} ({pp}%)</td>
                <td class="num">{stats['negative']} ({np_}%)</td>
                <td class="num">{stats['neutral']} ({ep}%)</td>
                <td class="num">{t}</td>
                <td class="num">{acc_str}</td>
            </tr>"""

        # Top 10 comments by likes
        top_comments = sorted(results.get('comments', []), key=lambda x: int(x.get('likes',0)), reverse=True)[:10]
        comment_rows = ''
        for i, c in enumerate(top_comments, 1):
            text = str(c.get('text',''))[:120] + ('...' if len(str(c.get('text',''))) > 120 else '')
            sent = c.get('naive_bayes_sentiment') or c.get('svm_sentiment') or '-'
            color = '#2d7a4f' if 'Positif' in sent else '#9b2335' if 'Negatif' in sent else '#5a6a7a'
            comment_rows += f"""
            <tr>
                <td class="num">{i}</td>
                <td>{text}</td>
                <td style="color:{color};font-weight:600;text-align:center;">{sent}</td>
                <td class="num">{c.get('likes',0)}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: Arial, sans-serif; font-size: 12px; color: #1e2d3d; background:#fff; padding: 32px; }}
  .header {{ background: #0f2238; color:#fff; padding: 24px 28px; border-radius: 8px; margin-bottom: 24px; display:flex; justify-content:space-between; align-items:center; }}
  .header h1 {{ font-size: 20px; font-weight: 800; letter-spacing: -.3px; }}
  .header .sub {{ font-size: 11px; color: rgba(255,255,255,.6); margin-top: 4px; }}
  .header .badge {{ background: rgba(200,151,58,.15); border: 1px solid rgba(200,151,58,.4); color: #e8b96a; padding: 8px 16px; border-radius: 8px; text-align:center; }}
  .badge-year {{ font-size: 22px; font-weight: 800; display:block; }}
  .meta {{ display:grid; grid-template-columns:repeat(2,1fr); gap:12px; margin-bottom:20px; }}
  .meta-item {{ background:#f0f3f7; border-radius:6px; padding:12px 16px; }}
  .meta-label {{ font-size:10px; color:#6b7c8d; text-transform:uppercase; letter-spacing:.5px; }}
  .meta-value {{ font-size:14px; font-weight:700; color:#1a3a5c; margin-top:3px; }}
  h2 {{ font-size:14px; font-weight:700; color:#1a3a5c; margin: 20px 0 10px; padding-bottom:6px; border-bottom:2px solid #c8973a; }}
  table {{ width:100%; border-collapse:collapse; margin-bottom:20px; }}
  thead tr {{ background:#1a3a5c; color:#fff; }}
  thead th {{ padding:9px 12px; text-align:left; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; }}
  tbody tr {{ border-bottom:1px solid #dce3ea; }}
  tbody tr:nth-child(even) {{ background:#f8fafc; }}
  tbody td {{ padding:8px 12px; font-size:11px; }}
  .num {{ text-align:right; font-variant-numeric: tabular-nums; }}
  .footer {{ margin-top:32px; padding-top:14px; border-top:1px solid #dce3ea; text-align:center; color:#6b7c8d; font-size:10px; }}
</style>
</head>
<body>
<div class="header">
  <div>
    <div style="font-size:10px;color:rgba(255,255,255,.5);text-transform:uppercase;letter-spacing:2px;margin-bottom:6px;">Badan Pusat Statistik</div>
    <h1>SATRIA SE2026</h1>
    <div class="sub">Laporan Analisis Sentimen Komentar YouTube</div>
    <div class="sub" style="margin-top:4px;">Dicetak: {now}</div>
  </div>
  <div class="badge">
    <span class="badge-year">2026</span>
    <div style="font-size:9px;color:rgba(255,255,255,.4);">Sensus Ekonomi</div>
  </div>
</div>

<div class="meta">
  <div class="meta-item"><div class="meta-label">Judul Video</div><div class="meta-value" style="font-size:12px;">{title}</div></div>
  <div class="meta-item"><div class="meta-label">Channel</div><div class="meta-value">{channel}</div></div>
  <div class="meta-item"><div class="meta-label">Total Komentar Dianalisis</div><div class="meta-value">{total:,}</div></div>
  <div class="meta-item"><div class="meta-label">Video ID</div><div class="meta-value">{scraped.get('video_id','-')}</div></div>
</div>

<h2>Ringkasan Distribusi Sentimen per Metode</h2>
<table>
  <thead><tr>
    <th>Metode</th><th>Positif</th><th>Negatif</th><th>Netral</th><th>Total</th><th>Agreement</th>
  </tr></thead>
  <tbody>{summary_rows}</tbody>
</table>

<h2>10 Komentar Teratas (berdasarkan Likes)</h2>
<table>
  <thead><tr><th>#</th><th>Komentar</th><th style="text-align:center;">Sentimen (NB)</th><th>Likes</th></tr></thead>
  <tbody>{comment_rows}</tbody>
</table>

<div class="footer">
  Laporan ini digenerate otomatis oleh SATRIA SE2026 &mdash; Badan Pusat Statistik Kabupaten Bangkalan
</div>
</body></html>"""

        return Response(html, mimetype='text/html',
                        headers={'Content-Disposition': 'inline; filename=laporan_sentimen.html',
                                 'X-Print-Trigger': '1'})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/youtube/word_trend', methods=['GET'])
def word_trend():
    """API endpoint: top words per month from scraped comments"""
    try:
        if not app_data.get('scraped_data'):
            return jsonify({'error': 'Belum ada data scraping'}), 400

        comments = app_data['scraped_data'].get('comments', [])
        from collections import Counter, defaultdict
        import re

        # Stopwords sederhana
        stopwords = {'yang', 'dan', 'di', 'ke', 'dari', 'ini', 'itu', 'ada',
                     'juga', 'dengan', 'untuk', 'adalah', 'tidak', 'saya',
                     'aku', 'kamu', 'dia', 'mereka', 'kita', 'kami', 'bisa',
                     'sudah', 'akan', 'ya', 'nya', 'lah', 'pun', 'aja',
                     'deh', 'sih', 'gak', 'ga', 'bang', 'mas', 'pak'}

        monthly = defaultdict(Counter)

        for c in comments:
            published = c.get('published_at', '')
            if not published:
                continue
            try:
                ym = published[:7]  # YYYY-MM
            except Exception:
                continue

            text = str(c.get('text', '')).lower()
            text = re.sub(r'http\S+|@\w+|#\w+|\d+|[^\w\s]', ' ', text)
            words = [w for w in text.split() if len(w) > 3 and w not in stopwords]
            monthly[ym].update(words)

        if not monthly:
            return jsonify({'months': [], 'words': [], 'data': []})

        # Sort months
        months = sorted(monthly.keys())

        # Top 8 words overall
        overall = Counter()
        for cnt in monthly.values():
            overall.update(cnt)
        top_words = [w for w, _ in overall.most_common(8)]

        # Build series data
        data = {}
        for word in top_words:
            data[word] = [monthly[m].get(word, 0) for m in months]

        return jsonify({'months': months, 'words': top_words, 'data': data})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/youtube/analyze_single', methods=['POST'])
def analyze_single():
    """Analyze single comment input from user"""
    try:
        data = request.get_json()
        comment_text = data.get('comment', '').strip()
        
        if not comment_text:
            return jsonify({'error': 'Komentar tidak boleh kosong'}), 400
        
        # Preprocess
        preprocessed = analyzer.preprocessor.preprocess_simple(comment_text)
        
        # Analyze with all 4 methods
        results = {
            'original': comment_text,
            'preprocessed': preprocessed,
            'sentiments': {}
        }
        
        # Naive Bayes
        nb_sentiment, nb_score = analyzer.naive_bayes_analysis(preprocessed)
        results['sentiments']['naive_bayes'] = {
            'label': nb_sentiment,
            'score': nb_score,
            'name': 'Naive Bayes'
        }
        
        # SVM
        svm_sentiment, svm_score = analyzer.svm_analysis(preprocessed)
        results['sentiments']['svm'] = {
            'label': svm_sentiment,
            'score': svm_score,
            'name': 'SVM'
        }
        
        # LSTM
        lstm_sentiment, lstm_score = analyzer.lstm_analysis(preprocessed)
        results['sentiments']['lstm'] = {
            'label': lstm_sentiment,
            'score': lstm_score,
            'name': 'LSTM'
        }
        
        # IndoBERT
        indobert_sentiment, indobert_score = analyzer.indobert_analysis(preprocessed)
        results['sentiments']['indobert'] = {
            'label': indobert_sentiment,
            'score': indobert_score,
            'name': 'IndoBERT'
        }
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/youtube/preprocess_text', methods=['POST'])
def preprocess_text():
    """Endpoint untuk mendapatkan detail preprocessing steps untuk satu text"""
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'success': False, 'error': 'Text is required'}), 400
        
        # Menggunakan text_preprocessor untuk mendapatkan detail steps
        from text_preprocessor import TextPreprocessor
        preprocessor = TextPreprocessor()
        
        # Get detailed steps
        steps = {}
        
        # Original
        steps['original'] = text
        steps['original_words'] = len(text.split())
        
        # Case folding
        case_folded = preprocessor.case_folding(text)
        steps['case_folding'] = case_folded
        
        # Noise removal (URL, mentions, hashtags, numbers)
        noise_removed = preprocessor.remove_noise(case_folded)
        steps['noise_removal'] = noise_removed
        
        # Remove numbers (already in remove_noise)
        steps['remove_numbers'] = noise_removed
        
        # Remove punctuation
        no_punct = preprocessor.remove_punctuation(noise_removed)
        steps['remove_punctuation'] = no_punct
        
        # Spelling correction (normalization)
        corrected = preprocessor.normalize_text(no_punct)
        steps['spelling_correction'] = corrected
        
        # Tokenization
        tokens = preprocessor.tokenize(corrected)
        steps['tokenization'] = tokens
        steps['token_count'] = len(tokens)
        
        # Normalization (already done above in spelling_correction)
        steps['normalization'] = tokens
        
        # Stopword removal
        no_stopwords = preprocessor.remove_stopwords(tokens)
        steps['stopword_removal'] = no_stopwords
        steps['tokens_after_stopword'] = len(no_stopwords)
        
        # Stemming
        stemmed = preprocessor.stem_text(no_stopwords)
        steps['stemming'] = stemmed
        
        # Negation handling
        negation_handled = preprocessor.handle_negation(stemmed)
        steps['negation_handling'] = negation_handled
        
        # Final result
        final = ' '.join(negation_handled) if isinstance(negation_handled, list) else negation_handled
        steps['final'] = final
        steps['final_words'] = len(negation_handled) if isinstance(negation_handled, list) else len(final.split())
        
        # Calculate reduction rate
        if steps['original_words'] > 0:
            reduction = ((steps['original_words'] - steps['final_words']) / steps['original_words']) * 100
            steps['reduction_rate'] = round(reduction, 1)
        else:
            steps['reduction_rate'] = 0
        
        return jsonify({
            'success': True,
            'steps': steps
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/youtube/get_dashboard_stats', methods=['GET'])
def youtube_get_dashboard_stats():
    """Get dashboard statistics from database"""
    try:
        from db_config import execute_query
        
        # Get total videos
        video_count = execute_query("SELECT COUNT(*) as count FROM videos", fetch=True)
        total_videos = video_count[0]['count'] if video_count else 0
        
        # Get total comments
        comment_count = execute_query("SELECT COUNT(*) as count FROM comments", fetch=True)
        total_comments = comment_count[0]['count'] if comment_count else 0
        
        # Get total analysis sessions (each analysis run increments this)
        session_count = execute_query(
            "SELECT COUNT(*) as count FROM analysis_sessions",
            fetch=True
        )
        total_analyzed = session_count[0]['count'] if session_count else 0


        # Keep total analyzed comments available for future UI use
        analyzed_comments_count = execute_query(
            "SELECT COUNT(*) as count FROM analysis_results",
            fetch=True
        )
        total_analyzed_comments = analyzed_comments_count[0]['count'] if analyzed_comments_count else 0
        
        return jsonify({
            'success': True,
            'total_videos': total_videos,
            'total_comments': total_comments,
            'total_analyzed': total_analyzed,
            'total_analyzed_comments': total_analyzed_comments
        })
        
    except Exception as e:
        # Return zeros if database not available
        return jsonify({
            'success': False,
            'total_videos': 0,
            'total_comments': 0,
            'total_analyzed': 0,
            'error': str(e)
        })

# ═══════════════════════════════════════════════════════════════════════════
# MEDIA MASSA DASHBOARD ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/media/')
def media_index():
    """Media Massa dashboard - Beranda/Analisis"""
    # Get statistics
    stats = media_storage.get_statistics()
    
    # Get available months
    available_months = media_storage.get_available_months()
    
    return render_template(
        'index_media.html',
        total_articles=stats['total_articles'],
        total_months=stats['total_months'],
        total_sources=stats['total_sources'],
        total_analyzed=stats['total_analyzed'],
        available_months=available_months
    )

@app.route('/media/comments')
def media_comments():
    """Media Massa dashboard - Data Berita"""
    return render_template('comments_media.html')

@app.route('/media/comparison')
def media_comparison():
    """Media Massa dashboard - Perbandingan"""
    return render_template('comparison_media.html')

@app.route('/media/trend')
def media_trend():
    """Media Massa dashboard - Trend"""
    return render_template('trend_media.html')

@app.route('/media/about')
def media_about():
    """Media Massa dashboard - Tentang"""
    return render_template('about_media.html')

@app.route('/media/analyze', methods=['POST'])
def media_analyze():
    """Analyze news articles for selected month"""
    try:
        data = request.get_json()
        month = data.get('month')
        methods = data.get('methods', ['naive_bayes', 'svm', 'lstm', 'indobert'])
        
        if not month:
            return jsonify({'error': 'Month parameter required'}), 400
        
        # Get articles for the month
        articles = media_storage.get_articles_by_month(month)
        
        if not articles:
            return jsonify({'error': 'Tidak ada artikel untuk bulan tersebut'}), 404
        
        # Analyze articles
        results = media_analyzer.analyze_articles(articles, methods)
        
        # Save analysis results
        media_storage.save_analysis_results(month, results['articles'], methods)
        
        # Store in media_data
        media_data['analysis_results'] = results
        media_data['selected_month'] = month
        
        return jsonify({
            'success': True,
            'summary': results['summary'],
            'total_articles': len(articles),
            'preprocessing_examples': results.get('preprocessing_examples', []),
            'accuracy': results.get('accuracy', {}),
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/media/get_analysis_results', methods=['GET'])
def media_get_analysis_results():
    """Get stored analysis results"""
    if media_data['analysis_results']:
        return jsonify({
            'success': True,
            'results': media_data['analysis_results'],
            'selected_month': media_data['selected_month']
        })
    return jsonify({'success': False, 'error': 'Belum ada hasil analisis'}), 404

@app.route('/media/word_trend', methods=['GET'])
def media_word_trend():
    """API endpoint: top words per week from analyzed articles"""
    try:
        if not media_data.get('analysis_results'):
            return jsonify({'error': 'Belum ada data analisis'}), 400
        
        articles = media_data['analysis_results'].get('articles', [])
        month_value = media_data.get('selected_month', '')
        
        trend_data = media_analyzer.generate_word_trend_weekly(articles, month_value)
        
        return jsonify(trend_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/media/generate_wordcloud', methods=['POST'])
def media_generate_wordcloud():
    """Generate wordcloud for analyzed articles"""
    try:
        if not media_data.get('analysis_results'):
            return jsonify({'error': 'Belum ada hasil analisis'}), 400
        
        # Generate wordcloud
        results = media_data['analysis_results']
        wordclouds = media_analyzer.generate_wordcloud(results['articles'])
        
        return jsonify({
            'success': True,
            'wordcloud_positive': wordclouds.get('positive'),
            'wordcloud_negative': wordclouds.get('negative'),
            'positive_count': wordclouds.get('positive_count', 0),
            'negative_count': wordclouds.get('negative_count', 0)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/media/export', methods=['GET'])
def media_export():
    """Export analysis results to Excel"""
    try:
        if not media_data.get('analysis_results'):
            return jsonify({'error': 'Tidak ada data untuk di-export'}), 400
        
        results = media_data['analysis_results']
        selected_month = media_data.get('selected_month', 'export')
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1: Summary per Method
            summary_rows = []
            for method, stats in results.get('summary', {}).items():
                pos = int(stats.get('positive', 0))
                neg = int(stats.get('negative', 0))
                neu = int(stats.get('neutral', 0))
                total = pos + neg + neu
                if total == 0:
                    continue
                summary_rows.append({
                    'Metode': method,
                    'Positif': pos,
                    'Negatif': neg,
                    'Netral': neu,
                    'Total': total,
                    'Pct Positif (%)': round(pos / total * 100, 2),
                    'Pct Negatif (%)': round(neg / total * 100, 2),
                    'Pct Netral (%)': round(neu / total * 100, 2),
                })
            if summary_rows:
                df_summary = pd.DataFrame(summary_rows)
                df_summary.to_excel(writer, sheet_name='Ringkasan Metode', index=False)
            
            # Sheet 2: Articles + Sentiments
            articles_raw = results.get('articles', [])
            if articles_raw:
                df_articles = pd.DataFrame(articles_raw)
                # Reorder columns
                prio = ['title', 'source', 'published_date',
                        'naive_bayes_sentiment', 'naive_bayes_score',
                        'svm_sentiment', 'svm_score',
                        'lstm_sentiment', 'lstm_score',
                        'indobert_sentiment', 'indobert_score']
                cols = [c for c in prio if c in df_articles.columns] + \
                       [c for c in df_articles.columns if c not in prio]
                df_articles = df_articles[cols]
                df_articles.to_excel(writer, sheet_name='Berita & Sentimen', index=False)
            
            # Sheet 3: Agreement Rate
            accuracy = results.get('accuracy')
            if accuracy:
                acc_rows = [{'Metode': m.replace('_', ' ').title(),
                             'Agreement Rate (%)': v}
                            for m, v in accuracy.items()]
                pd.DataFrame(acc_rows).to_excel(writer, sheet_name='Agreement Rate', index=False)
        
        output.seek(0)
        filename = f'SATRIA_SE2026_MediaMassa_{selected_month}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Export gagal: {str(e)}'}), 500

@app.route('/get_dashboard_stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics from database"""
    try:
        from db_config import execute_query
        
        # Get total videos
        video_count = execute_query("SELECT COUNT(*) as count FROM videos", fetch=True)
        total_videos = video_count[0]['count'] if video_count else 0
        
        # Get total comments
        comment_count = execute_query("SELECT COUNT(*) as count FROM comments", fetch=True)
        total_comments = comment_count[0]['count'] if comment_count else 0
        
        # Get total analysis sessions (each analysis run increments this)
        session_count = execute_query(
            "SELECT COUNT(*) as count FROM analysis_sessions",
            fetch=True
        )
        total_analyzed = session_count[0]['count'] if session_count else 0

        # Keep total analyzed comments available for future UI use
        analyzed_comments_count = execute_query(
            "SELECT COUNT(*) as count FROM analysis_results",
            fetch=True
        )
        total_analyzed_comments = analyzed_comments_count[0]['count'] if analyzed_comments_count else 0
        
        return jsonify({
            'success': True,
            'total_videos': total_videos,
            'total_comments': total_comments,
            'total_analyzed': total_analyzed,
            'total_analyzed_comments': total_analyzed_comments
        })
        
    except Exception as e:
        # Return zeros if database not available
        return jsonify({
            'success': False,
            'total_videos': 0,
            'total_comments': 0,
            'total_analyzed': 0,
            'error': str(e)
        })

# ═══════════════════════════════════════════════════════════════════════════
# BERITA SENSUS EKONOMI 2026 — NEWS MONITORING ROUTES
# ═══════════════════════════════════════════════════════════════════════════

news_refresh_state = {'running': False}


@app.route('/news/')
def news_index():
    """Berita SE2026 — Beranda: ringkasan statistik, status fetch, berita terbaru"""
    stats = se_news_storage.get_statistics()
    latest = se_news_storage.get_articles(limit=8)
    last_log = se_news_storage.get_latest_fetch_log()
    return render_template(
        'index_news.html',
        stats=stats,
        latest_articles=latest,
        last_log=last_log,
        fetch_interval_hours=int(os.getenv('SE_NEWS_FETCH_INTERVAL_HOURS', 3)),
    )


@app.route('/news/articles')
def news_articles_page():
    """Berita SE2026 — Data Berita: filter per tanggal/sumber/sentimen/pencarian"""
    return render_template('articles_news.html', sources=se_news_storage.get_available_sources())


@app.route('/news/analysis')
def news_analysis_page():
    """Berita SE2026 — Analisis Sentimen"""
    return render_template('analysis_news.html')


@app.route('/news/daily')
def news_daily_page():
    """Berita SE2026 — Statistik Harian: pilih bulan, lihat jumlah berita per hari"""
    return render_template('daily_news.html')


@app.route('/news/trend')
def news_trend_page():
    """Berita SE2026 — Trend & Insight: sentimen dari waktu ke waktu, sumber, kalender heatmap"""
    return render_template('trend_news.html')


@app.route('/news/about')
def news_about_page():
    """Berita SE2026 — Tentang"""
    return render_template('about_news.html')


@app.route('/news/refresh', methods=['POST'])
def news_refresh():
    """Trigger manual fetch pipeline in a background thread; returns immediately."""
    if news_refresh_state['running']:
        return jsonify({'success': False, 'error': 'Refresh sedang berjalan, tunggu sebentar.'}), 409

    def _run():
        news_refresh_state['running'] = True
        try:
            from se_news_scheduler import run_fetch_job
            run_fetch_job(se_news_storage, se_news_analyzer, trigger_type='manual')
        finally:
            news_refresh_state['running'] = False

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({'success': True, 'message': 'Refresh dimulai di background.'})


@app.route('/news/refresh_status')
def news_refresh_status():
    """Poll the latest fetch log row to show progress/result of a refresh."""
    log = se_news_storage.get_latest_fetch_log()
    return jsonify({
        'success': True,
        'running': news_refresh_state['running'],
        'log': log,
    })


@app.route('/news/api/articles')
def news_api_articles():
    try:
        articles = se_news_storage.get_articles(
            date=request.args.get('date'),
            date_from=request.args.get('date_from'),
            date_to=request.args.get('date_to'),
            q=request.args.get('q'),
            source=request.args.get('source'),
            sentiment=request.args.get('sentiment'),
            method=request.args.get('method', 'naive_bayes'),
            limit=int(request.args.get('limit', 50)),
            offset=int(request.args.get('offset', 0)),
        )
        return jsonify({'success': True, 'articles': articles})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/news/api/article/<int:article_id>')
def news_api_article_detail(article_id):
    article = se_news_storage.get_article_by_id(article_id)
    if not article:
        return jsonify({'success': False, 'error': 'Artikel tidak ditemukan'}), 404
    article['sentence_analysis'] = se_news_analyzer.explain_sentiment(article.get('content'))
    return jsonify({'success': True, 'article': article})


@app.route('/news/api/daily_counts')
def news_api_daily_counts():
    """?month=YYYY-MM -> per-day counts for that month, zero-filled including
    future days (so a day that hasn't happened yet reads as 'belum terjadi',
    not the same as a past day with genuinely zero news)."""
    try:
        import calendar as cal
        month_param = request.args.get('month')
        if not month_param:
            return jsonify({'error': 'month parameter required (format YYYY-MM)'}), 400
        year, month = (int(x) for x in month_param.split('-'))

        rows = se_news_storage.get_daily_counts(year, month)
        counts_by_day = {}
        for r in rows:
            d = r['published_day']
            day_num = d.day if hasattr(d, 'day') else int(str(d).split('-')[2])
            counts_by_day[day_num] = r['count']

        days_in_month = cal.monthrange(year, month)[1]
        today = datetime.now(ZoneInfo('Asia/Jakarta')).date()

        days = []
        for day_num in range(1, days_in_month + 1):
            this_date = date(year, month, day_num)
            days.append({
                'day': day_num,
                'count': counts_by_day.get(day_num, 0),
                'is_future': this_date > today,
            })

        return jsonify({'success': True, 'year': year, 'month': month, 'days': days})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/news/api/calendar_counts')
def news_api_calendar_counts():
    """?year=YYYY -> day->count map for the year-long calendar heatmap."""
    try:
        year = int(request.args.get('year', datetime.now().year))
        rows = se_news_storage.get_calendar_counts(year)
        days = {str(r['published_day']): r['count'] for r in rows}
        return jsonify({'success': True, 'year': year, 'days': days})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/news/api/source_breakdown')
def news_api_source_breakdown():
    try:
        rows = se_news_storage.get_source_breakdown(
            date_from=request.args.get('date_from'),
            date_to=request.args.get('date_to'),
        )
        return jsonify({'success': True, 'sources': rows})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/news/api/sentiment_trend')
def news_api_sentiment_trend():
    try:
        date_to = request.args.get('date_to') or datetime.now(ZoneInfo('Asia/Jakarta')).strftime('%Y-%m-%d')
        date_from = request.args.get('date_from') or '2026-01-01'
        method = request.args.get('method', 'naive_bayes')
        rows = se_news_storage.get_sentiment_trend(date_from, date_to, method)

        by_day = {}
        for r in rows:
            day = str(r['published_day'])
            by_day.setdefault(day, {'Positif': 0, 'Negatif': 0, 'Netral': 0})
            by_day[day][r['sentiment']] = r['count']

        days = sorted(by_day.keys())
        return jsonify({
            'success': True,
            'days': days,
            'positive': [by_day[d].get('Positif', 0) for d in days],
            'negative': [by_day[d].get('Negatif', 0) for d in days],
            'neutral': [by_day[d].get('Netral', 0) for d in days],
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/news/api/analyze', methods=['POST'])
def news_api_analyze():
    """Re-run/refresh sentiment analysis over a date range with selected methods."""
    try:
        data = request.get_json() or {}
        date_from = data.get('date_from') or '2026-01-01'
        date_to = data.get('date_to') or datetime.now(ZoneInfo('Asia/Jakarta')).strftime('%Y-%m-%d')
        methods = data.get('methods') or ['naive_bayes', 'svm', 'lstm', 'indobert']

        articles = se_news_storage.get_articles(date_from=date_from, date_to=date_to, limit=2000)
        articles = [a for a in articles if a.get('content')]

        if not articles:
            return jsonify({'error': 'Tidak ada artikel dengan konten untuk dianalisis pada rentang ini'}), 404

        results = se_news_analyzer.analyze_batch(articles, methods)
        for row in results['articles']:
            if row.get('id'):
                se_news_storage.save_sentiment_results(row['id'], row['_method_results'])

        return jsonify({
            'success': True,
            'total_articles': len(articles),
            'summary': results['summary'],
            'accuracy': results.get('accuracy', {}),
            'preprocessing_examples': results.get('preprocessing_examples', []),
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/news/export')
def news_export():
    """Export filtered articles + sentiment to Excel."""
    try:
        date_from = request.args.get('date_from') or '2026-01-01'
        date_to = request.args.get('date_to') or datetime.now(ZoneInfo('Asia/Jakarta')).strftime('%Y-%m-%d')
        articles = se_news_storage.get_articles(date_from=date_from, date_to=date_to, limit=5000)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if articles:
                df = pd.DataFrame(articles)
                prio = ['title', 'source', 'published_date', 'url', 'content_source',
                        'naive_bayes_sentiment', 'naive_bayes_score',
                        'svm_sentiment', 'svm_score',
                        'lstm_sentiment', 'lstm_score',
                        'indobert_sentiment', 'indobert_score']
                cols = [c for c in prio if c in df.columns] + [c for c in df.columns if c not in prio]
                df[cols].to_excel(writer, sheet_name='Berita & Sentimen', index=False)
            else:
                pd.DataFrame([{'info': 'Tidak ada data pada rentang tanggal ini'}]).to_excel(
                    writer, sheet_name='Berita & Sentimen', index=False)

        output.seek(0)
        filename = f'SATRIA_SE2026_BeritaSE2026_{date_from}_{date_to}.xlsx'
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Export gagal: {str(e)}'}), 500


def _should_start_news_scheduler():
    """See se_news_scheduler.py docstring for the reasoning: the classic
    Werkzeug reloader (used only when FLASK_DEBUG=true and the optional
    `livereload` package isn't installed) forks a parent+child process, and
    only the child sets WERKZEUG_RUN_MAIN — so the scheduler must be skipped
    in the parent to avoid starting twice. The livereload branch and
    gunicorn (which never hits `__main__` at all) each run this module
    exactly once, so no such guard is needed there."""
    using_classic_werkzeug_reloader = debug and Server is None
    if using_classic_werkzeug_reloader and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        return False
    return os.getenv('SE_NEWS_SCHEDULER_ENABLED', 'true').lower() == 'true'


if _should_start_news_scheduler():
    try:
        from se_news_scheduler import init_scheduler
        init_scheduler(se_news_storage, se_news_analyzer)
    except Exception as e:
        print(f"[!] Berita SE2026 scheduler failed to start: {e}")


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    if debug and Server is not None:
        server = Server(app.wsgi_app)
        server.watch('*.py')
        server.watch('templates/*.html')
        server.watch('static/**/*')
        server.serve(host='0.0.0.0', port=port, debug=True, restart_delay=1)
    else:
        app.run(host='0.0.0.0', port=port, debug=debug)
