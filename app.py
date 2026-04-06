from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.exc import IntegrityError
import language_tool_python
import textstat
import re
from datetime import datetime

import os
import requests
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama-3.3-70b-versatile"

# Validate API Key on startup
if not GROQ_API_KEY:
    import warnings
    warnings.warn(
        "⚠️  GROQ_API_KEY is not set! Set it in environment variables. "
        "Chat and text simplification will not work until this is configured.\n"
        "For Render: Go to Dashboard → Settings → Environment → Add GROQ_API_KEY"
    )
# ---------------------------------------------------------
# Flask App Configuration
# ---------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key-change-in-production")

# Database Configuration - Supports SQLite (default) or AWS RDS
DB_TYPE = os.getenv('DB_TYPE', 'sqlite')

if DB_TYPE.lower() == 'mysql':
    # AWS RDS MySQL Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'admin')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'policy_helper_ai')
    DB_PORT = os.getenv('DB_PORT', 3306)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
elif DB_TYPE.lower() == 'postgresql':
    # AWS RDS PostgreSQL Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'policy_helper_ai')
    DB_PORT = os.getenv('DB_PORT', 5432)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
else:
    # Default SQLite Configuration (for development/small deployments)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# Email Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', True)
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)

# Validate email configuration on startup
if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
    import warnings
    warnings.warn(
        "⚠️  Email configuration incomplete! MAIL_USERNAME and MAIL_PASSWORD not set. "
        "Password reset functionality will not work until this is configured.\n"
        "For Render: Go to Dashboard → Settings → Environment → Add these variables:\n"
        "  MAIL_SERVER=smtp.gmail.com\n"
        "  MAIL_PORT=587\n"
        "  MAIL_USE_TLS=True\n"
        "  MAIL_USERNAME=your_email@gmail.com\n"
        "  MAIL_PASSWORD=your_app_password\n"
        "See RENDER_DEPLOYMENT.md for Gmail App Password setup."
    )

serializer = URLSafeTimedSerializer(app.secret_key)

# ---------------------------------------------------------
# Database Models
# ---------------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    reset_token = db.Column(db.String(256), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)

    activities = db.relationship('Activity', backref='user', lazy='dynamic')
    chat_conversations = db.relationship('ChatConversation', backref='user', lazy='dynamic', cascade='all, delete-orphan')

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

class ChatConversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    
    messages = db.relationship('ChatMessage', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ChatConversation {self.title}>'

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversation.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<ChatMessage {self.role}: {self.content[:50]}...>'

# ---------------------------------------------------------
# Utility: log activity
# ---------------------------------------------------------
def log_activity(user_obj_or_username, action, details=None):
    try:
        user = None
        if isinstance(user_obj_or_username, User):
            user = user_obj_or_username
        elif isinstance(user_obj_or_username, str):
            user = User.query.filter_by(username=user_obj_or_username).first()

        user_id = user.id if user else None

        if details:
            details = str(details)
            if len(details) > 1000:
                details = details[:1000] + " ...[truncated]"

        ip = request.remote_addr if request else None

        activity = Activity(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip
        )
        db.session.add(activity)
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Failed to log activity")

# ---------------------------------------------------------
# HOME / LANDING PAGE
# ---------------------------------------------------------
@app.route('/')
def home():
    if "username" in session:
        return redirect(url_for('index'))
    return render_template("landing.html")

# ---------------------------------------------------------
# REGISTER
# ---------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash("Username already exists. Choose another.", "danger")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("Email already registered. Use another or reset password.", "danger")
            return redirect(url_for('register'))

        hashed = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed,
            is_admin=(User.query.count() == 0)
        )

        db.session.add(new_user)

        try:
            db.session.commit()
            log_activity(new_user, "register", details=f"User registered with email {email}")
        except IntegrityError:
            db.session.rollback()
            flash("Registration failed due to duplicate data.", "danger")
            return redirect(url_for('register'))

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template("register.html")

# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid username or password.", "danger")
            log_activity(username, "login_failed", details=f"Failed login attempt for username: {username}")
            return redirect(url_for('login'))

        session['username'] = user.username
        session['is_admin'] = user.is_admin

        flash("Login successful!", "success")
        log_activity(user, "login", details=f"User logged in")
        if user.is_admin:
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('index'))

    return render_template("login.html")

# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------
@app.route('/logout')
def logout():
    username = session.get("username")
    session.clear()
    flash("Logged out successfully.", "success")
    log_activity(username, "logout", details="User logged out")
    return redirect(url_for('login'))

