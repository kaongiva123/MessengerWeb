from flask import Flask, render_template, request, redirect, session, jsonify, url_for, flash
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super-secret-key-nebula' # Секретный ключ для сессий
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024 # Лимит 100МБ для видео PS: позже увеличу
UPLOAD_FOLDER = 'static/avatars'
CHAT_IMAGES_FOLDER = 'static/chat_images'
CHAT_VIDEOS_FOLDER = 'static/chat_videos'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CHAT_IMAGES_FOLDER'] = CHAT_IMAGES_FOLDER
app.config['CHAT_VIDEOS_FOLDER'] = CHAT_VIDEOS_FOLDER
DATABASE = '/root/Messenger-Flask/messenger.db'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(CHAT_IMAGES_FOLDER):
    os.makedirs(CHAT_IMAGES_FOLDER)
if not os.path.exists(CHAT_VIDEOS_FOLDER):
    os.makedirs(CHAT_VIDEOS_FOLDER)

def get_db_connection():
    conn = sqlite3.connect(DATABASE, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Убеждаемся, что колонка text может быть NULL или исправляем миграцию
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            avatar TEXT,
            bio TEXT,
            profile_video TEXT,
            last_typing TEXT,
            typing_with INTEGER,
            theme TEXT DEFAULT 'dark'
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_read INTEGER DEFAULT 0,
            msg_type TEXT DEFAULT 'text',
            file_path TEXT,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (receiver_id) REFERENCES users (id)
        )
    ''')
    
    # Миграция
    try:
        conn.execute("ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'dark'")
    except: pass
    try:
        conn.execute("ALTER TABLE users ADD COLUMN bio TEXT")
    except: pass
    try:
        conn.execute("ALTER TABLE users ADD COLUMN profile_video TEXT")
    except: pass
    try:
        conn.execute("ALTER TABLE users ADD COLUMN last_typing TEXT")
    except: pass
    try:
        conn.execute("ALTER TABLE users ADD COLUMN typing_with INTEGER")
    except: pass

    # Миграции для сообщений
    try:
        conn.execute('ALTER TABLE messages ADD COLUMN msg_type TEXT DEFAULT "text"')
    except: pass
    try:
        conn.execute('ALTER TABLE messages ADD COLUMN file_path TEXT')
    except: pass
    
    try:
        conn.execute('ALTER TABLE messages ADD COLUMN deleted_by_sender INTEGER DEFAULT 0')
    except: pass
    try:
        conn.execute('ALTER TABLE messages ADD COLUMN deleted_by_receiver INTEGER DEFAULT 0')
    except: pass
    
    # Миграция: добавляем колонки если их нет
    try:
        conn.execute('ALTER TABLE users ADD COLUMN last_typing TEXT')
        conn.execute('ALTER TABLE users ADD COLUMN typing_with INTEGER')
    except: pass
    
    try:
        conn.execute('ALTER TABLE messages ADD COLUMN is_read INTEGER DEFAULT 0')
    except: pass
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    search_query = request.args.get('q', '')
    my_id = session['user_id']
    
    conn = get_db_connection()
    
    # Общее количество непрочитанных сообщений для бейджа в меню
    total_unread = conn.execute('SELECT COUNT(*) FROM messages WHERE receiver_id = ? AND is_read = 0', (my_id,)).fetchone()[0]
    
    if search_query:
        # Поиск новых пользователей
        # ...

        # Поиск новых пользователей
        users = conn.execute(
            'SELECT id, username, avatar FROM users WHERE id != ? AND username LIKE ?', 
            (my_id, f'%{search_query}%')
        ).fetchall()
        is_search = True
    else:
        # Получаем список пользователей, с которыми уже есть переписка
        # Сортируем по времени последнего сообщения
        users = conn.execute('''
            SELECT DISTINCT u.id, u.username, u.avatar, 
            (SELECT msg_type FROM messages 
             WHERE (sender_id = u.id AND receiver_id = ?) 
                OR (sender_id = ? AND receiver_id = u.id)
             ORDER BY timestamp DESC LIMIT 1) as last_type,
            (SELECT text FROM messages 
             WHERE (sender_id = u.id AND receiver_id = ?) 
                OR (sender_id = ? AND receiver_id = u.id)
             ORDER BY timestamp DESC LIMIT 1) as last_msg,
            (SELECT timestamp FROM messages 
             WHERE (sender_id = u.id AND receiver_id = ?) 
                OR (sender_id = ? AND receiver_id = u.id)
             ORDER BY timestamp DESC LIMIT 1) as last_time,
            (SELECT COUNT(*) FROM messages 
             WHERE sender_id = u.id AND receiver_id = ? AND is_read = 0) as unread_count
            FROM users u
            JOIN messages m ON (m.sender_id = u.id AND m.receiver_id = ?) 
                            OR (m.sender_id = ? AND m.receiver_id = u.id)
            WHERE u.id != ?
            ORDER BY last_time DESC
        ''', (my_id, my_id, my_id, my_id, my_id, my_id, my_id, my_id, my_id, my_id)).fetchall()
        is_search = False
        
    current_user = conn.execute('SELECT * FROM users WHERE id = ?', (my_id,)).fetchone()
    conn.close()
    
    return render_template('index.html', 
                          users=users, 
                          current_user=current_user, 
                          search_query=search_query, 
                          is_search=is_search,
                          total_unread=total_unread)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            flash('Регистрация успешна! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Это имя пользователя уже занято.', 'error')
        finally:
            conn.close()
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль.', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/chat/<int:user_id>')
def chat(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    recipient = conn.execute('SELECT id, username, avatar FROM users WHERE id = ?', (user_id,)).fetchone()
    if not recipient:
        conn.close()
        return redirect(url_for('index'))
    
    current_user = conn.execute('SELECT id, username, avatar FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    return render_template('chat.html', recipient=recipient, current_user=current_user)

@app.route('/api/messages/<int:other_id>')
def get_messages(other_id):
    if 'user_id' not in session:
        return jsonify([]), 403
    
    my_id = session['user_id']
    conn = get_db_connection()
    
    # Помечаем сообщения как прочитанные
    conn.execute('UPDATE messages SET is_read = 1 WHERE sender_id = ? AND receiver_id = ?', (other_id, my_id))
    conn.commit()
    
    messages = conn.execute('''
        SELECT m.*, u.username as sender_name 
        FROM messages m 
        JOIN users u ON m.sender_id = u.id
        WHERE ((sender_id = ? AND receiver_id = ? AND deleted_by_sender = 0) 
           OR (sender_id = ? AND receiver_id = ?) AND (receiver_id = ? AND deleted_by_receiver = 0))
        ORDER BY timestamp ASC
    ''', (my_id, other_id, other_id, my_id, my_id)).fetchall()
    conn.close()
    
    return jsonify([dict(m) for m in messages])

@app.route('/api/typing', methods=['POST'])
def set_typing():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    recipient_id = data.get('recipient_id')
    
    conn = get_db_connection()
    # Используем строку для времени, чтобы избежать DeprecationWarning и проблем с типами
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    conn.execute('UPDATE users SET last_typing = ?, typing_with = ? WHERE id = ?', 
                 (now_str, recipient_id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/typing_status/<int:other_id>')
def get_typing_status(other_id):
    if 'user_id' not in session:
        return jsonify({'is_typing': False}), 403
    
    conn = get_db_connection()
    user = conn.execute('SELECT last_typing, typing_with FROM users WHERE id = ?', (other_id,)).fetchone()
    conn.close()
    
    if user and user['last_typing'] and user['typing_with'] == session['user_id']:
        try:
            last_typing = datetime.strptime(user['last_typing'], '%Y-%m-%d %H:%M:%S.%f')
            if (datetime.now() - last_typing).total_seconds() < 3:
                return jsonify({'is_typing': True})
        except ValueError: pass
            
    return jsonify({'is_typing': False})

@app.route('/api/send', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403
    
    sender_id = session['user_id']
    receiver_id = request.form.get('receiver_id')
    text = request.form.get('text', '')
    
    # Если данные пришли в JSON (старый метод)
    if not receiver_id and request.is_json:
        data = request.json
        receiver_id = data.get('receiver_id')
        text = data.get('text', '')

    if not receiver_id:
        return jsonify({'error': 'Missing receiver_id'}), 400

    conn = get_db_connection()
    
    # Проверяем, пришел ли файл
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename != '':
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            is_video = ext in ['mp4', 'mov', 'avi', 'webm']
            folder = app.config['CHAT_VIDEOS_FOLDER'] if is_video else app.config['CHAT_IMAGES_FOLDER']
            msg_type = 'video' if is_video else 'image'
            
            filename = secure_filename(f"{msg_type}_{datetime.now().timestamp()}_{file.filename}")
            file_path = os.path.join(folder, filename)
            file.save(file_path)
            
            conn.execute('INSERT INTO messages (sender_id, receiver_id, text, msg_type, file_path) VALUES (?, ?, ?, ?, ?)',
                         (sender_id, receiver_id, text, msg_type, filename))
            conn.commit()
            conn.close()
            return jsonify({'status': 'sent', 'type': msg_type})

    # Если это просто текст
    if text:
        conn.execute('INSERT INTO messages (sender_id, receiver_id, text, msg_type) VALUES (?, ?, ?, ?)',
                     (sender_id, receiver_id, text, 'text'))
        conn.commit()
    
    conn.close()
    return jsonify({'status': 'sent', 'type': 'text'})

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_bio = request.form.get('bio')
        avatar_file = request.files.get('avatar_file')
        video_file = request.files.get('video_file')
        theme = request.form.get('theme', 'dark')
        
        if new_username:
            try:
                conn.execute('UPDATE users SET username = ? WHERE id = ?', (new_username, session['user_id']))
                session['username'] = new_username
            except sqlite3.IntegrityError:
                flash('Это имя пользователя уже занято.', 'error')
        
        conn.execute('UPDATE users SET theme = ?, bio = ? WHERE id = ?', (theme, new_bio, session['user_id']))
        
        if avatar_file and avatar_file.filename != '':
            filename = secure_filename(f"user_{session['user_id']}_{avatar_file.filename}")
            avatar_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            conn.execute('UPDATE users SET avatar = ? WHERE id = ?', (filename, session['user_id']))

        if video_file and video_file.filename != '':
            filename = secure_filename(f"vid_{session['user_id']}_{video_file.filename}")
            video_file.save(os.path.join(app.config['CHAT_VIDEOS_FOLDER'], filename))
            conn.execute('UPDATE users SET profile_video = ? WHERE id = ?', (filename, session['user_id']))
            
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
        
    conn.close()
    return render_template('settings.html', user=user)

@app.route('/profile/<int:user_id>')
def profile(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT id, username, avatar, bio, profile_video, theme FROM users WHERE id = ?', (user_id,)).fetchone()
    current_user = conn.execute('SELECT theme FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    if not user:
        return redirect(url_for('index'))
        
    return render_template('profile.html', user=user, current_user=current_user)

@app.route('/api/theme', methods=['POST'])
def set_theme():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    theme = data.get('theme')
    if theme in ['dark', 'midnight', 'light']:
        conn = get_db_connection()
        conn.execute('UPDATE users SET theme = ? WHERE id = ?', (theme, session['user_id']))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    return jsonify({'error': 'Invalid theme'}), 400

@app.route('/api/delete_chat/<int:other_id>', methods=['POST'])
def delete_chat(other_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403
    
    my_id = session['user_id']
    conn = get_db_connection()
    # Удаляем сообщения только для текущего пользователя (или полностью из таблицы для обоих)
    # Обычно в простых чатах удаление чата удаляет сообщения из базы.
    conn.execute('DELETE FROM messages WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)', 
                 (my_id, other_id, other_id, my_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/delete_message', methods=['POST'])
def delete_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    msg_id = data.get('message_id')
    delete_type = data.get('mode') or data.get('type') # 'me' or 'both'
    my_id = session['user_id']
    
    if not msg_id:
        return jsonify({'error': 'Missing message_id'}), 400
    
    conn = get_db_connection()
    msg = conn.execute('SELECT * FROM messages WHERE id = ?', (msg_id,)).fetchone()
    
    if not msg:
        conn.close()
        return jsonify({'error': 'Message not found'}), 404
        
    is_sender = (msg['sender_id'] == my_id)
    is_receiver = (msg['receiver_id'] == my_id)
    
    if not is_sender and not is_receiver:
        conn.close()
        return jsonify({'error': 'Forbidden'}), 403
        
    if delete_type == 'both':
        if not is_sender:
            conn.close()
            return jsonify({'error': 'Denied'}), 403
        conn.execute('DELETE FROM messages WHERE id = ?', (msg_id,))
    else:
        if is_sender:
            conn.execute('UPDATE messages SET deleted_by_sender = 1 WHERE id = ?', (msg_id,))
        else:
            conn.execute('UPDATE messages SET deleted_by_receiver = 1 WHERE id = ?', (msg_id,))
            
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
