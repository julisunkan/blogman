from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Post, SiteSettings
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Ensure instance directory exists and create tables
os.makedirs('instance', exist_ok=True)
with app.app_context():
    db.create_all()
    # Create default site settings if none exist
    if not SiteSettings.query.first():
        default_settings = SiteSettings(
            blog_title='Blog CMS', 
            blog_description='Welcome to Our Blog',
            primary_color='#667eea',
            secondary_color='#764ba2',
            background_color='#667eea',
            card_background='#ffffff',
            text_color='#333333',
            navbar_color='#000000'
        )
        db.session.add(default_settings)
        db.session.commit()

# Authentication decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Helper function to get site settings
def get_site_settings():
    settings = SiteSettings.query.first()
    if not settings:
        settings = SiteSettings(
            blog_title='Blog CMS', 
            blog_description='Welcome to Our Blog',
            primary_color='#667eea',
            secondary_color='#764ba2',
            background_color='#667eea',
            card_background='#ffffff',
            text_color='#333333',
            navbar_color='#000000'
        )
        db.session.add(settings)
        db.session.commit()
    return settings

# Template context processor to make site settings available to all templates
@app.context_processor
def inject_site_settings():
    return {'site_settings': get_site_settings()}

# Public routes
@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/post/<int:id>')
def post_detail(id):
    post = Post.query.get_or_404(id)
    return render_template('post_detail.html', post=post)

