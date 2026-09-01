import os
import tempfile
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from pypdf import PdfReader, PdfWriter

from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_me' # Required for flashing messages

# Configure upload settings
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'pdf_file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['pdf_file']
        password = request.form.get('password', '')

        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
            
        if not password:
            flash('Please provide a password')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            input_filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(input_filepath)
            
            # Process the PDF
            try:
                reader = PdfReader(input_filepath)
                
                if not reader.is_encrypted:
                    flash('This PDF is not password protected.')
                    return redirect(request.url)
                
                # Attempt to decrypt
                decrypted = reader.decrypt(password)
                
                if decrypted == 0: # 0 means failed decryption
                    flash('Incorrect password.')
                    return redirect(request.url)
                    
                # Create a writer to save the unlocked PDF
                writer = PdfWriter()
                
                # Add all pages to the writer
                for page in reader.pages:
                    writer.add_page(page)
                    
                # Save the new PDF to a temporary file
                output_filename = f"unlocked_{filename}"
                output_filepath = os.path.join(UPLOAD_FOLDER, output_filename)
                
                with open(output_filepath, "wb") as f:
                    writer.write(f)
                    
                # Send the file to the user
                return send_file(
                    output_filepath, 
                    as_attachment=True,
                    download_name=output_filename
                )
                
            except Exception as e:
                flash(f'An error occurred: {str(e)}')
                return redirect(request.url)
                
    return render_template('index.html')

if __name__ == '__main__':
    # Run the app
    app.run(debug=True, port=5000)
