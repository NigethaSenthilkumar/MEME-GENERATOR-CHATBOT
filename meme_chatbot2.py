from flask import Flask, request, render_template, send_from_directory, redirect, url_for
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import random
import requests
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'user_templates'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB limit

# Ensure directories exist
os.makedirs('meme_templates', exist_ok=True)
os.makedirs('generated_memes', exist_ok=True)
os.makedirs('user_templates', exist_ok=True)

# Enhanced meme database with 10 popular templates
MEME_DATABASE = {
    "drake": {
        "url": "https://i.imgflip.com/30b1gx.jpg",
        "text_boxes": [
            {"x": 100, "y": 50, "width": 300, "height": 100},  # Top
            {"x": 100, "y": 300, "width": 300, "height": 100}  # Bottom
        ]
    },
    "distracted_bf": {
        "url": "https://i.imgflip.com/1bij.jpg",
        "text_boxes": [
            {"x": 50, "y": 50, "width": 250, "height": 50},   # Left
            {"x": 400, "y": 50, "width": 250, "height": 50},   # Middle
            {"x": 700, "y": 50, "width": 250, "height": 50}    # Right
        ]
    },
    "two_buttons": {
        "url": "https://i.imgflip.com/9vct.jpg",
        "text_boxes": [
            {"x": 50, "y": 30, "width": 400, "height": 100},  # Top
            {"x": 50, "y": 160, "width": 400, "height": 100}   # Bottom
        ]
    },
    "expanding_brain": {
        "url": "https://i.imgflip.com/1g8my.jpg",
        "text_boxes": [
            {"x": 50, "y": 50, "width": 300, "height": 80},   # Bottom
            {"x": 50, "y": 200, "width": 300, "height": 80},   # Middle
            {"x": 50, "y": 350, "width": 300, "height": 80}    # Top
        ]
    },
    "change_my_mind": {
        "url": "https://i.imgflip.com/24y43o.jpg",
        "text_boxes": [
            {"x": 100, "y": 400, "width": 400, "height": 100}  # Sign
        ]
    }
}

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Handle template upload
        if 'custom_template' in request.files:
            file = request.files['custom_template']
            if file.filename != '':
                filename = secure_filename(file.filename)
                template_name = os.path.splitext(filename)[0]
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                return redirect(url_for('custom_template', template=template_name))
        
        # Handle meme generation
        template = request.form.get('template')
        if template and template in MEME_DATABASE:
            texts = request.form.getlist('text[]')
            output_filename = create_meme(template, texts)
            if output_filename:
                return render_template('result.html', 
                                    meme=output_filename,
                                    download_link=url_for('download', filename=output_filename))
    
    return render_template('index.html', 
                         templates=MEME_DATABASE.keys(),
                         custom_templates=get_custom_templates())

def create_meme(template_name, texts, custom=False):
    try:
        # Get template path
        if custom:
            template_path = f"user_templates/{template_name}.jpg"
        else:
            template_path = f"meme_templates/{template_name}.jpg"
            if not os.path.exists(template_path):
                download_template(template_name)
        
        # Load image and setup drawing
        img = Image.open(template_path)
        draw = ImageDraw.Draw(img)
        
        # Font configuration
        font = get_font()
        
        # Get text positions
        if custom:
            positions = get_default_positions(len(texts), img.size)
        else:
            positions = MEME_DATABASE[template_name]["text_boxes"]
        
        # Add text to each position
        for i, (text, pos) in enumerate(zip(texts, positions)):
            wrapped = textwrap.fill(text.upper(), width=20)
            draw.text(
                (pos["x"], pos["y"]),
                wrapped,
                font=font,
                fill="white",
                stroke_width=3,
                stroke_fill="black"
            )
        
        # Save output
        output_filename = f"meme_{random.randint(1000,9999)}.jpg"
        output_path = f"generated_memes/{output_filename}"
        img.save(output_path)
        return output_filename
        
    except Exception as e:
        print(f"Error creating meme: {str(e)}")
        return None

def get_font():
    """Get the best available font"""
    try:
        return ImageFont.truetype("impact.ttf", 40)
    except:
        try:
            return ImageFont.truetype("arialbd.ttf", 40)
        except:
            return ImageFont.load_default()

def get_default_positions(count, img_size):
    """Generate default positions for custom templates"""
    width, height = img_size
    positions = []
    for i in range(count):
        y = (i * height) // (count + 1)
        positions.append({"x": 50, "y": y, "width": width-100, "height": 100})
    return positions

def download_template(template_name):
    """Download template from URL"""
    try:
        url = MEME_DATABASE[template_name]["url"]
        response = requests.get(url, stream=True)
        with open(f"meme_templates/{template_name}.jpg", 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading template: {str(e)}")
        return False

def get_custom_templates():
    """Get list of user-uploaded templates"""
    return [os.path.splitext(f)[0] for f in os.listdir(app.config['UPLOAD_FOLDER']) 
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

@app.route('/custom/<template>')
def custom_template(template):
    return render_template('custom.html', template=template)

@app.route('/generate_custom', methods=['POST'])
def generate_custom():
    template = request.form['template']
    texts = request.form.getlist('text[]')
    output_filename = create_meme(template, texts, custom=True)
    if output_filename:
        return render_template('result.html', 
                            meme=output_filename,
                            download_link=url_for('download', filename=output_filename))
    return redirect(url_for('home'))

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory('generated_memes', filename)

@app.route('/deploy_guide')
def deploy_guide():
    return render_template('deploy.html')

if __name__ == '__main__':
    app.run(debug=True)
