# TODO: refactor
"""
TODO API. Хранение задач в SQLite.
"""
from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "todos.db"


def query(sql, params=(), fetch=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    if fetch:
        result = [dict(r) for r in cur.fetchall()]
    else:
        result = cur.lastrowid
    conn.commit()
    conn.close()
    return result


def init():
    query("""CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        done INTEGER DEFAULT 0,
        created_at TEXT
    )""")


@app.route("/todos", methods=["GET"])
def list_todos():
    items = query("SELECT * FROM todos ORDER BY id DESC", fetch=True)
    return jsonify(items)


@app.route("/todos", methods=["POST"])
def add_todo():
    data = request.get_json()
    if not data or "title" not in data:
        return jsonify({"error": "title required"}), 400
    new_id = query(
        "INSERT INTO todos (title, created_at) VALUES (?, ?)",
        (data["title"], datetime.now().isoformat())
    )
    return jsonify({"id": new_id}), 201


@app.route("/todos/<int:tid>", methods=["PUT"])
def update_todo(tid):
    data = request.get_json()
    query("UPDATE todos SET done = ? WHERE id = ?", (int(data.get("done", 0)), tid))
    return jsonify({"ok": True})


@app.route("/todos/<int:tid>", methods=["DELETE"])
def delete_todo(tid):
    query("DELETE FROM todos WHERE id = ?", (tid,))
    return jsonify({"ok": True})


if __name__ == "__main__":
    init()
    app.run(port=5000)
