import os
import base64
import uuid
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, date, time
from pathlib import Path
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, g
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
from io import BytesIO
import jwt
from dotenv import load_dotenv

load_dotenv()

# ========== KONFİGÜRASYON ==========
BASE_DIR = Path(__file__).resolve().parent
PHOTO_ROOT = BASE_DIR / 'Fotoraflar'
DATABASE_PATH = BASE_DIR / 'app.db'

SECRET_KEY = os.environ.get('SECRET_KEY', 'cok-gizli-anahtar-degistir')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin123!')

# E-posta ayarları (Gmail SMTP)
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', 'diyetmaili01@gmail.com')
SMTP_PASS = os.environ.get('SMTP_PASS', '')
NOTIFICATION_EMAIL = os.environ.get('NOTIFICATION_EMAIL', 'diyetmaili01@gmail.com')

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['JSON_AS_ASCII'] = False

db = SQLAlchemy(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ========== IP BAN SİSTEMİ ==========
ip_attempts = {}
ip_banned = {}

def get_client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

def is_ip_banned(ip):
    if ip in ip_banned:
        if datetime.utcnow() < ip_banned[ip]:
            return True
        else:
            del ip_banned[ip]
    return False

def register_failed_attempt(ip):
    now = datetime.utcnow()
    if ip not in ip_attempts:
        ip_attempts[ip] = {'count': 1, 'first': now}
    else:
        if now - ip_attempts[ip]['first'] > timedelta(minutes=15):
            ip_attempts[ip] = {'count': 1, 'first': now}
        else:
            ip_attempts[ip]['count'] += 1
    if ip_attempts[ip]['count'] >= 3:
        ip_banned[ip] = now + timedelta(hours=1)
        ip_attempts.pop(ip, None)
        return True
    return False

# ========== MODELLER ==========
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Package(db.Model):
    __tablename__ = 'packages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.String(100))
    cover_image = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    features = db.relationship('PackageFeature', backref='package', cascade='all, delete-orphan', order_by='PackageFeature.sort_order')

class PackageFeature(db.Model):
    __tablename__ = 'package_features'
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    sort_order = db.Column(db.Integer, default=0)

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.Time)
    location = db.Column(db.String(255))
    is_online = db.Column(db.Boolean, default=False)
    cover_image = db.Column(db.String(500))
    capacity = db.Column(db.Integer)
    registration_link = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    summary = db.Column(db.Text)
    content = db.Column(db.Text)
    cover_image = db.Column(db.String(500))
    category = db.Column(db.String(100))
    author = db.Column(db.String(100))
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    goal = db.Column(db.String(100))
    activity_level = db.Column(db.String(100))
    nutrition_preference = db.Column(db.String(100))
    allergies = db.Column(db.Text)
    training_experience = db.Column(db.String(100))
    environment = db.Column(db.String(50))
    days_per_week = db.Column(db.Integer)
    note = db.Column(db.Text)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'))
    status = db.Column(db.String(50), default='Bekliyor')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
    service = db.Column(db.String(100))
    note = db.Column(db.Text)
    status = db.Column(db.String(50), default='Bekliyor')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SocialLink(db.Model):
    __tablename__ = 'social_links'
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), unique=True, nullable=False)
    url = db.Column(db.String(500), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SiteSetting(db.Model):
    __tablename__ = 'site_settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Media(db.Model):
    __tablename__ = 'media'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(500), nullable=False)
    filepath = db.Column(db.String(1000), nullable=False)
    filetype = db.Column(db.String(50))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), nullable=False)
    package_name = db.Column(db.String(255))
    price = db.Column(db.Float)
    note = db.Column(db.Text)
    status = db.Column(db.String(50), default='Bekliyor')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ========== YARDIMCILAR ==========
def slugify(text):
    text = text.lower()
    text = re.sub(r'[çÇ]', 'c', text)
    text = re.sub(r'[ğĞ]', 'g', text)
    text = re.sub(r'[ıİ]', 'i', text)
    text = re.sub(r'[öÖ]', 'o', text)
    text = re.sub(r'[şŞ]', 's', text)
    text = re.sub(r'[üÜ]', 'u', text)
    text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    return text

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return None

def parse_time(time_str):
    try:
        return datetime.strptime(time_str, '%H:%M').time()
    except:
        return None

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def json_response(success=True, data=None, message=None, status=200):
    response = {'success': success}
    if data is not None:
        response['data'] = data
    if message is not None:
        response['message'] = message
    return jsonify(response), status

