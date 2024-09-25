from flask import Flask, request, send_from_directory, render_template, redirect, url_for, flash, send_file
import os
import mimetypes

app = Flask(__name__)
app.secret_key = 'ishanihar'
NAS_DIR = '/home/ishanurgaonkar/nas'  # Ensure this path exists and Flask has access to it.

# Ensure the NAS directory exists
if not os.path.exists(NAS_DIR):
    os.makedirs(NAS_DIR)

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10GB file size limit

# Files to exclude from the listing (hidden files, system files)
excluded_files = ['.DS_Store', 'Thumbs.db', '$RECYCLE.BIN', 'System Volume Information']

def get_filtered_files(path):
    try:
        # List files and folders
        files = os.listdir(path)
        # Filter out hidden/system files and any files starting with a dot (.)
        return [f for f in files if not f.startswith('.') and f not in excluded_files]
    except Exception as e:
        flash(f"Error accessing directory: {str(e)}", 'danger')
        return []

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    full_path = os.path.join(NAS_DIR, path)
    
    if not os.path.exists(full_path):
        flash(f"Directory '{path}' does not exist.", 'danger')
        return redirect(url_for('index'))
    
    # Check if the current path is a directory
    if os.path.isdir(full_path):
        files = get_filtered_files(full_path)
        return render_template('index.html', files=files, current_path=path)
    else:
        # If it's a file, treat it as a download
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
    
    # Save the file securely
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
        
        # Guess MIME type based on file extension
        mime_type, _ = mimetypes.guess_type(file_path)
        
        if mime_type:
            # Handle media types (PDF, video, and audio)
            if mime_type.startswith('video/') or mime_type.startswith('audio/') or mime_type == 'application/pdf':
                return render_template('view_media.html', filename=filename, mime_type=mime_type)
            else:
                # Serve other viewable files (images, etc.)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
