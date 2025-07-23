from flask import Flask, request, jsonify
from config import get_connection

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    try:
        username = data['username']
        password = data['password']
        email = data['email']
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {e.args[0]}'}), 400

    proficiency_level = data.get('proficiency_level', 'beginner')
    learning_goal = data.get('learning_goal', 'general')

    conn = get_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Users (username, password, email, proficiency_level) VALUES (?, ?, ?, ?)",
            (username, password, email, proficiency_level)
        )
        conn.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    try:
        username = data['username']
        password = data['password']
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {e.args[0]}'}), 400

    conn = get_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = conn.cursor()
    cursor.execute("SELECT user_id, password FROM Users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row and row[1] == password:
        return jsonify({'message': 'Login successful', 'user_id': row[0]})
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/lessons/<language>/<level>', methods=['GET'])
def get_lessons(language, level):
    conn = get_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.lesson_id, l.title, l.content 
        FROM Lessons l 
        JOIN Languages lang ON l.language_id = lang.language_id 
        WHERE lang.name = ? AND l.level = ?
    """, (language, level))
    
    lessons = [{'id': row[0], 'title': row[1], 'content': row[2]} for row in cursor.fetchall()]
    conn.close()
    return jsonify({'lessons': lessons})

@app.route('/complete_lesson', methods=['POST'])
def complete_lesson():
    data = request.json
    try:
        user_id = data['user_id']
        lesson_id = data['lesson_id']
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {e.args[0]}'}), 400

    conn = get_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO UserProgress (user_id, lesson_id, completed) VALUES (?, ?, 1)",
        (user_id, lesson_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Lesson marked as completed'})

@app.route('/quizzes/<int:lesson_id>', methods=['GET'])
def get_quiz(lesson_id):
    conn = get_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = conn.cursor()
    cursor.execute("""
        SELECT quiz_id, question, option_a, option_b, option_c, option_d 
        FROM Quizzes WHERE lesson_id = ?
    """, (lesson_id,))
    
    quizzes = [{
        'id': row[0],
        'question': row[1],
        'options': {
            'A': row[2],
            'B': row[3],
            'C': row[4],
            'D': row[5]
        }
    } for row in cursor.fetchall()]
    conn.close()
    return jsonify({'quizzes': quizzes})

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    data = request.json
    try:
        user_id = data['user_id']
        quiz_id = data['quiz_id']
        selected_answer = data['selected_answer']
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {e.args[0]}'}), 400

    conn = get_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = conn.cursor()
    cursor.execute("SELECT correct_option FROM Quizzes WHERE quiz_id = ?", (quiz_id,))
    row = cursor.fetchone()

    if row:
        correct = (selected_answer.upper() == row[0].upper())
        cursor.execute("""
            INSERT INTO UserProgress (user_id, lesson_id, completed) 
            VALUES (?, NULL, 0)
        """, (user_id,))
        conn.commit()
        conn.close()
        return jsonify({'correct': correct})
    else:
        conn.close()
        return jsonify({'error': 'Quiz not found'}), 404

@app.route('/flashcards/<language>', methods=['GET'])
def get_flashcards(language):
    conn = get_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.card_id, f.word, f.translation 
        FROM Flashcards f 
        JOIN Languages lang ON f.language_id = lang.language_id 
        WHERE lang.name = ?
    """, (language,))
    
    flashcards = [{'id': row[0], 'word': row[1], 'translation': row[2]} for row in cursor.fetchall()]
    conn.close()
    return jsonify({'flashcards': flashcards})

@app.route('/user_progress/<int:user_id>', methods=['GET'])
def get_user_progress(user_id):
    conn = get_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM UserProgress WHERE user_id = ? AND completed = 1", (user_id,))
    lessons_done = cursor.fetchone()[0]

    # Quiz stats not clearly tracked in your schema — assuming future expansion
    conn.close()
    return jsonify({
        'lessons_completed': lessons_done,
        'quizzes_attempted': 'Not implemented',
        'correct_answers': 'Not implemented'
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'Flask API is running'})

if __name__ == '__main__':
    app.run(debug=True)
