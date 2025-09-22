from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    featured_image = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Post {self.id}: {self.title}>'

class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blog_title = db.Column(db.String(200), nullable=False, default='Blog CMS')
    blog_description = db.Column(db.Text, nullable=False, default='Welcome to Our Blog')
    
    def __repr__(self):
        return f'<SiteSettings: {self.blog_title}>'