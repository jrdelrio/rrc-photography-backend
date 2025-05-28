import os
import sqlite3
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from dotenv import load_dotenv
import resend
from datetime import datetime

# Cargar variables de entorno
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://www.raimundodelrio.cl", "http://localhost:3000"]}})

RESEND_API_KEY = os.getenv("RESEND_API_KEY_CHILISITES")
resend.api_key = RESEND_API_KEY
DATABASE = os.path.join(os.path.dirname(__file__), 'photos.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/test-connection', methods=['GET'])
def test_connection():
    return jsonify({'message': 'RRC Photography API working perfectly! 🚀'})

@app.route('/galleries', methods=['GET'])
def get_all_galleries():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT galleries.id, galleries.name, photos.url
            FROM galleries
            JOIN photos ON photos.id = galleries.photo_id
        ''')
        galleries = [
            {'gallery_id': row[0], 'gallery_name': row[1], 'cover_photo_url': row[2]}
            for row in cursor.fetchall()
        ]
        return jsonify(galleries)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/carrousel', methods=['GET'])
def get_carrousel_images():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, url, alternative_text FROM photos WHERE carrousel = 1')
        images = [{'photo_id': row[0], 'photo_url': row[1], 'alternative_text': row[2]} for row in cursor.fetchall()]
        return jsonify(images)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/all_photos', methods=['GET'])
def get_all_photos():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM photos')
        photos = [
            {
                'id': row[0],
                'url': row[1],
                'carrousel': row[2],
                'gallery_id': row[3],
                'alternative_text': row[4]
            }
            for row in cursor.fetchall()
        ]
        return jsonify(photos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/photos_from_<gallery_name>', methods=['GET'])
def get_photos_from_gallery(gallery_name):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT galleries.photo_id, photos.id, photos.url, photos.alternative_text
            FROM photos
            JOIN galleries ON photos.gallery_id = galleries.id
            WHERE galleries.name = ?
        ''', (gallery_name,))
        rows = cursor.fetchall()
        response = {
            "cover_photo": rows[0][2] if rows else "",
            "gallery_photos": [
                {
                    'photo_id': row[1],
                    'photo_url': row[2],
                    'alternative_text': row[3]
                } for row in rows
            ]
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/send-thanks-email', methods=['POST'])
def send_thanks_email():
    try:
        data = request.json
        file_path = os.path.join("templates", "thanks-email.html")
        with open(file_path, "r", encoding="utf-8") as file:
            html = file.read()
            html = html.replace("{{from_name}}", data.get("fromName", ""))
            html = html.replace("{{from_email}}", data.get("fromEmail", ""))
            html = html.replace("{{from_phone}}", data.get("fromPhone", ""))
            html = html.replace("{{from_message}}", data.get("fromMessage", ""))

        email = resend.Emails.send({
            "from": "Raimundo del Rio <contacto@chilisites.com>",
            "to": data["fromEmail"],
            "subject": "¡Gracias por tu mensaje y por visitar mi portafolio! 🌟",
            "html": html
        })
        return jsonify({"status": "success", "email": email})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/send-intern-email', methods=['POST'])
def send_intern_email():
    try:
        data = request.json
        file_path = os.path.join("templates", "intern-email.html")
        with open(file_path, "r", encoding="utf-8") as file:
            html = file.read()
            html = html.replace("{{from_name}}", data.get("fromName", ""))
            html = html.replace("{{from_email}}", data.get("fromEmail", ""))
            html = html.replace("{{from_phone}}", data.get("fromPhone", ""))
            html = html.replace("{{from_message}}", data.get("fromMessage", ""))
            html = html.replace("{{timestamp}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        email = resend.Emails.send({
            "from": "Raimundo del Rio <contacto@chilisites.com>",
            "to": "rdelrio62@gmail.com",
            "subject": "📩 Nuevo mensaje desde tu portafolio web",
            "html": html
        })
        return jsonify({"status": "success", "email": email})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
