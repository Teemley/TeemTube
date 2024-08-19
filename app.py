from flask import Flask, render_template, request, redirect, url_for, session
from databaser import init_db, get_videos, get_video, toggle_like, toggle_dislike, create_channel, login_channel, upload_video, edit_video, get_channel_videos, get_channel, get_total_likes, get_total_dislikes, get_channel_by_name, add_comment, get_comments
import random

app = Flask(__name__)
app.secret_key = 'supersecretkey'

@app.route('/')
def index():
    videos = get_videos()
    random_videos = random.sample(videos, min(5, len(videos)))
    return render_template('index.html', videos=videos, random_videos=random_videos)

@app.route('/video/<int:video_id>', methods=['GET', 'POST'])
def video(video_id):
    video_data = get_video(video_id)
    channel_data = get_channel(video_data[6])  # Получаем данные канала
    comments = get_comments(video_id)
    if request.method == 'POST':
        comment = request.form['comment']
        if 'channel_id' not in session:
            return redirect(url_for('login'))
        add_comment(video_id, session['channel_id'], comment)
        return redirect(url_for('video', video_id=video_id))
    return render_template('video.html', video=video_data, channel=channel_data, comments=comments)

@app.route('/like/<int:video_id>')
def like(video_id):
    if 'channel_id' not in session:
        return redirect(url_for('login'))
    toggle_like(video_id, session['channel_id'])
    return redirect(url_for('video', video_id=video_id))

@app.route('/dislike/<int:video_id>')
def dislike(video_id):
    if 'channel_id' not in session:
        return redirect(url_for('login'))
    toggle_dislike(video_id, session['channel_id'])
    return redirect(url_for('video', video_id=video_id))

@app.route('/create_channel', methods=['GET', 'POST'])
def create_channel_route():
    if request.method == 'POST':
        channel_name = request.form['channel_name']
        password = request.form['password']
        image_file = request.files['image_file']
        create_channel(channel_name, password, image_file)
        return redirect(url_for('index'))
    return render_template('create_channel.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        channel_name = request.form['channel_name']
        password = request.form['password']
        channel = get_channel_by_name(channel_name)  # Получаем данные канала по имени
        if channel and login_channel(channel_name, password):
            session['channel_name'] = channel_name
            session['channel_image'] = channel[2]  # Сохраняем изображение канала в сессии
            session['channel_id'] = channel[0]  # Сохраняем ID канала в сессии
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/upload_video', methods=['GET', 'POST'])
def upload_video_route():
    if 'channel_name' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        video_file = request.files['video_file']
        preview_file = request.files['preview_file']
        try:
            video_id = upload_video(session['channel_name'], title, description, video_file, preview_file)
            return redirect(url_for('video', video_id=video_id))
        except ValueError as e:
            return render_template('upload_video.html', error=str(e))
    return render_template('upload_video.html')

@app.route('/edit_video/<int:video_id>', methods=['GET', 'POST'])
def edit_video_route(video_id):
    if 'channel_name' not in session:
        return redirect(url_for('login'))
    video_data = get_video(video_id)
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        video_file = request.files.get('video_file')
        preview_file = request.files.get('preview_file')
        edit_video(video_id, title, description, video_file, preview_file)
        return redirect(url_for('video', video_id=video_id))
    return render_template('edit_video.html', video=video_data)

@app.route('/channel/<int:channel_id>')
def channel(channel_id):
    channel_data = get_channel(channel_id)
    videos = get_channel_videos(channel_id)
    total_likes = get_total_likes(channel_id)
    total_dislikes = get_total_dislikes(channel_id)
    return render_template('channel.html', channel=channel_data, videos=videos, total_likes=total_likes, total_dislikes=total_dislikes)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