# ---------------------------------------------------------
# FORGOT PASSWORD
# ---------------------------------------------------------
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        try:
            email = request.form['email'].strip()
            user = User.query.filter_by(email=email).first()

            if user:
                token = serializer.dumps(email, salt="reset-password")
                user.reset_token = token
                db.session.commit()

                reset_url = url_for('reset_password', token=token, _external=True)

                # Check if email is configured
                if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
                    app.logger.warning("Email not configured. Password reset link: %s", reset_url)
                    flash(
                        "Email service not configured. "
                        "Please contact the administrator. "
                        "Reset link has been generated and logged.",
                        "warning"
                    )
                else:
                    msg = Message(
                        "Password Reset Request",
                        sender=app.config.get('MAIL_USERNAME'),
                        recipients=[email]
                    )
                    msg.body = f"Click here to reset your password:\n{reset_url}"
                    
                    try:
                        mail.send(msg)
                        flash("Reset link sent to your email.", "info")
                        app.logger.info(f"Password reset email sent to {email}")
                    except Exception as e:
                        app.logger.exception(f"Failed to send reset email to {email}: {str(e)}")
                        app.logger.info("Password reset link for %s: %s", email, reset_url)
                        flash(
                            "Could not send email. "
                            "Please check your email configuration or contact administrator.",
                            "warning"
                        )

                log_activity(user, "forgot_password", details="Password reset requested")
            else:
                flash("Email not registered.", "danger")
                log_activity(None, "forgot_password_unknown", details=f"Password reset requested for unknown email: {email}")

            return redirect(url_for('login'))
        
        except Exception as e:
            app.logger.exception(f"Error in forgot_password route: {str(e)}")
            flash("An error occurred. Please try again later.", "danger")
            return redirect(url_for('forgot_password'))

    return render_template("forgot_password.html")

# ---------------------------------------------------------
# RESET PASSWORD
# ---------------------------------------------------------
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt="reset-password", max_age=3600)
    except Exception:
        flash("Invalid or expired reset link.", "danger")
        log_activity(None, "reset_token_invalid", details=f"Invalid/expired token used: {token}")
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email, reset_token=token).first()

    if not user:
        flash("Invalid reset link.", "danger")
        log_activity(None, "reset_token_invalid_lookup", details=f"Token didn't match a user: {token}")
        return redirect(url_for('login'))

    if request.method == "POST":
        new_password = request.form['password']
        user.password_hash = generate_password_hash(new_password)
        user.reset_token = None
        db.session.commit()

        flash("Password reset successful!", "success")
        log_activity(user, "reset_password", details="User reset their password")
        return redirect(url_for('login'))

    return render_template("reset_password.html")

# ---------------------------------------------------------
# USER INDEX (Policy Simplifier) + user history sidebar
# ---------------------------------------------------------
@app.route('/index', methods=['GET', 'POST'])
def index():
    if "username" not in session:
        flash("Login required.", "danger")
        return redirect(url_for('login'))

    output = ""
    user_activities = []
    username = session.get('username')
    user = User.query.filter_by(username=username).first() if username else None

    if request.method == 'POST':
        text = request.form['policy'].strip()
        simplified = ml_simplify(text)
        readable = improve_readability(simplified)
        output = highlight_entities(readable)

        details_snippet = text[:800]
        if user:
            log_activity(user, "policy_simplify", details=f"Input snippet: {details_snippet}")
        else:
            log_activity(None, "policy_simplify_anonymous", details=f"Input snippet: {details_snippet}")

    # fetch last 10 ONLY policy-related activities for this user (no login/logout/register/etc.)
    if user:
        user_activities = Activity.query.filter(
            Activity.user_id == user.id,
            Activity.action.in_(["policy_simplify", "policy_simplify_anonymous"])
        ).order_by(Activity.timestamp.desc()).limit(10).all()

    return render_template("index.html", output=output, activities=user_activities, username=username)

# ---------------------------------------------------------
# Clear user's own activity history
# ---------------------------------------------------------
@app.route('/clear_history', methods=['POST'])
def clear_history():
    if "username" not in session:
        flash("Login required.", "danger")
        return redirect(url_for('login'))

    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('index'))

    try:
        Activity.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        flash("Your history was cleared.", "success")
        log_activity(user, "clear_history", details="User cleared their own history")
    except Exception:
        db.session.rollback()
        flash("Could not clear history. Try again.", "danger")

    return redirect(url_for('index'))

