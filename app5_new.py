from flask import Flask, request, send_from_directory, render_template, redirect, url_for, flash, send_file
import os
import mimetypes

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'ishanihar'  # Secret key for session management
NAS_DIR = '/home/ishanurgaonkar/nas'  # Directory where files are stored

# Ensure the NAS directory exists
if not os.path.exists(NAS_DIR):
    os.makedirs(NAS_DIR)

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

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    """
    Main page for displaying files and directories.
    """
    full_path = os.path.join(NAS_DIR, path)  # Construct the full path

    if not os.path.exists(full_path):
        flash(f"Directory '{path}' does not exist.", 'danger')  # Flash an error if the path does not exist
        return redirect(url_for('index'))  # Redirect to the main page

    if os.path.isdir(full_path):
        files = get_filtered_files(full_path)  # Get filtered files
        return render_template('index.html', files=files, current_path=path)  # Render the main page
    else:
        # If it's a file, serve it for download
        return send_from_directory(NAS_DIR, path, as_attachment=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint to handle file uploads.
    """
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['file']  # Get the uploaded file
    current_path = request.form.get('current_path', '')  # Get the current path from the form

    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    
    try:
        save_path = os.path.join(NAS_DIR, current_path)  # Construct the save path
        file.save(os.path.join(save_path, file.filename))  # Save the file
        flash(f"File '{file.filename}' uploaded successfully!", 'success')  # Flash success message
    except Exception as e:
        flash(f"Error uploading file: {str(e)}", 'danger')  # Flash error message
    
    return redirect(url_for('index', path=current_path))

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
                return send_file(file_path, mimetype=mime_type)  # Serve the file directly
        else:
            flash(f"File '{filename}' cannot be viewed.", 'danger')  # Flash error message
            return redirect(url_for('index'))  # Redirect to the main page
    except Exception as e:
        flash(f"Error viewing file: {str(e)}", 'danger')  # Flash error message
        return redirect(url_for('index'))  # Redirect to the main page

@app.route('/delete/<path:filename>', methods=['POST'])
def delete_file(filename):
    """
    Endpoint to delete a file or folder.
    """
    try:
        full_path = os.path.join(NAS_DIR, filename)
        if os.path.isdir(full_path):
            os.rmdir(full_path)  # Remove the folder
            flash(f"Folder '{filename}' deleted successfully.", 'success')  # Flash success message
        else:
            os.remove(full_path)  # Remove the file
            flash(f"File '{filename}' deleted successfully.", 'success')  # Flash success message
    except Exception as e:
        flash(f"Error deleting file/folder: {str(e)}", 'danger')  # Flash error message
    return redirect(url_for('index'))  # Redirect to the main page

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Start the Flask application
