from flask import Flask, request, jsonify
from config import get_connection

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    proficiency_level = data.get('proficiency_level', 'beginner')
    learning_goal = data.get('learning_goal', 'general')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Users (username, password, email, proficiency_level, learning_goal) VALUES (?, ?, ?, ?, ?)",
                   (username, password, email, proficiency_level, learning_goal))
    conn.commit()
    conn.close()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM Users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row and row[1] == password:
        return jsonify({'message': 'Login successful', 'user_id': row[0]})
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/lessons/<language>/<level>', methods=['GET'])
def get_lessons(language, level):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content FROM Lessons WHERE language = ? AND level = ?", (language, level))
    lessons = [{'id': row[0], 'title': row[1], 'content': row[2]} for row in cursor.fetchall()]
    conn.close()
    return jsonify({'lessons': lessons})

@app.route('/complete_lesson', methods=['POST'])
def complete_lesson():
    data = request.json
    user_id = data.get('user_id')
    lesson_id = data.get('lesson_id')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO LessonProgress (user_id, lesson_id) VALUES (?, ?)", (user_id, lesson_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Lesson marked as completed'})

@app.route('/quizzes/<lesson_id>', methods=['GET'])
def get_quiz(lesson_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, question, options FROM Quizzes WHERE lesson_id = ?", (lesson_id,))
    quizzes = [{'id': row[0], 'question': row[1], 'options': row[2].split('|')} for row in cursor.fetchall()]
    conn.close()
    return jsonify({'quizzes': quizzes})

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    data = request.json
    user_id = data.get('user_id')
    quiz_id = data.get('quiz_id')
    selected_answer = data.get('selected_answer')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT correct_answer FROM Quizzes WHERE id = ?", (quiz_id,))
    row = cursor.fetchone()

    if row:
        correct = (selected_answer == row[0])
        cursor.execute("INSERT INTO UserProgress (user_id, quiz_id, selected_answer, is_correct) VALUES (?, ?, ?, ?)",
                       (user_id, quiz_id, selected_answer, int(correct)))
        conn.commit()
        conn.close()
        return jsonify({'correct': correct})
    return jsonify({'error': 'Quiz not found'}), 404

@app.route('/flashcards/<language>/<level>', methods=['GET'])
def get_flashcards(language, level):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, term, definition FROM Flashcards WHERE language = ? AND level = ?", (language, level))
    flashcards = [{'id': row[0], 'term': row[1], 'definition': row[2]} for row in cursor.fetchall()]
    conn.close()
    return jsonify({'flashcards': flashcards})

@app.route('/user_progress/<user_id>', methods=['GET'])
def get_user_progress(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Lessons completed
    cursor.execute("SELECT COUNT(*) FROM LessonProgress WHERE user_id = ?", (user_id,))
    lessons_done = cursor.fetchone()[0]

    # Quizzes attempted and correct
    cursor.execute("SELECT COUNT(*), SUM(is_correct) FROM UserProgress WHERE user_id = ?", (user_id,))
    quiz_stats = cursor.fetchone()
    total_quizzes = quiz_stats[0] or 0
    correct_answers = quiz_stats[1] or 0

    # Flashcards reviewed count (optional)
    # Skipped for now unless we implement flashcard progress table

    conn.close()
    return jsonify({
        'lessons_completed': lessons_done,
        'quizzes_attempted': total_quizzes,
        'correct_answers': correct_answers
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'Flask API is running'})


if __name__ == '__main__':
    app.run()