def generate_token(user_id):
    payload = {'user_id': user_id, 'exp': datetime.utcnow() + timedelta(hours=12), 'iat': datetime.utcnow()}
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def decode_token(token):
    try:
        return jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except:
        return None

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        if not token:
            return json_response(False, message='Yetkilendirme gerekli.', status=401)
        payload = decode_token(token)
        if not payload:
            return json_response(False, message='Geçersiz token.', status=401)
        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return json_response(False, message='Kullanıcı bulunamadı.', status=401)
        g.user_id = user.id
        return f(*args, **kwargs)
    return decorated

def save_image(data_bytes, folder='general', extension='jpg', filename_prefix='img'):
    target_folder = PHOTO_ROOT / folder
    target_folder.mkdir(parents=True, exist_ok=True)
    unique_name = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.{extension}"
    file_path = target_folder / unique_name
    with open(file_path, 'wb') as f:
        f.write(data_bytes)
    return f"/{folder}/{unique_name}"

def validate_image(file_data, filename=None):
    if isinstance(file_data, str) and file_data.startswith('data:'):
        try:
            header, encoded = file_data.split(',', 1)
            mime = header.split(':')[1].split(';')[0]
            allowed = {'image/jpeg':'jpg', 'image/png':'png', 'image/webp':'webp', 'image/gif':'gif'}
            if mime not in allowed:
                return None, 'Desteklenmeyen dosya türü.'
            data_bytes = base64.b64decode(encoded)
            if len(data_bytes) > 10*1024*1024:
                return None, 'Dosya boyutu 10 MB\'ı geçemez.'
            return data_bytes, allowed[mime]
        except:
            return None, 'Base64 verisi çözümlenemedi.'
    else:
        if not filename:
            filename = getattr(file_data, 'filename', '')
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        allowed_exts = {'jpg','jpeg','png','webp','gif'}
        if ext not in allowed_exts:
            return None, 'Desteklenmeyen dosya uzantısı.'
        data_bytes = file_data.read()
        if len(data_bytes) > 10*1024*1024:
            return None, 'Dosya boyutu 10 MB\'ı geçemez.'
        try:
            img = Image.open(BytesIO(data_bytes))
            img.verify()
        except:
            return None, 'Geçersiz görsel dosyası.'
        return data_bytes, ext if ext != 'jpeg' else 'jpg'

def delete_image(relative_path):
    if not relative_path:
        return
    relative_path = relative_path.lstrip('/')
    file_path = (PHOTO_ROOT / relative_path).resolve()
    if PHOTO_ROOT.resolve() in file_path.parents and file_path.exists():
        file_path.unlink()

def send_email(to_email, subject, body):
    if not SMTP_PASS:
        print(f"[EMAIL] Gönderilemedi: SMTP şifresi ayarlanmamış. Konu: {subject}")
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"[EMAIL] Hata: {str(e)}")
        return False

