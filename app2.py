from flask import Flask, request, send_from_directory, render_template, redirect, url_for, flash, send_file
import os
import mimetypes
import math

app = Flask(__name__)
app.secret_key = 'ishanihar'
NAS_DIR = '/home/ishanurgaonkar/nas'  # Ensure this path exists and Flask has access to it.

# Ensure the NAS directory exists
if not os.path.exists(NAS_DIR):
    os.makedirs(NAS_DIR)

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  


@app.route('/')
def index():
    try:
        files = os.listdir(NAS_DIR)
    except Exception as e:
        files = []
        flash(f"Error accessing NAS directory: {str(e)}", 'danger')
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    
    # Save the file securely
    try:
        file_path = os.path.join(NAS_DIR, file.filename)
        file.save(file_path)
        flash(f"File '{file.filename}' uploaded successfully!", 'success')
    except Exception as e:
        flash(f"Error uploading file: {str(e)}", 'danger')
    
    return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory(NAS_DIR, filename, as_attachment=True)
    except Exception as e:
        flash(f"Error downloading file: {str(e)}", 'danger')
        return redirect(url_for('index'))

@app.route('/view/<filename>')
def view_file(filename):
    try:
        file_path = os.path.join(NAS_DIR, filename)
        
        # Guess MIME type based on file extension
        mime_type, _ = mimetypes.guess_type(file_path)
        
        # Serve the file directly if it is viewable in the browser
        return send_file(file_path, mimetype=mime_type)
    except Exception as e:
        flash(f"Error viewing file: {str(e)}", 'danger')
        return redirect(url_for('index'))

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    try:
        os.remove(os.path.join(NAS_DIR, filename))
        flash(f"File '{filename}' deleted successfully.", 'success')
    except Exception as e:
        flash(f"Error deleting file: {str(e)}", 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
