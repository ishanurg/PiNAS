from flask import Flask, request, send_from_directory, render_template, redirect, url_for, flash, send_file, jsonify
from ping3 import ping, errors
import os
import mimetypes
import requests
import logging
import subprocess
import socket
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)
app.secret_key = 'ishanihar'

# Path to NAS Directory
NAS_DIR = '/home/ishanurgaonkar/nas'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10GB file size limit

# Excluded files from listing
excluded_files = ['.DS_Store', 'Thumbs.db', '$RECYCLE.BIN', 'System Volume Information']

# Create NAS directory if not exists
if not os.path.exists(NAS_DIR):
    os.makedirs(NAS_DIR)

def get_filtered_files(path):
    try:
        files = os.listdir(path)
        return [f for f in files if not f.startswith('.') and f not in excluded_files]
    except Exception as e:
        flash(f"Error accessing directory: {str(e)}", 'danger')
        return []

# Enable logging
logging.basicConfig(level=logging.DEBUG)

# NAS Routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    full_path = os.path.join(NAS_DIR, path)
    
    if not os.path.exists(full_path):
        flash(f"Directory '{path}' does not exist.", 'danger')
        return redirect(url_for('index'))

    if os.path.isdir(full_path):
        files = get_filtered_files(full_path)
        return render_template('index.html', files=files, current_path=path)
    else:
        return send_from_directory(NAS_DIR, path, as_attachment=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    current_path = request.form.get('current_path', '')

    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    
    try:
        save_path = os.path.join(NAS_DIR, current_path)
        file.save(os.path.join(save_path, file.filename))
        flash(f"File '{file.filename}' uploaded successfully!", 'success')
    except Exception as e:
        flash(f"Error uploading file: {str(e)}", 'danger')
    
    return redirect(url_for('index', path=current_path))

@app.route('/download/<path:filename>')
def download_file(filename):
    try:
        return send_from_directory(NAS_DIR, filename, as_attachment=True)
    except Exception as e:
        flash(f"Error downloading file: {str(e)}", 'danger')
        return redirect(url_for('index'))

@app.route('/view/<path:filename>')
def view_file(filename):
    try:
        file_path = os.path.join(NAS_DIR, filename)
        mime_type, _ = mimetypes.guess_type(file_path)

        if mime_type:
            if mime_type.startswith('video/') or mime_type.startswith('audio/'):
                return render_template('view_media.html', filename=filename, mime_type=mime_type)
            elif mime_type == 'text/plain':
                with open(file_path, 'r') as file:
                    file_content = file.read()
                return render_template('view_media.html', filename=filename, mime_type=mime_type, file_content=file_content)
            else:
                return send_file(file_path, mimetype=mime_type)
        else:
            flash(f"File '{filename}' cannot be viewed.", 'danger')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f"Error viewing file: {str(e)}", 'danger')
        return redirect(url_for('index'))

@app.route('/delete/<path:filename>', methods=['POST'])
def delete_file(filename):
    try:
        os.remove(os.path.join(NAS_DIR, filename))
        flash(f"File '{filename}' deleted successfully.", 'success')
    except Exception as e:
        flash(f"Error deleting file: {str(e)}", 'danger')
    return redirect(url_for('index'))

# Network Analyzer Routes
@app.route('/network')
def network_analyzer():
    return render_template('network_analyzer.html')

@app.route('/ping_test', methods=['POST'])
def ping_test():
    ip_or_url = request.form.get('ip_or_url')
    try:
        response_time = ping(ip_or_url, timeout=5)
        if response_time is None:
            return jsonify({'status': 'unreachable', 'response_time': None})
        else:
            return jsonify({'status': 'reachable', 'response_time': f'{response_time:.2f} ms'})
    except errors.PingError:
        return jsonify({'status': 'error', 'message': 'Ping Error occurred.'})

@app.route('/dns_lookup', methods=['POST'])
def dns_lookup():
    domain = request.form.get('domain')
    try:
        ip_address = socket.gethostbyname(domain)
        return jsonify({'status': 'success', 'ip_address': ip_address})
    except socket.gaierror:
        return jsonify({'status': 'error', 'message': 'Invalid domain or DNS resolution failed.'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
