from flask import Flask, request, send_from_directory, render_template, redirect, url_for, flash, jsonify
import os
import mimetypes
from datetime import datetime

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'ishanihar'  # Secret key for session management
NAS_DIR = '/home/ishanurgaonkar/nas'  # Directory where files are stored

# Ensure the NAS directory exists
if not os.path.exists(NAS_DIR):
    os.makedirs(NAS_DIR)  # Create the directory if it does not exist

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # Set max file upload size to 10GB

# Files to exclude from the listing
excluded_files = ['.DS_Store', 'Thumbs.db', '$RECYCLE.BIN', 'System Volume Information']

def get_filtered_files(path):
    """
    List files and directories in the given path, excluding hidden/system files
    and those specified in the excluded_files list.
    """
    try:
        files = os.listdir(path)  # List all files and directories
        # Filter out files that start with '.' or are in the excluded list
        return [f for f in files if not f.startswith('.') and f not in excluded_files]
    except Exception as e:
        flash(f"Error accessing directory: {str(e)}", 'danger')  # Flash an error message
        return []

@app.route('/', defaults={'path': '', 'search': ''})
@app.route('/<path:path>', defaults={'search': ''})
@app.route('/search/<search>', defaults={'path': ''})
def index(path, search):
    """
    Main page for displaying files and directories.
    Supports searching and navigating through directories.
    """
    full_path = os.path.join(NAS_DIR, path)  # Construct the full path

    if not os.path.exists(full_path):
        flash(f"Directory '{path}' does not exist.", 'danger')  # Flash an error if the path does not exist
        return redirect(url_for('index'))  # Redirect to the main page

    if os.path.isdir(full_path):
        files = get_filtered_files(full_path)  # Get filtered files

        # Implement search functionality
        if search:
            files = [f for f in files if search.lower() in f.lower()]  # Filter files based on search input

        # Sort files by modification time
        files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(full_path, x)), reverse=True)
        
        return render_template('index.html', files=files, current_path=path, search=search)  # Render the main page
    else:
        # If it's a file, serve it for download
        return send_from_directory(NAS_DIR, path, as_attachment=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint to handle file uploads.
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400  # Handle missing file part
    
    file = request.files['file']  # Get the uploaded file
    current_path = request.form.get('current_path', '')  # Get the current path from the form

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400  # Handle empty file name

    try:
        save_path = os.path.join(NAS_DIR, current_path)  # Construct the save path
        file.save(os.path.join(save_path, file.filename))  # Save the file
        return jsonify({'success': True, 'message': f"File '{file.filename}' uploaded successfully!"}), 200  # Success response
    except Exception as e:
        return jsonify({'success': False, 'message': f"Error uploading file: {str(e)}"}), 500  # Error response

@app.route('/create_folder', methods=['POST'])
def create_folder():
    """
    Endpoint to create a new folder.
    """
    folder_name = request.form.get('folder_name')  # Get folder name from the form
    current_path = request.form.get('current_path', '')  # Get current path

    if folder_name:
        try:
            # Construct the new folder path within the NAS directory
            new_folder_path = os.path.join(NAS_DIR, current_path, folder_name)  
            os.makedirs(new_folder_path, exist_ok=True)  # Create the folder
            flash(f"Folder '{folder_name}' created successfully!", 'success')  # Flash success message
        except Exception as e:
            flash(f"Error creating folder: {str(e)}", 'danger')  # Flash error message

    return redirect(url_for('index', path=current_path))  # Redirect back to the current path

@app.route('/download/<path:filename>')
def download_file(filename):
    """
    Endpoint to download a file.
    """
    try:
        return send_from_directory(NAS_DIR, filename, as_attachment=True)  # Serve the file for download
    except Exception as e:
        flash(f"Error downloading file: {str(e)}", 'danger')  # Flash error message
        return redirect(url_for('index'))  # Redirect to the main page

@app.route('/view/<path:filename>')
def view_file(filename):
    """
    Endpoint to view a file (supports media types and text files).
    """
    try:
        file_path = os.path.join(NAS_DIR, filename)  # Construct the file path
        
        # Guess MIME type based on file extension
        mime_type, _ = mimetypes.guess_type(file_path)
        
        if mime_type:
            # Handle media types (PDF, video, and audio)
            if mime_type.startswith('video/') or mime_type.startswith('audio/'):
                return render_template('view_media.html', filename=filename, mime_type=mime_type)  # Render media viewer
            elif mime_type == 'text/plain':
                with open(file_path, 'r') as file:
                    file_content = file.read()  # Read text file content
                return render_template('view_media.html', filename=filename, mime_type=mime_type, file_content=file_content)  # Render text viewer
            else:
                return send_from_directory(NAS_DIR, filename, mimetype=mime_type)  # Serve the file directly
        else:
            flash(f"File '{filename}' cannot be viewed.", 'danger')  # Flash error message
            return redirect(url_for('index'))  # Redirect to the main page
    except Exception as e:
        flash(f"Error viewing file: {str(e)}", 'danger')  # Flash error message
        return redirect(url_for('index'))  # Redirect to the main page

@app.route('/delete/<path:filename>', methods=['POST'])
def delete_file(filename):
    """
    Endpoint to delete a file.
    """
    try:
        os.remove(os.path.join(NAS_DIR, filename))  # Remove the file
        flash(f"File '{filename}' deleted successfully.", 'success')  # Flash success message
    except Exception as e:
        flash(f"Error deleting file: {str(e)}", 'danger')  # Flash error message
    return redirect(url_for('index'))  # Redirect to the main page

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Start the Flask application
