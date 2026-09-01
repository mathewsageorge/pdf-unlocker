import os
import tempfile
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from pypdf import PdfReader, PdfWriter
from PIL import Image
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_me'

UPLOAD_FOLDER = tempfile.gettempdir()

def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/unlock-pdf', methods=['GET', 'POST'])
def unlock_pdf():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['pdf_file']
        password = request.form.get('password', '')

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
            
        if not password:
            flash('Please provide a password')
            return redirect(request.url)

        if file and allowed_file(file.filename, {'pdf'}):
            filename = secure_filename(file.filename)
            input_filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(input_filepath)
            
            try:
                reader = PdfReader(input_filepath)
                if not reader.is_encrypted:
                    flash('This PDF is not password protected.')
                    return redirect(request.url)
                
                decrypted = reader.decrypt(password)
                if decrypted == 0:
                    flash('Incorrect password.')
                    return redirect(request.url)
                    
                writer = PdfWriter()
                for page in reader.pages:
                    writer.add_page(page)
                    
                output_filename = f"unlocked_{filename}"
                output_filepath = os.path.join(UPLOAD_FOLDER, output_filename)
                
                with open(output_filepath, "wb") as f:
                    writer.write(f)
                    
                return send_file(output_filepath, as_attachment=True, download_name=output_filename)
            except Exception as e:
                flash(f'An error occurred: {str(e)}')
                return redirect(request.url)
                
    return render_template('unlock_pdf.html')

@app.route('/convert-image', methods=['GET', 'POST'])
def convert_image():
    if request.method == 'POST':
        if 'image_file' not in request.files:
            flash('No file part')
            return redirect(request.url)
            
        file = request.files['image_file']
        target_format = request.form.get('target_format', 'PNG').upper()
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
            
        if file:
            filename = secure_filename(file.filename)
            input_filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(input_filepath)
            
            try:
                img = Image.open(input_filepath)
                # Convert RGBA to RGB if saving as JPEG
                if target_format == 'JPEG' and img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                    
                name_without_ext = os.path.splitext(filename)[0]
                output_ext = target_format.lower()
                if output_ext == 'jpeg': output_ext = 'jpg'
                
                output_filename = f"converted_{name_without_ext}.{output_ext}"
                output_filepath = os.path.join(UPLOAD_FOLDER, output_filename)
                
                img.save(output_filepath, format=target_format)
                
                return send_file(output_filepath, as_attachment=True, download_name=output_filename)
            except Exception as e:
                flash(f'An error occurred: {str(e)}')
                return redirect(request.url)
                
    return render_template('convert_image.html')

@app.route('/resize-image', methods=['GET', 'POST'])
def resize_image():
    if request.method == 'POST':
        if 'image_file' not in request.files:
            flash('No file part')
            return redirect(request.url)
            
        file = request.files['image_file']
        width = request.form.get('width')
        height = request.form.get('height')
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
            
        if not width or not height:
            flash('Please provide both width and height')
            return redirect(request.url)
            
        if file:
            filename = secure_filename(file.filename)
            input_filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(input_filepath)
            
            try:
                img = Image.open(input_filepath)
                new_size = (int(width), int(height))
                resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                output_filename = f"resized_{filename}"
                output_filepath = os.path.join(UPLOAD_FOLDER, output_filename)
                
                resized_img.save(output_filepath)
                
                return send_file(output_filepath, as_attachment=True, download_name=output_filename)
            except Exception as e:
                flash(f'An error occurred: {str(e)}')
                return redirect(request.url)

    return render_template('resize_image.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
