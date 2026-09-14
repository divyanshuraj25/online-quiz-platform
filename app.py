from flask import Flask, render_template, request, redirect, url_for
import json
import os
import sqlite3

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

QUESTIONS_FILE = os.path.join(BASE_DIR, "questions.json")
DATABASE_FILE = os.path.join(BASE_DIR, "quiz.db")


# =========================
# Load Default Questions
# =========================

with open(QUESTIONS_FILE, "r", encoding="utf-8") as file:
    quiz_data = json.load(file)


# =========================
# Database Connection
# =========================

def get_db_connection():
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    return connection


# =========================
# Create Database Tables
# =========================

def initialize_database():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
        )
    """)

    connection.commit()
    connection.close()


initialize_database()


# =========================
# Home Page
# =========================

@app.route("/")
def home():
    connection = get_db_connection()

    custom_quizzes = connection.execute("""
        SELECT * FROM quizzes
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    categories = list(quiz_data.keys())

    return render_template(
        "index.html",
        categories=categories,
        custom_quizzes=custom_quizzes
    )


# =========================
# Default Quiz Page
# =========================

@app.route("/quiz/<category>")
def quiz(category):
    if category not in quiz_data:
        return "Category not found", 404

    questions = quiz_data[category]

    return render_template(
        "quiz.html",
        quiz_title=f"{category} Quiz",
        questions=questions,
        quiz_type="default",
        quiz_id=category
    )


# =========================
# Custom Quiz Page
# =========================

@app.route("/custom-quiz/<int:quiz_id>")
def custom_quiz(quiz_id):
    connection = get_db_connection()

    quiz_details = connection.execute("""
        SELECT * FROM quizzes
        WHERE id = ?
    """, (quiz_id,)).fetchone()

    if quiz_details is None:
        connection.close()
        return "Custom quiz not found", 404

    database_questions = connection.execute("""
        SELECT * FROM questions
        WHERE quiz_id = ?
        ORDER BY id
    """, (quiz_id,)).fetchall()

    connection.close()

    questions = []

    for item in database_questions:
        questions.append({
            "question": item["question"],
            "options": [
                item["option_a"],
                item["option_b"],
                item["option_c"],
                item["option_d"]
            ],
            "answer": item["correct_option"]
        })

    return render_template(
        "quiz.html",
        quiz_title=quiz_details["title"],
        questions=questions,
        quiz_type="custom",
        quiz_id=quiz_id
    )


# =========================
# Create Quiz Page
# =========================

@app.route("/create-quiz")
def create_quiz():
    return render_template("create_quiz.html")


# =========================
# Save User-Created Quiz
# =========================

@app.route("/save-quiz", methods=["POST"])
def save_quiz():
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()

    if not title or not category:
        return "Quiz title and category are required", 400

    questions = []

    for number in range(1, 6):
        question_text = request.form.get(
            f"question_{number}", ""
        ).strip()

        option_a = request.form.get(
            f"option_a_{number}", ""
        ).strip()

        option_b = request.form.get(
            f"option_b_{number}", ""
        ).strip()

        option_c = request.form.get(
            f"option_c_{number}", ""
        ).strip()

        option_d = request.form.get(
            f"option_d_{number}", ""
        ).strip()

        correct_option = request.form.get(
            f"correct_option_{number}", ""
        ).strip()

        if not all([
            question_text,
            option_a,
            option_b,
            option_c,
            option_d,
            correct_option
        ]):
            return f"Question {number} ke saare fields bharna zaroori hai", 400

        questions.append({
            "question": question_text,
            "option_a": option_a,
            "option_b": option_b,
            "option_c": option_c,
            "option_d": option_d,
            "correct_option": correct_option
        })

    connection = get_db_connection()

    cursor = connection.execute("""
        INSERT INTO quizzes (title, category)
        VALUES (?, ?)
    """, (title, category))

    quiz_id = cursor.lastrowid

    for question in questions:
        connection.execute("""
            INSERT INTO questions (
                quiz_id,
                question,
                option_a,
                option_b,
                option_c,
                option_d,
                correct_option
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            quiz_id,
            question["question"],
            question["option_a"],
            question["option_b"],
            question["option_c"],
            question["option_d"],
            question["correct_option"]
        ))

    connection.commit()
    connection.close()

    return redirect(url_for("home"))


# =========================
# Default Quiz Result
# =========================

@app.route("/result/default/<category>", methods=["POST"])
def default_result(category):
    if category not in quiz_data:
        return "Category not found", 404

    questions = quiz_data[category]
    score = 0

    for index, question in enumerate(questions):
        selected_answer = request.form.get(
            f"question_{index}"
        )

        if selected_answer == question["answer"]:
            score += 1

    total_questions = len(questions)

    if total_questions > 0:
        percentage = (score / total_questions) * 100
    else:
        percentage = 0

    return render_template(
        "result.html",
        category=category,
        score=score,
        total=total_questions,
        percentage=percentage,
        quiz_type="default",
        quiz_id=category
    )


# =========================
# Custom Quiz Result
# =========================

@app.route("/result/custom/<int:quiz_id>", methods=["POST"])
def custom_result(quiz_id):
    connection = get_db_connection()

    quiz_details = connection.execute("""
        SELECT * FROM quizzes
        WHERE id = ?
    """, (quiz_id,)).fetchone()

    database_questions = connection.execute("""
        SELECT * FROM questions
        WHERE quiz_id = ?
        ORDER BY id
    """, (quiz_id,)).fetchall()

    connection.close()

    if quiz_details is None:
        return "Custom quiz not found", 404

    score = 0

    for index, question in enumerate(database_questions):
        selected_answer = request.form.get(
            f"question_{index}"
        )

        if selected_answer == question["correct_option"]:
            score += 1

    total_questions = len(database_questions)

    if total_questions > 0:
        percentage = (score / total_questions) * 100
    else:
        percentage = 0

    return render_template(
        "result.html",
        category=quiz_details["title"],
        score=score,
        total=total_questions,
        percentage=percentage,
        quiz_type="custom",
        quiz_id=quiz_id
    )


# =========================
# Run Application
# =========================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )