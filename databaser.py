import sqlite3
import os
import time
from werkzeug.utils import secure_filename

DATABASE = 'database.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    password TEXT,
                    image TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER,
                    title TEXT,
                    description TEXT,
                    likes INTEGER DEFAULT 0,
                    dislikes INTEGER DEFAULT 0,
                    timestamp INTEGER,
                    FOREIGN KEY(channel_id) REFERENCES channels(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER,
                    channel_id INTEGER,
                    comment TEXT,
                    timestamp INTEGER,
                    FOREIGN KEY(video_id) REFERENCES videos(id),
                    FOREIGN KEY(channel_id) REFERENCES channels(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_reactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER,
                    channel_id INTEGER,
                    reaction TEXT,
                    FOREIGN KEY(video_id) REFERENCES videos(id),
                    FOREIGN KEY(channel_id) REFERENCES channels(id))''')
    conn.commit()
    conn.close()

def get_videos():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, title, description, likes, dislikes, timestamp, channel_id FROM videos ORDER BY (likes - dislikes) DESC')
    videos = c.fetchall()
    conn.close()
    return videos

def get_video(video_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, title, description, likes, dislikes, timestamp, channel_id FROM videos WHERE id=?', (video_id,))
    video = c.fetchone()
    conn.close()
    return video

def toggle_like(video_id, channel_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM user_reactions WHERE video_id=? AND channel_id=?', (video_id, channel_id))
    reaction = c.fetchone()
    if reaction:
        if reaction[3] == 'like':
            c.execute('DELETE FROM user_reactions WHERE video_id=? AND channel_id=?', (video_id, channel_id))
            c.execute('UPDATE videos SET likes = likes - 1 WHERE id=?', (video_id,))
        else:
            c.execute('UPDATE user_reactions SET reaction=? WHERE video_id=? AND channel_id=?', ('like', video_id, channel_id))
            c.execute('UPDATE videos SET likes = likes + 1, dislikes = dislikes - 1 WHERE id=?', (video_id,))
    else:
        c.execute('INSERT INTO user_reactions (video_id, channel_id, reaction) VALUES (?, ?, ?)', (video_id, channel_id, 'like'))
        c.execute('UPDATE videos SET likes = likes + 1 WHERE id=?', (video_id,))
    conn.commit()
    conn.close()

def toggle_dislike(video_id, channel_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM user_reactions WHERE video_id=? AND channel_id=?', (video_id, channel_id))
    reaction = c.fetchone()
    if reaction:
        if reaction[3] == 'dislike':
            c.execute('DELETE FROM user_reactions WHERE video_id=? AND channel_id=?', (video_id, channel_id))
            c.execute('UPDATE videos SET dislikes = dislikes - 1 WHERE id=?', (video_id,))
        else:
            c.execute('UPDATE user_reactions SET reaction=? WHERE video_id=? AND channel_id=?', ('dislike', video_id, channel_id))
            c.execute('UPDATE videos SET dislikes = dislikes + 1, likes = likes - 1 WHERE id=?', (video_id,))
    else:
        c.execute('INSERT INTO user_reactions (video_id, channel_id, reaction) VALUES (?, ?, ?)', (video_id, channel_id, 'dislike'))
        c.execute('UPDATE videos SET dislikes = dislikes + 1 WHERE id=?', (video_id,))
    conn.commit()
    conn.close()

def create_channel(channel_name, password, image_file):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    image_filename = secure_filename(image_file.filename)
    image_path = os.path.join('static/channels', image_filename)
    image_file.save(image_path)
    c.execute('INSERT INTO channels (name, password, image) VALUES (?, ?, ?)', (channel_name, password, image_filename))
    conn.commit()
    conn.close()

def login_channel(channel_name, password):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM channels WHERE name=? AND password=?', (channel_name, password))
    channel = c.fetchone()
    conn.close()
    return channel is not None

def get_channel_by_name(channel_name):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, name, image FROM channels WHERE name=?', (channel_name,))
    channel = c.fetchone()
    conn.close()
    return channel

def upload_video(channel_name, title, description, video_file, preview_file):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id FROM channels WHERE name=?', (channel_name,))
    channel_id = c.fetchone()

    if channel_id is None:
        conn.close()
        raise ValueError("Channel not found")

    channel_id = channel_id[0]

    # Используем текущее время для создания уникального имени файла
    timestamp = int(time.time())
    video_filename = f"{channel_id}_{timestamp}.mp4"
    preview_filename = f"{channel_id}_{timestamp}.png"

    video_path = os.path.join('static/videos', video_filename)
    preview_path = os.path.join('static/previews', preview_filename)

    video_file.save(video_path)
    preview_file.save(preview_path)

    c.execute('INSERT INTO videos (channel_id, title, description, timestamp) VALUES (?, ?, ?, ?)', (channel_id, title, description, timestamp))
    video_id = c.lastrowid
    conn.commit()
    conn.close()

    return video_id

def edit_video(video_id, title, description, video_file, preview_file):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    if video_file:
        video_filename = f"{video_id}.mp4"
        video_path = os.path.join('static/videos', video_filename)
        video_file.save(video_path)

    if preview_file:
        preview_filename = f"{video_id}.png"
        preview_path = os.path.join('static/previews', preview_filename)
        preview_file.save(preview_path)

    c.execute('UPDATE videos SET title=?, description=? WHERE id=?', (title, description, video_id))
    conn.commit()
    conn.close()

def get_channel_videos(channel_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, title, description, likes, dislikes, timestamp FROM videos WHERE channel_id=?', (channel_id,))
    videos = c.fetchall()
    conn.close()
    return videos

def get_channel(channel_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, name, image FROM channels WHERE id=?', (channel_id,))
    channel = c.fetchone()
    conn.close()
    return channel

def get_total_likes(channel_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT SUM(likes) FROM videos WHERE channel_id=?', (channel_id,))
    total_likes = c.fetchone()[0]
    conn.close()
    return total_likes

def get_total_dislikes(channel_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT SUM(dislikes) FROM videos WHERE channel_id=?', (channel_id,))
    total_dislikes = c.fetchone()[0]
    conn.close()
    return total_dislikes

def add_comment(video_id, channel_id, comment):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    timestamp = int(time.time())
    c.execute('INSERT INTO comments (video_id, channel_id, comment, timestamp) VALUES (?, ?, ?, ?)', (video_id, channel_id, comment, timestamp))
    conn.commit()
    conn.close()

def get_comments(video_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT comments.id, comments.comment, comments.timestamp, channels.name, channels.image FROM comments JOIN channels ON comments.channel_id = channels.id WHERE comments.video_id=? ORDER BY comments.timestamp DESC', (video_id,))
    comments = c.fetchall()
    conn.close()
    return comments
