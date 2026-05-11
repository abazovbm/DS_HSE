"""
Простой блог на Flask с PostgreSQL.
"""
from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.secret_key = "dev_secret_key"

DB_CONFIG = {
    "host": "localhost",
    "database": "blog",
    "user": "postgres",
    "password": "postgres"
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


@app.route("/")
def index():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, body, created_at FROM posts ORDER BY created_at DESC")
    posts = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", posts=posts)


@app.route("/post/<int:post_id>")
def show_post(post_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT title, body, created_at FROM posts WHERE id = %s", (post_id,))
    post = cur.fetchone()
    cur.close()
    conn.close()
    if not post:
        flash("Пост не найден")
        return redirect(url_for("index"))
    return render_template("post.html", post=post)


@app.route("/create", methods=["GET", "POST"])
def create_post():
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO posts (title, body, created_at) VALUES (%s, %s, %s)",
            (title, body, datetime.now())
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("index"))
    return render_template("create.html")


if __name__ == "__main__":
    app.run(debug=True)
