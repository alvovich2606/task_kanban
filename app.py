from flask import Flask, render_template, request, redirect, url_for, session
import db

app = Flask(__name__)
app.secret_key = 'kanban-secret-key-change-me'

TAG_COLORS = [
    '#e74c3c', '#e67e22', '#f1c40f', '#2ecc71',
    '#3498db', '#9b59b6', '#1abc9c', '#e91e63'
]


@app.route('/')
def index():
    tasks = db.get_all_tasks()
    todo = [t for t in tasks if t['status'] == 'todo']
    in_progress = [t for t in tasks if t['status'] == 'in_progress']
    done = [t for t in tasks if t['status'] == 'done']
    limit = session.get('limit', '')
    tag_presets = db.get_all_tag_presets()
    return render_template(
        'index.html',
        todo=todo,
        in_progress=in_progress,
        done=done,
        tag_colors=TAG_COLORS,
        tag_presets=tag_presets,
        limit=limit
    )


@app.route('/task', methods=['POST'])
def create():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    tag_texts = request.form.getlist('tag_text')
    tag_colors = request.form.getlist('tag_color')
    preset_ids = request.form.getlist('preset_tag')
    tags = []
    seen_texts = set()
    for text, color in zip(tag_texts, tag_colors):
        text = text.strip().lower()
        if text and text not in seen_texts:
            tags.append({'text': text, 'color': color})
            seen_texts.add(text)
        if len(tags) >= 5:
            break
    if len(tags) < 5:
        all_presets = db.get_all_tag_presets()
        for preset_id in preset_ids:
            preset = next((p for p in all_presets if str(p['id']) == preset_id), None)
            if preset and preset['text'] not in seen_texts:
                tags.append({'text': preset['text'], 'color': preset['color']})
                seen_texts.add(preset['text'])
            if len(tags) >= 5:
                break
    if title:
        db.create_task(title, description, tags)
    return redirect(url_for('index'))


@app.route('/task/<int:task_id>/move', methods=['POST'])
def move(task_id):
    status = request.form.get('status', '').strip()
    limit_str = request.form.get('limit', '').strip()

    if limit_str:
        session['limit'] = limit_str

    if status == 'in_progress':
        limit_val = int(limit_str) if limit_str.isdigit() else 0
        if limit_val > 0:
            current = db.count_tasks_by_status('in_progress')
            if current >= limit_val:
                return redirect(url_for('index'))

    if status in ('todo', 'in_progress', 'done'):
        db.update_task_status(task_id, status)
    return redirect(url_for('index'))


@app.route('/task/<int:task_id>/delete', methods=['POST'])
def delete(task_id):
    db.delete_task(task_id)
    return redirect(url_for('index'))


@app.route('/set-limit', methods=['POST'])
def set_limit():
    new_limit = request.form.get('limit', '').strip()
    old_limit = session.get('limit', '')

    if new_limit.isdigit():
        new_limit_int = int(new_limit)
        old_limit_int = int(old_limit) if old_limit.isdigit() else 999

        if new_limit_int < old_limit_int:
            in_progress_ids = db.get_in_progress_tasks_ordered_by_recent()
            excess = len(in_progress_ids) - new_limit_int
            if excess > 0:
                to_move_back = in_progress_ids[:excess]
                db.update_task_status_bulk(to_move_back, 'todo')

    session['limit'] = new_limit
    return redirect(url_for('index'))


if __name__ == '__main__':
    db.init_db()
    app.run(debug=True)