# ========== VERİTABANI BAŞLATMA ==========
def init_db():
    PHOTO_ROOT.mkdir(exist_ok=True)
    for sub in ['packages', 'events', 'blog', 'profile', 'general']:
        (PHOTO_ROOT / sub).mkdir(exist_ok=True)
    db.create_all()

    admin = User.query.filter_by(email=ADMIN_EMAIL).first()
    if not admin:
        admin = User(email=ADMIN_EMAIL, is_active=True)
        admin.set_password(ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin oluşturuldu: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")

    socials = [
        ('instagram', 'https://www.instagram.com/senaform'),
        ('tiktok', 'https://www.tiktok.com/@senaform'),
        ('youtube', 'https://www.youtube.com/@senaform'),
        ('whatsapp', 'https://wa.me/905555555555'),
        ('email', 'mailto:info@senaform.com')
    ]
    for platform, url in socials:
        if not SocialLink.query.filter_by(platform=platform).first():
            db.session.add(SocialLink(platform=platform, url=url))
    db.session.commit()

    settings = {
        'site_name': 'SENA FORM',
        'hero_title': 'Beslenmeni Planla. Hareketini Güçlendir.',
        'hero_description': 'Kişisel hedeflerine uygun beslenme ve egzersiz programlarıyla daha sürdürülebilir bir yaşam oluştur.',
        'footer_text': '© 2026 SENA FORM. Tüm hakları saklıdır.',
        'phone': '+90 555 555 55 55',
        'email': 'info@senaform.com',
        'about_text': 'Beslenme ve Diyetetik ile Egzersiz ve Spor Bilimleri alanlarındaki eğitimlerimle, bilimi günlük hayata uygulanabilir, sürdürülebilir ve kişiye özel programlara dönüştürüyorum.'
    }
    for key, value in settings.items():
        if not SiteSetting.query.filter_by(key=key).first():
            db.session.add(SiteSetting(key=key, value=value))
    db.session.commit()

    if Package.query.count() == 0:
        p1 = Package(name='4 Haftalık Beslenme Programı', slug='4-haftalik-beslenme', category='beslenme',
                     description='Kişiye özel beslenme planı, haftalık takip ve online destek.',
                     price=1499, duration='4 Hafta', is_active=True, is_featured=False, sort_order=1)
        p1.features = [PackageFeature(text='Haftalık beslenme listesi', sort_order=0),
                       PackageFeature(text='Online görüşme', sort_order=1),
                       PackageFeature(text='WhatsApp destek', sort_order=2)]
        db.session.add(p1)
        p2 = Package(name='8 Haftalık Egzersiz Programı', slug='8-haftalik-egzersiz', category='egzersiz',
                     description='Seviyene uygun antrenman planı, video gösterimler ve ilerleme takibi.',
                     price=1799, duration='8 Hafta', is_active=True, is_featured=True, sort_order=2)
        p2.features = [PackageFeature(text='Haftalık antrenman planı', sort_order=0),
                       PackageFeature(text='Video kütüphanesi', sort_order=1),
                       PackageFeature(text='Form kontrolü', sort_order=2)]
        db.session.add(p2)
        p3 = Package(name='12 Haftalık Beslenme + Egzersiz', slug='12-haftalik-kombine', category='kombine',
                     description='Beslenme ve egzersiz birlikte, kapsamlı dönüşüm programı.',
                     price=2999, duration='12 Hafta', is_active=True, is_featured=True, sort_order=3)
        p3.features = [PackageFeature(text='Kişiye özel beslenme planı', sort_order=0),
                       PackageFeature(text='Antrenman programı', sort_order=1),
                       PackageFeature(text='Haftalık online görüşme', sort_order=2),
                       PackageFeature(text='Sınırsız WhatsApp destek', sort_order=3)]
        db.session.add(p3)
        db.session.commit()

    if Event.query.count() == 0:
        e1 = Event(title='Sağlıklı Yaşam Webinarı', description='Beslenme ve egzersizde sürdürülebilirlik üzerine bilgilendirici online seminer.',
                   event_date=date(2026, 9, 20), event_time=time(19, 0), location='Online', is_online=True,
                   capacity=100, is_active=True)
        e2 = Event(title='Formda Kalma Atölyesi', description='Uygulamalı egzersiz atölyesi.',
                   event_date=date(2026, 10, 5), event_time=time(18, 30), location='İstanbul, Kadıköy', is_online=False,
                   capacity=20, is_active=True)
        db.session.add(e1)
        db.session.add(e2)
        db.session.commit()

    if BlogPost.query.count() == 0:
        b1 = BlogPost(title='Protein Kaynakları Hakkında 5 Pratik Öneri', slug='5-pratik-protein-kaynagi',
                      summary='Günlük protein ihtiyacınızı karşılamak için pratik öneriler.',
                      content='<p>Protein, kas gelişimi ve tokluk için önemlidir...</p>',
                      category='Beslenme', author='Sena Form', published_at=datetime.utcnow(), is_active=True)
        b2 = BlogPost(title='Evde Antrenman Yapmanın Püf Noktaları', slug='evde-antrenman-puf-noktalari',
                      summary='Ekipmansız etkili antrenman yöntemleri.',
                      content='<p>Evde antrenman yaparken dikkat edilmesi gerekenler...</p>',
                      category='Egzersiz', author='Sena Form', published_at=datetime.utcnow(), is_active=True)
        b3 = BlogPost(title='Sürdürülebilir Beslenme Nasıl Olur?', slug='surdurulebilir-beslenme',
                      summary='Kısa vadeli diyetler yerine kalıcı alışkanlıklar.',
                      content='<p>Sürdürülebilir beslenme, yaşam tarzıdır...</p>',
                      category='Yaşam', author='Sena Form', published_at=datetime.utcnow(), is_active=True)
        db.session.add(b1)
        db.session.add(b2)
        db.session.add(b3)
        db.session.commit()

# ========== API ROUTES ==========
@app.route('/api/auth/login', methods=['POST'])
def login():
    ip = get_client_ip()
    if is_ip_banned(ip):
        return json_response(False, message='IP adresiniz geçici olarak banlandı. Lütfen 1 saat sonra tekrar deneyin.', status=403)

    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        if register_failed_attempt(ip):
            return json_response(False, message='3 başarısız deneme. IP adresiniz 1 saat banlandı.', status=403)
        return json_response(False, message='E-posta veya şifre hatalı.', status=401)
    if not user.is_active:
        return json_response(False, message='Hesabınız pasif durumda.', status=403)
    user.last_login = datetime.utcnow()
    db.session.commit()
    token = generate_token(user.id)
    return json_response(True, data={'token': token, 'email': user.email}, message='Giriş başarılı.')

@app.route('/api/auth/me', methods=['GET'])
@admin_required
def me():
    user = User.query.get(g.user_id)
    return json_response(True, data={'email': user.email})

# Paketler
@app.route('/api/packages', methods=['GET'])
def get_packages():
    query = Package.query.filter_by(is_active=True)
    category = request.args.get('category')
    if category:
        query = query.filter(Package.category == category)
    packages = query.order_by(Package.sort_order, Package.created_at.desc()).all()
    data = []
    for p in packages:
        data.append({
            'id': p.id,
            'name': p.name,
            'slug': p.slug,
            'category': p.category,
            'description': p.description,
            'price': p.price,
            'duration': p.duration,
            'cover_image': p.cover_image,
            'is_active': p.is_active,
            'is_featured': p.is_featured,
            'sort_order': p.sort_order,
            'features': [f.text for f in p.features]
        })
    return json_response(True, data=data)

@app.route('/api/packages/<int:package_id>', methods=['GET'])
def get_package(package_id):
    p = Package.query.get_or_404(package_id)
    if not p.is_active:
        return json_response(False, message='Paket aktif değil.', status=404)
    return json_response(True, data={
        'id': p.id,
        'name': p.name,
        'slug': p.slug,
        'category': p.category,
        'description': p.description,
        'price': p.price,
        'duration': p.duration,
        'cover_image': p.cover_image,
        'features': [f.text for f in p.features]
    })

@app.route('/api/packages', methods=['POST'])
@admin_required
def create_package():
    data = request.get_json() or {}
    if not data.get('name') or not data.get('category') or data.get('price') is None:
        return json_response(False, message='Paket adı, kategori ve fiyat zorunludur.', status=400)
    slug = data.get('slug') or slugify(data['name'])
    if Package.query.filter_by(slug=slug).first():
        return json_response(False, message='Bu slug zaten mevcut.', status=400)
    p = Package(
        name=data['name'],
        slug=slug,
        category=data.get('category'),
        description=data.get('description', ''),
        price=float(data.get('price', 0)),
        duration=data.get('duration'),
        cover_image=data.get('cover_image'),
        is_active=data.get('is_active', True),
        is_featured=data.get('is_featured', False),
        sort_order=int(data.get('sort_order', 0))
    )
    features = data.get('features', [])
    for idx, text in enumerate(features):
        p.features.append(PackageFeature(text=text, sort_order=idx))
    db.session.add(p)
    db.session.commit()
    return json_response(True, message='Paket oluşturuldu.', status=201)

@app.route('/api/packages/<int:package_id>', methods=['PUT'])
@admin_required
def update_package(package_id):
    p = Package.query.get_or_404(package_id)
    data = request.get_json() or {}
    if 'name' in data and data['name']:
        p.name = data['name']
        if 'slug' not in data:
            p.slug = slugify(data['name'])
    if 'slug' in data:
        p.slug = data['slug']
    if 'category' in data:
        p.category = data['category']
    if 'description' in data:
        p.description = data['description']
    if 'price' in data:
        p.price = float(data['price'])
    if 'duration' in data:
        p.duration = data['duration']
    if 'cover_image' in data:
        p.cover_image = data['cover_image']
    if 'is_active' in data:
        p.is_active = data['is_active']
    if 'is_featured' in data:
        p.is_featured = data['is_featured']
    if 'sort_order' in data:
        p.sort_order = int(data['sort_order'])
    if 'features' in data:
        for f in p.features:
            db.session.delete(f)
        for idx, text in enumerate(data['features']):
            p.features.append(PackageFeature(text=text, sort_order=idx))
    db.session.commit()
    return json_response(True, message='Paket güncellendi.')

@app.route('/api/packages/<int:package_id>', methods=['DELETE'])
@admin_required
def delete_package(package_id):
    p = Package.query.get_or_404(package_id)
    if p.cover_image:
        delete_image(p.cover_image)
    db.session.delete(p)
    db.session.commit()
    return json_response(True, message='Paket silindi.')

# Etkinlikler
@app.route('/api/events', methods=['GET'])
def get_events():
    events = Event.query.filter_by(is_active=True).order_by(Event.event_date.asc()).all()
    data = [{
        'id': e.id,
        'title': e.title,
        'description': e.description,
        'event_date': e.event_date.isoformat() if e.event_date else None,
        'event_time': e.event_time.strftime('%H:%M') if e.event_time else None,
        'location': e.location,
        'is_online': e.is_online,
        'cover_image': e.cover_image,
        'capacity': e.capacity,
        'registration_link': e.registration_link
    } for e in events]
    return json_response(True, data=data)

@app.route('/api/events', methods=['POST'])
@admin_required
def create_event():
    data = request.get_json() or {}
    if not data.get('title') or not data.get('event_date'):
        return json_response(False, message='Başlık ve tarih zorunludur.', status=400)
    e = Event(
        title=data['title'],
        description=data.get('description', ''),
        event_date=parse_date(data['event_date']),
        event_time=parse_time(data['event_time']) if data.get('event_time') else None,
        location=data.get('location'),
        is_online=data.get('is_online', False),
        cover_image=data.get('cover_image'),
        capacity=int(data['capacity']) if data.get('capacity') else None,
        registration_link=data.get('registration_link'),
        is_active=data.get('is_active', True)
    )
    db.session.add(e)
    db.session.commit()
    return json_response(True, message='Etkinlik oluşturuldu.', status=201)

@app.route('/api/events/<int:event_id>', methods=['PUT'])
@admin_required
def update_event(event_id):
    e = Event.query.get_or_404(event_id)
    data = request.get_json() or {}
    if 'title' in data:
        e.title = data['title']
    if 'description' in data:
        e.description = data['description']
    if 'event_date' in data:
        e.event_date = parse_date(data['event_date'])
    if 'event_time' in data:
        e.event_time = parse_time(data['event_time']) if data['event_time'] else None
    if 'location' in data:
        e.location = data['location']
    if 'is_online' in data:
        e.is_online = data['is_online']
    if 'cover_image' in data:
        e.cover_image = data['cover_image']
    if 'capacity' in data:
        e.capacity = int(data['capacity']) if data['capacity'] else None
    if 'registration_link' in data:
        e.registration_link = data['registration_link']
    if 'is_active' in data:
        e.is_active = data['is_active']
    db.session.commit()
    return json_response(True, message='Etkinlik güncellendi.')

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
@admin_required
def delete_event(event_id):
    e = Event.query.get_or_404(event_id)
    if e.cover_image:
        delete_image(e.cover_image)
    db.session.delete(e)
    db.session.commit()
    return json_response(True, message='Etkinlik silindi.')

# Blog
@app.route('/api/blog', methods=['GET'])
def get_blog_posts():
    posts = BlogPost.query.filter_by(is_active=True).order_by(BlogPost.published_at.desc()).all()
    data = [{
        'id': p.id,
        'title': p.title,
        'slug': p.slug,
        'summary': p.summary,
        'cover_image': p.cover_image,
        'category': p.category,
        'author': p.author,
        'published_at': p.published_at.isoformat() if p.published_at else None
    } for p in posts]
    return json_response(True, data=data)

@app.route('/api/blog/<slug>', methods=['GET'])
def get_blog_post(slug):
    post = BlogPost.query.filter_by(slug=slug, is_active=True).first_or_404()
    return json_response(True, data={
        'id': post.id,
        'title': post.title,
        'slug': post.slug,
        'summary': post.summary,
        'content': post.content,
        'cover_image': post.cover_image,
        'category': post.category,
        'author': post.author,
        'published_at': post.published_at.isoformat() if post.published_at else None
    })

@app.route('/api/blog', methods=['POST'])
@admin_required
def create_blog_post():
    data = request.get_json() or {}
    if not data.get('title'):
        return json_response(False, message='Başlık zorunludur.', status=400)
    slug = data.get('slug') or slugify(data['title'])
    if BlogPost.query.filter_by(slug=slug).first():
        return json_response(False, message='Bu slug zaten mevcut.', status=400)
    post = BlogPost(
        title=data['title'],
        slug=slug,
        summary=data.get('summary', ''),
        content=data.get('content', ''),
        cover_image=data.get('cover_image'),
        category=data.get('category', ''),
        author=data.get('author', ''),
        published_at=data.get('published_at') or None,
        is_active=data.get('is_active', True)
    )
    db.session.add(post)
    db.session.commit()
    return json_response(True, message='Blog yazısı oluşturuldu.', status=201)

@app.route('/api/blog/<int:post_id>', methods=['PUT'])
@admin_required
def update_blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    data = request.get_json() or {}
    if 'title' in data and data['title']:
        post.title = data['title']
        if 'slug' not in data:
            post.slug = slugify(data['title'])
    if 'slug' in data:
        post.slug = data['slug']
    if 'summary' in data:
        post.summary = data['summary']
    if 'content' in data:
        post.content = data['content']
    if 'cover_image' in data:
        post.cover_image = data['cover_image']
    if 'category' in data:
        post.category = data['category']
    if 'author' in data:
        post.author = data['author']
    if 'published_at' in data:
        post.published_at = data['published_at']
    if 'is_active' in data:
        post.is_active = data['is_active']
    db.session.commit()
    return json_response(True, message='Blog yazısı güncellendi.')

@app.route('/api/blog/<int:post_id>', methods=['DELETE'])
@admin_required
def delete_blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    if post.cover_image:
        delete_image(post.cover_image)
    db.session.delete(post)
    db.session.commit()
    return json_response(True, message='Blog yazısı silindi.')

# Başvurular
@app.route('/api/applications', methods=['POST'])
def create_application():
    data = request.get_json() or {}
    if not data.get('name') or not data.get('surname'):
        return json_response(False, message='Ad ve soyad zorunludur.', status=400)
    app = Application(
        name=data['name'],
        surname=data['surname'],
        phone=data.get('phone'),
        email=data.get('email'),
        age=int(data['age']) if data.get('age') else None,
        gender=data.get('gender'),
        height=float(data['height']) if data.get('height') else None,
        weight=float(data['weight']) if data.get('weight') else None,
        goal=data.get('goal'),
        activity_level=data.get('activity_level'),
        nutrition_preference=data.get('nutrition_preference'),
        allergies=data.get('allergies'),
        training_experience=data.get('training_experience'),
        environment=data.get('environment'),
        days_per_week=int(data['days_per_week']) if data.get('days_per_week') else None,
        note=data.get('note'),
        package_id=int(data['package_id']) if data.get('package_id') else None,
        status=data.get('status', 'Bekliyor')
    )
    db.session.add(app)
    db.session.commit()
    return json_response(True, message='Başvuru alındı.', status=201)

@app.route('/api/applications', methods=['GET'])
@admin_required
def get_applications():
    apps = Application.query.order_by(Application.created_at.desc()).all()
    data = [{
        'id': a.id,
        'name': a.name,
        'surname': a.surname,
        'phone': a.phone,
        'email': a.email,
        'age': a.age,
        'goal': a.goal,
        'status': a.status,
        'note': a.note,
        'created_at': a.created_at.isoformat() if a.created_at else None
    } for a in apps]
    return json_response(True, data=data)

@app.route('/api/applications/<int:app_id>', methods=['PUT'])
@admin_required
def update_application(app_id):
    app = Application.query.get_or_404(app_id)
    data = request.get_json() or {}
    if 'status' in data:
        app.status = data['status']
    if 'note' in data:
        app.note = data['note']
    db.session.commit()
    return json_response(True, message='Başvuru güncellendi.')

@app.route('/api/applications/<int:app_id>', methods=['DELETE'])
@admin_required
def delete_application(app_id):
    app = Application.query.get_or_404(app_id)
    db.session.delete(app)
    db.session.commit()
    return json_response(True, message='Başvuru silindi.')

# Randevular
@app.route('/api/appointments', methods=['POST'])
def create_appointment():
    data = request.get_json() or {}
    if not data.get('date') or not data.get('time') or not data.get('name'):
        return json_response(False, message='Tarih, saat ve isim zorunludur.', status=400)
    apt = Appointment(
        date=parse_date(data['date']),
        time=parse_time(data['time']),
        name=data['name'],
        phone=data.get('phone'),
        email=data.get('email'),
        service=data.get('service'),
        note=data.get('note'),
        status=data.get('status', 'Bekliyor')
    )
    db.session.add(apt)
    db.session.commit()
    return json_response(True, message='Randevu talebi alındı.', status=201)

@app.route('/api/appointments', methods=['GET'])
@admin_required
def get_appointments():
    apts = Appointment.query.order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    data = [{
        'id': a.id,
        'date': a.date.isoformat() if a.date else None,
        'time': a.time.strftime('%H:%M') if a.time else None,
        'name': a.name,
        'phone': a.phone,
        'email': a.email,
        'service': a.service,
        'note': a.note,
        'status': a.status,
        'created_at': a.created_at.isoformat() if a.created_at else None
    } for a in apts]
    return json_response(True, data=data)

@app.route('/api/appointments/<int:apt_id>', methods=['PUT'])
@admin_required
def update_appointment(apt_id):
    apt = Appointment.query.get_or_404(apt_id)
    data = request.get_json() or {}
    if 'date' in data:
        apt.date = parse_date(data['date'])
    if 'time' in data:
        apt.time = parse_time(data['time'])
    if 'name' in data:
        apt.name = data['name']
    if 'phone' in data:
        apt.phone = data['phone']
    if 'email' in data:
        apt.email = data['email']
    if 'service' in data:
        apt.service = data['service']
    if 'note' in data:
        apt.note = data['note']
    if 'status' in data:
        apt.status = data['status']
    db.session.commit()
    return json_response(True, message='Randevu güncellendi.')

@app.route('/api/appointments/<int:apt_id>', methods=['DELETE'])
@admin_required
def delete_appointment(apt_id):
    apt = Appointment.query.get_or_404(apt_id)
    db.session.delete(apt)
    db.session.commit()
    return json_response(True, message='Randevu silindi.')

# Site ayarları ve sosyal linkler
@app.route('/api/site-settings', methods=['GET'])
def get_site_settings():
    settings = {}
    for s in SiteSetting.query.all():
        settings[s.key] = s.value
    social = {link.platform: link.url for link in SocialLink.query.all()}
    data = {**settings, 'social': social}
    return json_response(True, data=data)

@app.route('/api/site-settings', methods=['PUT'])
@admin_required
def update_site_settings():
    data = request.get_json() or {}
    allowed_keys = {'site_name', 'logo_url', 'favicon_url', 'hero_title', 'hero_description',
                    'footer_text', 'phone', 'email', 'address', 'about_text'}
    for key, value in data.items():
        if key in allowed_keys:
            setting = SiteSetting.query.filter_by(key=key).first()
            if setting:
                setting.value = str(value)
            else:
                setting = SiteSetting(key=key, value=str(value))
                db.session.add(setting)
    db.session.commit()
    return json_response(True, message='Site ayarları güncellendi.')

@app.route('/api/social-links', methods=['GET'])
def get_social_links():
    links = SocialLink.query.all()
    return json_response(True, data={link.platform: link.url for link in links})

@app.route('/api/social-links', methods=['PUT'])
@admin_required
def update_social_links():
    data = request.get_json() or {}
    allowed_platforms = {'instagram', 'tiktok', 'youtube', 'whatsapp', 'email'}
    for platform, url in data.items():
        if platform in allowed_platforms:
            link = SocialLink.query.filter_by(platform=platform).first()
            if link:
                link.url = str(url)
            else:
                link = SocialLink(platform=platform, url=str(url))
                db.session.add(link)
    db.session.commit()
    return json_response(True, message='Sosyal medya linkleri güncellendi.')

# Medya
@app.route('/api/media', methods=['GET'])
@admin_required
def get_media():
    media = Media.query.order_by(Media.uploaded_at.desc()).all()
    data = [{
        'id': m.id,
        'filename': m.filename,
        'filepath': m.filepath,
        'filetype': m.filetype,
        'url': f"/media/{m.filepath.lstrip('/')}",
        'uploaded_at': m.uploaded_at.isoformat() if m.uploaded_at else None
    } for m in media]
    return json_response(True, data=data)

@app.route('/api/media/upload', methods=['POST'])
@admin_required
def upload_media():
    folder = request.form.get('folder', 'general')
    if folder not in ['packages', 'events', 'blog', 'profile', 'general']:
        folder = 'general'
    if 'image_base64' in request.form:
        base64_str = request.form['image_base64']
        data_bytes, ext = validate_image(base64_str)
        if data_bytes is None:
            return json_response(False, message=ext, status=400)
        filepath = save_image(data_bytes, folder=folder, extension=ext, filename_prefix='upload')
    elif 'file' in request.files:
        file = request.files['file']
        if not file:
            return json_response(False, message='Dosya seçilmedi.', status=400)
        data_bytes, ext = validate_image(file, file.filename)
        if data_bytes is None:
            return json_response(False, message=ext, status=400)
        filepath = save_image(data_bytes, folder=folder, extension=ext, filename_prefix='upload')
    else:
        return json_response(False, message='Dosya veya Base64 verisi gerekli.', status=400)
    media = Media(filename=filepath.split('/')[-1], filepath=filepath, filetype=ext)
    db.session.add(media)
    db.session.commit()
    return json_response(True, data={'url': f"/media/{filepath.lstrip('/')}", 'filepath': filepath}, message='Görsel yüklendi.', status=201)

@app.route('/api/media/<int:media_id>', methods=['DELETE'])
@admin_required
def delete_media(media_id):
    media = Media.query.get_or_404(media_id)
    delete_image(media.filepath)
    db.session.delete(media)
    db.session.commit()
    return json_response(True, message='Görsel silindi.')

# Satın alma
@app.route('/api/purchase', methods=['POST'])
def create_purchase():
    data = request.get_json() or {}
    if not data.get('name') or not data.get('surname') or not data.get('email') or not data.get('package_id'):
        return json_response(False, message='Ad, soyad, e-posta ve paket bilgisi zorunludur.', status=400)
    if not validate_email(data['email']):
        return json_response(False, message='Geçerli bir e-posta adresi girin.', status=400)
    package = Package.query.get(data['package_id'])
    if not package:
        return json_response(False, message='Paket bulunamadı.', status=404)
    purchase = Purchase(
        name=data['name'],
        surname=data['surname'],
        email=data['email'],
        package_id=package.id,
        package_name=package.name,
        price=package.price,
        note=data.get('note', ''),
        status='Bekliyor'
    )
    db.session.add(purchase)
    db.session.commit()

    subject = f"Yeni Satın Alma Talebi: {package.name}"
    body = f"""Yeni satın alma talebi alındı.

Müşteri Bilgileri:
- Ad Soyad: {data['name']} {data['surname']}
- E-posta: {data['email']}
- Not: {data.get('note', 'Belirtilmedi')}

Paket Bilgileri:
- Paket Adı: {package.name}
- Kategori: {package.category}
- Fiyat: ₺{package.price}
- Süre: {package.duration or 'Belirtilmedi'}

Tarih: {datetime.utcnow().strftime('%d.%m.%Y %H:%M')}
"""
    send_email(NOTIFICATION_EMAIL, subject, body)

    return json_response(True, message='Satın alma talebiniz alındı. En kısa sürede size dönüş yapılacaktır.', status=201)

@app.route('/api/purchases', methods=['GET'])
@admin_required
def get_purchases():
    purchases = Purchase.query.order_by(Purchase.created_at.desc()).all()
    data = [{
        'id': p.id,
        'name': p.name,
        'surname': p.surname,
        'email': p.email,
        'package_name': p.package_name,
        'price': p.price,
        'note': p.note,
        'status': p.status,
        'created_at': p.created_at.isoformat() if p.created_at else None
    } for p in purchases]
    return json_response(True, data=data)

# Dashboard
@app.route('/api/dashboard', methods=['GET'])
@admin_required
def dashboard():
    total_packages = Package.query.count()
    active_packages = Package.query.filter_by(is_active=True).count()
    total_events = Event.query.count()
    active_events = Event.query.filter_by(is_active=True).count()
    total_applications = Application.query.count()
    pending_applications = Application.query.filter_by(status='Bekliyor').count()
    total_appointments = Appointment.query.count()
    pending_appointments = Appointment.query.filter_by(status='Bekliyor').count()
    total_blog = BlogPost.query.count()
    total_purchases = Purchase.query.count()
    pending_purchases = Purchase.query.filter_by(status='Bekliyor').count()
    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_applications = Application.query.filter(Application.created_at >= week_ago).count()
    return json_response(True, data={
        'total_packages': total_packages,
        'active_packages': active_packages,
        'total_events': total_events,
        'active_events': active_events,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'total_blog': total_blog,
        'total_purchases': total_purchases,
        'pending_purchases': pending_purchases,
        'weekly_applications': weekly_applications
    })

# Medya servisi
@app.route('/media/<path:filename>')
def serve_media(filename):
    return send_from_directory(PHOTO_ROOT, filename)

# Statik dosyalar
@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if path.startswith('api/') or path.startswith('media/'):
        return json_response(False, message='Not found', status=404)
    file_path = BASE_DIR / path
    if file_path.exists() and file_path.is_file():
        return send_from_directory(BASE_DIR, path)
    if path.endswith('.html'):
        return send_from_directory(BASE_DIR, path)
    return json_response(False, message='Not found', status=404)

@app.errorhandler(404)
def not_found(e):
    return json_response(False, message='Kaynak bulunamadı.', status=404)

@app.errorhandler(500)
def internal_error(e):
    return json_response(False, message='Sunucu hatası.', status=500)

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
else:
    with app.app_context():
        init_db()