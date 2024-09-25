from flask import Flask, request, send_from_directory, render_template, redirect, url_for
import os

app = Flask(__name__)
NAS_DIR = '/home/ishanurgaonkar/nas'  # Change this to your NAS path

@app.route('/')
def index():
    files = os.listdir(NAS_DIR)
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename != '':
        file.save(os.path.join(NAS_DIR, file.filename))
    return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(NAS_DIR, filename, as_attachment=True)

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    try:
        os.remove(os.path.join(NAS_DIR, filename))
    except Exception as e:
        return str(e)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
