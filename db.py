import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kanban.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql'), encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def get_all_tasks():
    conn = get_connection()
    tasks = conn.execute('SELECT * FROM tasks ORDER BY moved_at DESC').fetchall()
    result = []
    for task in tasks:
        task_dict = dict(task)
        task_dict['tags'] = json.loads(task_dict['tags'])
        result.append(task_dict)
    conn.close()
    return result


def get_task_by_id(task_id):
    conn = get_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if task:
        task_dict = dict(task)
        task_dict['tags'] = json.loads(task_dict['tags'])
        conn.close()
        return task_dict
    conn.close()
    return None


def create_task(title, description, tags):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO tasks (title, description, tags, moved_at) VALUES (?, ?, ?, datetime('now', 'localtime'))",
        (title, description, json.dumps(tags))
    )
    task_id = cursor.lastrowid
    for tag in tags:
        conn.execute(
            'INSERT OR IGNORE INTO tag_presets (text, color) VALUES (?, ?)',
            (tag['text'].lower(), tag['color'])
        )
    conn.commit()
    conn.close()
    return get_task_by_id(task_id)


def update_task_status(task_id, status):
    conn = get_connection()
    conn.execute(
        "UPDATE tasks SET status = ?, moved_at = datetime('now', 'localtime') WHERE id = ?",
        (status, task_id)
    )
    conn.commit()
    conn.close()
    return get_task_by_id(task_id)


def update_task_status_bulk(task_ids, status):
    conn = get_connection()
    for task_id in task_ids:
        conn.execute(
            "UPDATE tasks SET status = ?, moved_at = datetime('now', 'localtime') WHERE id = ?",
            (status, task_id)
        )
    conn.commit()
    conn.close()


def delete_task(task_id):
    conn = get_connection()
    conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()


def count_tasks_by_status(status):
    conn = get_connection()
    count = conn.execute('SELECT COUNT(*) FROM tasks WHERE status = ?', (status,)).fetchone()[0]
    conn.close()
    return count


def get_in_progress_tasks_ordered_by_recent():
    conn = get_connection()
    tasks = conn.execute(
        "SELECT id FROM tasks WHERE status = 'in_progress' ORDER BY moved_at DESC"
    ).fetchall()
    conn.close()
    return [t['id'] for t in tasks]


def get_all_tag_presets():
    conn = get_connection()
    presets = conn.execute('SELECT DISTINCT text, color, id FROM tag_presets ORDER BY text ASC').fetchall()
    conn.close()
    return [dict(p) for p in presets]