# Admin authentication
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == app.config['ADMIN_USERNAME'] and password == app.config['ADMIN_PASSWORD']:
            session['logged_in'] = True
            session.permanent = True
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    session.pop('logged_in', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# Admin dashboard
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('dashboard.html', posts=posts)

@app.route('/admin/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        featured_image = request.form.get('featured_image', '').strip() or None
        
        post = Post(title=title, content=content, featured_image=featured_image)
        db.session.add(post)
        db.session.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('new_post.html')

@app.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)
    
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        post.featured_image = request.form.get('featured_image', '').strip() or None
        db.session.commit()
        
        flash('Post updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_post.html', post=post)

@app.route('/admin/delete/<int:id>', methods=['POST'])
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    settings = get_site_settings()
    
    if request.method == 'POST':
        settings.blog_title = request.form['blog_title']
        settings.blog_description = request.form['blog_description']
        settings.primary_color = request.form['primary_color']
        settings.secondary_color = request.form['secondary_color']
        settings.background_color = request.form['background_color']
        settings.card_background = request.form['card_background']
        settings.text_color = request.form['text_color']
        settings.navbar_color = request.form['navbar_color']
        db.session.commit()
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin_settings'))
    
    return render_template('admin_settings.html', settings=settings)

@app.route('/manifest.json')
def serve_manifest():
    """Serve PWA manifest with proper MIME type"""
    from flask import send_from_directory
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')

@app.route('/certificate/<int:post_id>/<path:student_name>')
def download_certificate(post_id, student_name):
    """Generate and download certificate server-side"""
    from flask import Response
    import urllib.parse
    from datetime import datetime
    
    post = Post.query.get_or_404(post_id)
    settings = get_site_settings()
    
    # Decode the student name from URL
    student_name = urllib.parse.unquote(student_name)
    completion_date = datetime.now().strftime('%B %d, %Y')
    
    certificate_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Certificate - {student_name}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{
            font-family: 'Times New Roman', serif;
            background: linear-gradient(135deg, {settings.background_color} 0%, {settings.secondary_color} 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .certificate {{
            max-width: 800px;
            margin: 50px auto;
            background: white;
            padding: 60px;
            border: 8px solid {settings.primary_color};
            position: relative;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }}
        
        .certificate::before {{
            content: '';
            position: absolute;
            top: 20px;
            left: 20px;
            right: 20px;
            bottom: 20px;
            border: 3px solid {settings.secondary_color};
            pointer-events: none;
        }}
        
        .certificate-header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        
        .certificate-title {{
            font-size: 3rem;
            font-weight: bold;
            color: {settings.primary_color};
            margin-bottom: 10px;
            letter-spacing: 3px;
        }}
        
        .certificate-subtitle {{
            font-size: 1.2rem;
            color: {settings.secondary_color};
            margin-bottom: 30px;
        }}
        
        .student-name {{
            font-size: 2.5rem;
            font-weight: bold;
            color: {settings.secondary_color};
            text-decoration: underline;
            text-decoration-color: {settings.primary_color};
            margin: 20px 0;
        }}
        
        .tutorial-title {{
            font-size: 1.8rem;
            font-style: italic;
            color: {settings.primary_color};
            margin: 20px 0;
        }}
        
        .completion-text {{
            font-size: 1.1rem;
            line-height: 1.8;
            text-align: center;
            margin: 30px 0;
        }}
        
        .date-signature {{
            display: flex;
            justify-content: space-between;
            margin-top: 60px;
        }}
        
        .signature-line {{
            text-align: center;
            min-width: 200px;
        }}
        
        .signature-line hr {{
            border: 2px solid {settings.primary_color};
            margin: 10px 0;
        }}
        
        .signature-line small {{
            color: {settings.secondary_color};
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="certificate">
        <div class="certificate-header">
            <h1 class="certificate-title">CERTIFICATE</h1>
            <h2 class="certificate-subtitle">of Achievement</h2>
        </div>
        
        <div class="certificate-content text-center">
            <p class="completion-text">This is to certify that</p>
            
            <h2 class="student-name">{student_name}</h2>
            
            <p class="completion-text">has successfully completed the tutorial</p>
            
            <h3 class="tutorial-title">"{post.title}"</h3>
            
            <p class="completion-text">
                and has demonstrated proficiency in the subject matter<br>
                on this day of <strong>{completion_date}</strong>
            </p>
        </div>
        
        <div class="date-signature">
            <div class="signature-line">
                <hr>
                <small>Date</small>
            </div>
            <div class="signature-line">
                <hr>
                <small>Tutorial Platform</small>
            </div>
        </div>
    </div>
</body>
</html>
    """
    
    response = Response(certificate_html, mimetype='text/html')
    response.headers['Content-Disposition'] = f'attachment; filename="certificate-{student_name.replace(" ", "-").lower()}.html"'
    return response

@app.route('/dynamic-styles.css')
def dynamic_styles():
    settings = get_site_settings()
    
    css_content = f"""
/* Dynamic styles based on admin settings */
.gradient-bg {{
    background: linear-gradient(135deg, {settings.background_color} 0%, {settings.secondary_color} 100%);
}}

.btn-gradient {{
    background: linear-gradient(45deg, {settings.primary_color}, {settings.secondary_color});
}}

.btn-gradient:hover {{
    background: linear-gradient(45deg, {settings.secondary_color}, {settings.primary_color});
}}

.blog-card {{
    background: rgba({hex_to_rgb(settings.card_background)}, 0.95);
}}

.navbar-dark {{
    background: rgba({hex_to_rgb(settings.navbar_color)}, 0.8) !important;
}}

.certificate {{
    border: 3px solid {settings.primary_color};
}}

.certificate::before {{
    border: 2px solid {settings.secondary_color};
}}

.certificate-header h2 {{
    color: {settings.primary_color};
}}

.student-name {{
    color: {settings.secondary_color} !important;
    text-decoration-color: {settings.primary_color};
}}

.tutorial-title {{
    color: {settings.primary_color} !important;
}}

.signature-line hr {{
    border: 1px solid {settings.primary_color};
}}

.signature-line small {{
    color: {settings.secondary_color};
}}

.form-control {{
    border: 2px solid rgba({hex_to_rgb(settings.primary_color)}, 0.3);
}}

.form-control:focus {{
    border-color: {settings.primary_color};
    box-shadow: 0 0 0 0.2rem rgba({hex_to_rgb(settings.primary_color)}, 0.25);
}}

.text-primary {{
    color: {settings.text_color} !important;
}}

.card-title {{
    color: {settings.text_color};
}}

.post-content {{
    color: {settings.text_color};
}}
"""
    
    from flask import Response
    return Response(css_content, mimetype='text/css')

def hex_to_rgb(hex_color):
    """Convert hex color to RGB values for rgba usage"""
    hex_color = hex_color.lstrip('#')
    return ', '.join(str(int(hex_color[i:i+2], 16)) for i in (0, 2, 4))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)