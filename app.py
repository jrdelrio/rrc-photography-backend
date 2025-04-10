import os
import sqlite3
from flask import Flask, request, jsonify, g
from flask_cors import CORS
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, text
from dotenv import load_dotenv
import resend
from datetime import datetime

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__)


CORS(app, resources={r"/*": {"origins": "https://www.raimundodelrio.cl"}})

# app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key')

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
DATABASE = os.path.join(os.path.dirname(__file__), 'photos.db')

def get_db():
    """Establece la conexión con la base de datos y la reutiliza en cada petición"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.route('/test-connection', methods=['GET'])
def test_connection():
    print("✅ Connection test endpoint hit")
    connection = False
    if get_db:
        connection = True

    response = {
        'message': 'RRC Photography API working perfectly! 🚀'}
    
    return jsonify(response)

@app.route('/galleries', methods=['GET'])
def get_all_galleries():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
                    SELECT 
                        galleries.id AS gallery_id,
                        galleries.name AS gallery_name,
                        photos.url AS cover_photo_url
                    FROM 
                        galleries
                    JOIN 
                        photos ON photos.id = galleries.photo_id;
                       ''')
        # Convertimos cada registro en un diccionario con las keys esperadas
        galleries = [
            {
                'gallery_id': row[0],
                'gallery_name': row[1], 
                'cover_photo_url': row[2]
            }  
            for row in cursor.fetchall()
        ]
        
        return jsonify(galleries)
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # 500 para indicar error de servidor interno

@app.route('/carrousel', methods=['GET'])
def get_carrousel_images():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
                    SELECT 
                        id, url, alternative_text
                    FROM 
                        PHOTOS
                    WHERE
                        carrousel = 1;
                       ''')
        
        # Almacena los resultados de fetchall() en una variable y úsala
        rows = cursor.fetchall()
        print("Filas:", rows)

        # Crear la lista con los resultados
        carrousel_images = [
            {
                'photo_id': row[0],
                'photo_url': row[1],
                'alternative_text': row[2]
            }
            for row in rows
        ]
        
        return jsonify(carrousel_images)
    except Exception as e:
        return jsonify({'error': 'Error al obtener imagenes del carrousel', 'details': str(e)}), 500

@app.route('/all_photos', methods=['GET'])
def get_all_photos():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM photos;')
        
        respuesta = cursor.fetchall()
        
        photos = [
            {
                'id': row[0],
                'url': row[1],
                'carrousel': row[2],
                'gallery_id': row[3],
                'alternative_text': row[4]
            }
            for row in respuesta
            
        ]
        
        return jsonify(photos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # 500 para indicar error de servidor interno

@app.route('/photos_from_<gallery_name>', methods=['GET'])
def get_photos_from_gallery(gallery_name):
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT
                GALLERIES.photo_id,
                PHOTOS.id,
                PHOTOS.url,
                PHOTOS.alternative_text
            FROM
                PHOTOS
            JOIN
                GALLERIES ON PHOTOS.gallery_id = GALLERIES.id
            WHERE
                GALLERIES.name = ?;
        ''', (gallery_name,))

        
        respuesta = cursor.fetchall()
        # print("Respuesta completa:", respuesta)
        
        return_json = {"cover_photo": respuesta[0][2]}

        # Convertimos cada registro en un diccionario con las keys esperadas
        photos = [
            {
                'photo_id': row[1],
                'photo_url': row[2],
                'alternative_text': row[3]
            }
            for row in respuesta
        ]
        
        return_json['gallery_photos'] = photos
        
        return jsonify(return_json)
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # 500 para indicar error de servidor interno

@app.route("/send-thanks-email", methods=["POST"])
def send_email_to_leed():
    print("Endpoint /send-thanks-email hit")
    try:
        resend.api_key = RESEND_API_KEY
        data = request.json
        
        file_path = os.path.join(os.path.dirname(__file__), "templates", "thanks-email.html")
        
        with open(file_path, "r", encoding="utf-8") as file:
            email_template = file.read()
            email_template = email_template.replace("{{from_name}}", data.get("fromName", ""))
            email_template = email_template.replace("{{from_email}}", data.get("fromEmail", ""))
            email_template = email_template.replace("{{from_phone}}", data.get("fromPhone", ""))
            email_template = email_template.replace("{{from_message}}", data.get("fromMessage", ""))
            
        
        params: resend.Emails.SendParams = {
            "from": "Raimundo del Rio <contacto@chilisites.com>",
            "to": data["fromEmail"],
            "subject": "¡Gracias por tu mensaje y por visitar mi portafolio! 🌟",
            "html": email_template
        }
        
        email = resend.Emails.send(params)
            
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    
    return {"email": email}

@app.route("/send-intern-email", methods=["POST"])
def send_intern_email():
    print("Endpoint /send-intern-email hit")
    
    try:
        resend.api_key = RESEND_API_KEY
        data = request.json
        
        file_path = os.path.join(os.path.dirname(__file__), "templates", "intern-email.html")
        
        with open(file_path, "r", encoding="utf-8") as file:
            email_template = file.read()
            email_template = email_template.replace("{{from_name}}", data.get("fromName", ""))
            email_template = email_template.replace("{{from_email}}", data.get("fromEmail", ""))
            email_template = email_template.replace("{{from_phone}}", data.get("fromPhone", ""))
            email_template = email_template.replace("{{from_message}}", data.get("fromMessage", ""))
            email_template = email_template.replace("{{timestamp}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
        
        params: resend.Emails.SendParams = {
            "from": "Raimundo del Rio <contacto@chilisites.com>",
            "to": "rdelrio62@gmail.com",
            "subject": "📩 Nuevo mensaje desde tu portafolio web",
            "html": email_template
        }
        
        email = resend.Emails.send(params)
            
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    
    return {"email": email}
    

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5003)