# ---------------------------------------------------------
# ADMIN PANEL
# ---------------------------------------------------------
@app.route('/admin')
def admin():
    if "username" not in session or not session.get("is_admin"):
        flash("Admin access only.", "danger")
        return redirect(url_for('login'))

    users = User.query.order_by(User.id.asc()).all()
    recent_activities = Activity.query.order_by(Activity.timestamp.desc()).limit(200).all()
    return render_template("Admin.html", users=users, activities=recent_activities)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if "username" not in session or not session.get("is_admin"):
        flash("Admin access only.", "danger")
        return redirect(url_for('login'))

    user = User.query.get(user_id)

    if user:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted.", "success")
        log_activity(None, "delete_user", details=f"Admin deleted user_id={user_id}, username={user.username}")
    else:
        flash("User not found.", "danger")

    return redirect(url_for('admin'))
@app.route("/chat")
def chat():
    if "username" not in session:
        flash("Login required.", "danger")
        return redirect(url_for('login'))
    return render_template("chat.html")

@app.route('/api/chat/conversations', methods=['GET'])
def get_conversations():
    """Get all chat conversations for logged in user"""
    if "username" not in session:
        return jsonify({"success": False, "error": "Login required"}), 401
    
    try:
        username = session.get('username')
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
        
        conversations = ChatConversation.query.filter_by(user_id=user.id).order_by(
            ChatConversation.updated_at.desc()
        ).all()
        
        conv_data = [{
            'id': conv.id,
            'title': conv.title,
            'created_at': conv.created_at.isoformat(),
            'updated_at': conv.updated_at.isoformat()
        } for conv in conversations]
        
        return jsonify({"success": True, "conversations": conv_data})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/chat/new', methods=['POST'])
def create_new_conversation():
    """Create a new chat conversation"""
    if "username" not in session:
        app.logger.warning("Attempt to create conversation without login")
        return jsonify({"success": False, "error": "Login required"}), 401
    
    try:
        username = session.get('username')
        app.logger.info(f"Creating conversation for user: {username}")
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            app.logger.error(f"User not found: {username}")
            return jsonify({"success": False, "error": "User not found"}), 404
        
        # Create new conversation with default title
        new_conversation = ChatConversation(
            user_id=user.id,
            title="New Chat"
        )
        db.session.add(new_conversation)
        db.session.commit()
        
        app.logger.info(f"Conversation created successfully (ID: {new_conversation.id})")
        
        return jsonify({
            "success": True,
            "conversation_id": new_conversation.id,
            "title": new_conversation.title
        })
    
    except Exception as e:
        db.session.rollback()
        app.logger.exception(f"Error creating conversation: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/chat/<int:conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    """Get all messages for a specific conversation"""
    if "username" not in session:
        return jsonify({"success": False, "error": "Login required"}), 401
    
    try:
        username = session.get('username')
        user = User.query.filter_by(username=username).first()
        
        conversation = ChatConversation.query.filter_by(
            id=conversation_id,
            user_id=user.id
        ).first()
        
        if not conversation:
            return jsonify({"success": False, "error": "Conversation not found"}), 404
        
        messages = ChatMessage.query.filter_by(
            conversation_id=conversation_id
        ).order_by(ChatMessage.created_at).all()
        
        msg_data = [{
            'id': msg.id,
            'role': msg.role,
            'content': msg.content,
            'created_at': msg.created_at.isoformat()
        } for msg in messages]
        
        return jsonify({
            "success": True,
            "conversation_id": conversation_id,
            "title": conversation.title,
            "messages": msg_data
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/chat/<int:conversation_id>/message', methods=['POST'])
def save_message(conversation_id):
    """Save a message to a conversation"""
    if "username" not in session:
        return jsonify({"success": False, "error": "Login required"}), 401
    
    try:
        username = session.get('username')
        user = User.query.filter_by(username=username).first()
        
        conversation = ChatConversation.query.filter_by(
            id=conversation_id,
            user_id=user.id
        ).first()
        
        if not conversation:
            return jsonify({"success": False, "error": "Conversation not found"}), 404
        
        data = request.get_json()
        role = data.get('role')  # 'user' or 'assistant'
        content = data.get('content')
        
        if not role or not content:
            return jsonify({"success": False, "error": "Missing role or content"}), 400
        
        message = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        db.session.add(message)
        
        # Update conversation title if it's the first user message
        if role == 'user' and conversation.title == "New Chat":
            # Use first 50 chars of message as title
            conversation.title = content[:50] + ("..." if len(content) > 50 else "")
        
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message_id": message.id,
            "conversation_title": conversation.title
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/chat/<int:conversation_id>/delete', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete a conversation"""
    if "username" not in session:
        return jsonify({"success": False, "error": "Login required"}), 401
    
    try:
        username = session.get('username')
        user = User.query.filter_by(username=username).first()
        
        conversation = ChatConversation.query.filter_by(
            id=conversation_id,
            user_id=user.id
        ).first()
        
        if not conversation:
            return jsonify({"success": False, "error": "Conversation not found"}), 404
        
        db.session.delete(conversation)
        db.session.commit()
        
        return jsonify({"success": True})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
@app.route('/api/explain', methods=['POST'])
def explain():
    try:
        # Check if API key is configured
        if not GROQ_API_KEY:
            return jsonify({
                "success": False, 
                "error": "GROQ API Key not configured. Contact administrator or set GROQ_API_KEY environment variable."
            }), 500
            
        data = request.get_json()
        query = data.get("query")

        if not query:
            return jsonify({"success": False, "error": "Query is empty"}), 400

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "user", "content": query}
            ],
            "temperature": 0.7
        }

        response = requests.post(GROQ_API_URL, json=payload, headers=headers)

        if response.status_code != 200:
            error_msg = response.text
            # Provide helpful error message for invalid API key
            if "invalid_api_key" in error_msg.lower():
                error_msg = "Invalid GROQ API Key. Check your GROQ_API_KEY environment variable."
            return jsonify({"success": False, "error": error_msg}), 500

        result = response.json()

        reply = result["choices"][0]["message"]["content"]

        return jsonify({
            "success": True,
            "explanation": reply
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
@app.route('/api/clear-history', methods=['POST'])
def clear_chat_history_api():
    try:
        return jsonify({
            "success": True
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
# ---------------------------------------------------------
# NLP MODEL + TOOLS (original logic)
# ---------------------------------------------------------
# Lazy load BART model only when needed (not at startup)
try:
    tool = language_tool_python.LanguageTool('en-US')
except Exception:
    tool = None
    app.logger.warning("language_tool_python unavailable (likely missing Java). Grammar correction disabled.")

LEXICAL_MAP = {
    "pursuant to": "under",
    "terminate": "end",
    "notwithstanding": "even if",
    "prior to": "before",
    "hereby": "",
    "in accordance with": "as per",
    "shall": "must",
    "thereof": "of it",
    "therein": "in it",
    "explicit consent": "clear permission",
    "processed": "used",
    "organization": "company",
    "applicable": "relevant",
    "commence": "start",
    "subsequent": "next",
    "compliance": "following rules",
    "authorization": "permission",
    "violation": "breaking rules",
    "regulation": "rule",
    "inception": "start",
    "intimate": "inform",
    "insurer": "insurance company",
    "rejection": "denial",
    "claim": "request for payment",
    "pre-existing diseases": "existing illnesses",
    "Information Technology Act, 2000": "Indian IT law (2000)",
    "Ministry of Electronics and Information Technology": "Electronics and IT Ministry (India)",
    "Reserve Bank of India": "RBI",
    "Central Government": "Indian Government",
    "state government": "local government",
    "Goods and Services Tax": "GST",
    "Companies Act": "Indian company law",
    "penal provisions": "punishments",
    "data fiduciary": "data handler",
    "adjudicating officer": "appointed officer",
    "Digital Personal Data Protection Act": "DPDP Act",
    "Bharatiya Nyaya Sanhita": "Indian criminal law code",
    "service level agreement": "SLA",
    "data subject": "person whose data is used",
    "privacy policy": "rules about data use",
    "data retention": "how long data is kept",
    "third-party vendors": "outside service providers",
    "cybersecurity": "online safety",
    "incident response": "problem handling",
    "disclosure": "sharing info",
    "intellectual property": "ownership of ideas",
    "source code": "main code of software",
    "non-performing asset": "bad loan",
    "financial institution": "bank or finance company",
    "Know Your Customer": "KYC",
    "mutual fund": "pooled investment",
    "creditworthiness": "ability to repay loans",
    "collateral": "security for loan",
    "monetary policy": "RBI money rules",
    "loan default": "failure to repay loan",
    "interest rate": "loan cost",
    "repo rate": "RBI lending rate",
    "base rate": "minimum bank loan rate",
    "statutory": "by law",
    "obligation": "duty",
    "jurisdiction": "legal area",
    "litigation": "legal case",
    "enforceable": "can be made to happen",
    "hereinafter": "from now on",
    "inter alia": "among others",
    "null and void": "invalid",
    "provision": "rule or part",
    "undertaking": "agreement or promise"
}

def simplify_lexically(text):
    for word, simple in LEXICAL_MAP.items():
        text = re.sub(rf'\b{re.escape(word)}\b', simple, text, flags=re.IGNORECASE)
    return text

def correct_grammar(text):
    if tool is None:
        return text
    return language_tool_python.utils.correct(text, tool.check(text))

def improve_readability(text):
    score = textstat.flesch_reading_ease(text)
    if score < 50:
        text += "\n\n(Note: This content may still be complex.)"
    return text

def ml_simplify(text):
    """Simplify text using Groq API instead of local BART model"""
    try:
        # Check if API key is configured
        if not GROQ_API_KEY:
            app.logger.warning("GROQ_API_KEY not configured. Falling back to lexical simplification.")
            return simplify_lexically(text)
        
        # Use Groq API for text simplification - more efficient than local model
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "user",
                    "content": f"""Please simplify and summarize the following text. Make it clear and easy to understand for a general audience. 
Keep the main points but use simpler language. Return only the simplified text without any additional commentary.

Text to simplify:
{text}"""
                }
            ],
            "temperature": 0.5,
            "max_tokens": 500
        }

        response = requests.post(GROQ_API_URL, json=payload, headers=headers)
        
        if response.status_code != 200:
            # Fallback to lexical simplification if API fails
            app.logger.warning(f"Groq API error for simplification: {response.text}")
            return simplify_lexically(text)

        result = response.json()
        simplified = result["choices"][0]["message"]["content"]
        
        # Apply additional simplifications
        simplified = simplify_lexically(simplified)
        simplified = correct_grammar(simplified)
        return simplified.strip()
        
    except Exception as e:
        app.logger.error(f"Error in ml_simplify: {e}")
        # Fallback - still provide some simplification without API
        return simplify_lexically(text)

def highlight_entities(text):
    # Dates, durations - Orange/Amber highlight
    text = re.sub(r'\b\d+\s+(?:hours?|days?|weeks?|months?|years?)\b',
                  r'<span style="background-color:rgba(217,119,6,0.25); color:#fbbf24; padding:2px 6px; border-radius:4px; font-weight:600;">\g<0></span>', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                  r'<span style="background-color:rgba(217,119,6,0.25); color:#fbbf24; padding:2px 6px; border-radius:4px; font-weight:600;">\g<0></span>', text)
    text = re.sub(r'\b\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{4}\b',
                  r'<span style="background-color:rgba(217,119,6,0.25); color:#fbbf24; padding:2px 6px; border-radius:4px; font-weight:600;">\g<0></span>', text, flags=re.IGNORECASE)

    # Currency - Blue highlight
    text = re.sub(r'\b(?:₹|Rs\.?|INR)\s?\d+(?:,\d{3})*(?:\.\d{2})?\b',
                  r'<span style="background-color:rgba(99,102,241,0.25); color:#818cf8; padding:2px 6px; border-radius:4px; font-weight:600;">\g<0></span>', text)
    text = re.sub(r'\b(?:₹|Rs\.?|INR)\s?[\d,]+(?:\.\d+)?\s?(lakh|crore)?\b', 
                  r'<span style="background-color:rgba(99,102,241,0.25); color:#818cf8; padding:2px 6px; border-radius:4px; font-weight:600;">\g<0></span>', text, flags=re.IGNORECASE)

    # Organizations - Pink highlight
    text = re.sub(r'\b(?:insurance company|RBI|SEBI|IRDAI|UIDAI|Ministry of [A-Za-z ]+|Government of India|Income Tax Department|Central Government|state government|company)\b',
                  r'<span style="background-color:rgba(190,24,93,0.25); color:#ec4899; padding:2px 6px; border-radius:4px; font-weight:600;">\g<0></span>', text, flags=re.IGNORECASE)

    # Proper nouns - Green highlight
    text = re.sub(r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b',
                  r'<span style="background-color:rgba(5,150,105,0.25); color:#10b981; padding:2px 6px; border-radius:4px; font-weight:600;">\g<0></span>', text)

    # Important keywords - Red highlight
    keywords = ['must', 'rule', 'act', 'law', 'permission', 'penalty', 'request for payment', 'denial']
    for word in keywords:
        text = re.sub(rf'\b({word})\b', r'<span style="background-color:rgba(239,68,68,0.25); color:#ff6b6b; padding:2px 6px; border-radius:4px; font-weight:600;">\1</span>', text, flags=re.IGNORECASE)

    return text.strip()

# ---------------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
