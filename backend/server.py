import os
import time
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# Initialize database
def init_db():
    conn = sqlite3.connect('transcriptions.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transcriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            audio_url TEXT NOT NULL,
            language TEXT NOT NULL,
            vtt_content TEXT,
            plain_text TEXT,
            transcript_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create translations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transcription_id INTEGER NOT NULL,
            target_language TEXT NOT NULL,
            translated_text TEXT NOT NULL,
            translated_vtt TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (transcription_id) REFERENCES transcriptions (id)
        )
    ''')
    
    # Check if transcript_json column exists, if not add it
    cursor.execute("PRAGMA table_info(transcriptions)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'transcript_json' not in columns:
        print("Adding transcript_json column to existing database...")
        cursor.execute('ALTER TABLE transcriptions ADD COLUMN transcript_json TEXT')
        print("transcript_json column added successfully!")
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

app = Flask(__name__)
CORS(app)

# Retrieve the API key from environment variable
api_key = os.environ.get("SONIOX_API_KEY")
if not api_key:
    raise ValueError("SONIOX_API_KEY environment variable is required")

api_base = "https://api.soniox.com"

session = requests.Session()
session.headers["Authorization"] = f"Bearer {api_key}"

@app.route('/transcribe', methods=['POST'])
def start_transcription():
    print("🚀 [ENDPOINT] POST /transcribe - Starting new transcription")
    try:
        data = request.get_json()
        audio_url = data.get('audio_url')
        title = data.get('title', 'Untitled Transcription')
        language = data.get('language', 'en')
        
        if not audio_url:
            return jsonify({'error': 'audio_url is required'}), 400

        # Create language hints array with primary language first
        language_hints = [language]
        if language != 'en':
            language_hints.append('en')  # Add English as fallback

        res = session.post(
            f"{api_base}/v1/transcriptions",
            json={
                "audio_url": audio_url,
                "model": "stt-async-preview",
                "language_hints": language_hints,
            },
        )
        res.raise_for_status()
        transcription_id = res.json()["id"]
        
        # Store initial record in database
        conn = sqlite3.connect('transcriptions.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transcriptions (title, audio_url, language)
            VALUES (?, ?, ?)
        ''', (title, audio_url, language))
        db_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'transcription_id': transcription_id, 'db_id': db_id})
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/transcribe/<transcription_id>/status', methods=['GET'])
def get_transcription_status(transcription_id):
    print(f"📊 [ENDPOINT] GET /transcribe/{transcription_id}/status - Checking transcription status")
    try:
        res = session.get(f"{api_base}/v1/transcriptions/{transcription_id}")
        res.raise_for_status()
        data = res.json()
        
        return jsonify({
            'status': data['status'],
            'error_message': data.get('error_message')
        })
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_vtt(transcript_data):
    """Generate VTT content from transcript data with tokens"""
    vtt_content = "WEBVTT\n\n"
    
    tokens = transcript_data.get('tokens', [])
    if not tokens:
        return vtt_content
    
    # First, reconstruct complete words from token fragments
    words = []
    current_word = ""
    current_start_ms = None
    current_end_ms = None
    
    for token in tokens:
        token_text = token['text']
        
        # If token starts with a space or is the first token, it's a new word
        if token_text.startswith(' ') or current_word == "":
            # Save previous word if exists
            if current_word:
                words.append({
                    'text': current_word,
                    'start_ms': current_start_ms,
                    'end_ms': current_end_ms
                })
            
            # Start new word
            current_word = token_text.strip()
            current_start_ms = token['start_ms']
            current_end_ms = token['end_ms']
        else:
            # Continue building current word
            current_word += token_text
            current_end_ms = token['end_ms']
    
    # Don't forget the last word
    if current_word:
        words.append({
            'text': current_word,
            'start_ms': current_start_ms,
            'end_ms': current_end_ms
        })
    
    # Group complete words into subtitle chunks
    words_per_chunk = 6  # Number of complete words per subtitle
    
    for i in range(0, len(words), words_per_chunk):
        chunk = words[i:i + words_per_chunk]
        if not chunk:
            continue
            
        start_ms = chunk[0]['start_ms']
        end_ms = chunk[-1]['end_ms']
        
        # Convert milliseconds to VTT timestamp format (HH:MM:SS.mmm)
        start_time = format_vtt_timestamp(start_ms)
        end_time = format_vtt_timestamp(end_ms)
        
        # Combine text from all words in this chunk
        text = ' '.join(word['text'] for word in chunk)
        
        vtt_content += f"{start_time} --> {end_time}\n{text}\n\n"

    return vtt_content

def format_vtt_timestamp(ms):
    """Convert milliseconds to VTT timestamp format (HH:MM:SS.mmm)"""
    seconds = ms / 1000
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

@app.route('/transcribe/<transcription_id>/transcript', methods=['GET'])
def get_transcript(transcription_id):
    db_id = request.args.get('db_id')
    print(f"📝 [ENDPOINT] GET /transcribe/{transcription_id}/transcript - Getting plain text transcript (db_id: {db_id}, type: {type(db_id)})")
    try:
        
        res = session.get(f"{api_base}/v1/transcriptions/{transcription_id}/transcript")
        res.raise_for_status()
        transcript_data = res.json()
        
        # Update database with plain text and raw JSON
        if db_id:
            try:
                db_id_int = int(db_id)
                print(f"Converting db_id to int: {db_id} -> {db_id_int}")
                conn = sqlite3.connect('transcriptions.db')
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE transcriptions 
                    SET plain_text = ?, transcript_json = ? 
                    WHERE id = ?
                ''', (transcript_data['text'], str(transcript_data), db_id_int))
                rows_affected = cursor.rowcount
                conn.commit()
                conn.close()
                print(f"Database update completed. Rows affected: {rows_affected}")
            except ValueError as e:
                print(f"Error converting db_id to int: {e}")
            except Exception as e:
                print(f"Database error: {e}")
        else:
            print("No db_id provided!")
        
        # Clean up - delete the transcription
        try:
            session.delete(f"{api_base}/v1/transcriptions/{transcription_id}")
        except:
            pass  # Don't fail if cleanup fails
        
        return jsonify({'text': transcript_data['text']})
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/transcribe/<transcription_id>/vtt', methods=['GET'])
def get_transcript_vtt(transcription_id):
    db_id = request.args.get('db_id')
    print(f"🎬 [ENDPOINT] GET /transcribe/{transcription_id}/vtt - Getting VTT transcript (db_id: {db_id}, type: {type(db_id)})")
    try:
        
        res = session.get(f"{api_base}/v1/transcriptions/{transcription_id}/transcript")
        res.raise_for_status()
        transcript_data = res.json()
        
        # Generate VTT content
        vtt_content = generate_vtt(transcript_data)
        
        # Update database with VTT content, plain text, and raw JSON
        if db_id:
            try:
                db_id_int = int(db_id)
                print(f"Converting db_id to int: {db_id} -> {db_id_int}")
                conn = sqlite3.connect('transcriptions.db')
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE transcriptions 
                    SET vtt_content = ?, plain_text = ?, transcript_json = ? 
                    WHERE id = ?
                ''', (vtt_content, transcript_data['text'], str(transcript_data), db_id_int))
                rows_affected = cursor.rowcount
                conn.commit()
                conn.close()
                print(f"Database update completed. Rows affected: {rows_affected}")
            except ValueError as e:
                print(f"Error converting db_id to int: {e}")
            except Exception as e:
                print(f"Database error: {e}")
        else:
            print("No db_id provided!")
        
        # Clean up - delete the transcription
        try:
            session.delete(f"{api_base}/v1/transcriptions/{transcription_id}")
        except:
            pass  # Don't fail if cleanup fails
        
        # Return VTT content with proper content type
        from flask import Response
        return Response(vtt_content, mimetype='text/vtt', headers={
            'Content-Disposition': f'attachment; filename="transcript_{transcription_id}.vtt"'
        })
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/transcriptions', methods=['GET'])
def get_transcriptions():
    print("📋 [ENDPOINT] GET /transcriptions - Getting all saved transcriptions")
    try:
        conn = sqlite3.connect('transcriptions.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, audio_url, language, created_at, 
                   CASE WHEN vtt_content IS NOT NULL AND vtt_content != '' THEN 1 ELSE 0 END as has_vtt,
                   CASE WHEN plain_text IS NOT NULL AND plain_text != '' THEN 1 ELSE 0 END as has_text
            FROM transcriptions 
            ORDER BY created_at DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        transcriptions = []
        for row in rows:
            transcriptions.append({
                'id': row[0],
                'title': row[1],
                'audio_url': row[2],
                'language': row[3],
                'created_at': row[4],
                'has_vtt': bool(row[5]),
                'has_text': bool(row[6])
            })
        
        return jsonify({'transcriptions': transcriptions})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/transcriptions/<int:db_id>/vtt', methods=['GET'])
def get_saved_vtt(db_id):
    print(f"💾 [ENDPOINT] GET /transcriptions/{db_id}/vtt - Downloading saved VTT file")
    try:
        conn = sqlite3.connect('transcriptions.db')
        cursor = conn.cursor()
        cursor.execute('SELECT title, vtt_content FROM transcriptions WHERE id = ?', (db_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row or not row[1]:
            return jsonify({'error': 'VTT content not found'}), 404
        
        title, vtt_content = row
        
        # Return VTT content with proper content type
        from flask import Response
        return Response(vtt_content, mimetype='text/vtt', headers={
            'Content-Disposition': f'attachment; filename="{title}.vtt"'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/transcriptions/<int:db_id>/regenerate-vtt', methods=['POST'])
def regenerate_vtt(db_id):
    print(f"🔄 [ENDPOINT] POST /transcriptions/{db_id}/regenerate-vtt - Regenerating VTT from stored JSON")
    try:
        conn = sqlite3.connect('transcriptions.db')
        cursor = conn.cursor()
        cursor.execute('SELECT title, transcript_json FROM transcriptions WHERE id = ?', (db_id,))
        row = cursor.fetchone()
        
        if not row or not row[1]:
            conn.close()
            return jsonify({'error': 'Transcript JSON data not found'}), 404
        
        title, transcript_json_str = row
        
        # Parse the stored JSON data
        import json
        transcript_data = json.loads(transcript_json_str.replace("'", '"'))
        
        # Generate new VTT content
        vtt_content = generate_vtt(transcript_data)
        
        # Update database with new VTT content
        cursor.execute('''
            UPDATE transcriptions 
            SET vtt_content = ? 
            WHERE id = ?
        ''', (vtt_content, db_id))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'VTT regenerated successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/transcriptions/<int:db_id>/regenerate-text', methods=['POST'])
def regenerate_text(db_id):
    print(f"🔄 [ENDPOINT] POST /transcriptions/{db_id}/regenerate-text - Regenerating text from stored JSON")
    try:
        conn = sqlite3.connect('transcriptions.db')
        cursor = conn.cursor()
        cursor.execute('SELECT title, transcript_json FROM transcriptions WHERE id = ?', (db_id,))
        row = cursor.fetchone()
        
        if not row or not row[1]:
            conn.close()
            return jsonify({'error': 'Transcript JSON data not found'}), 404
        
        title, transcript_json_str = row
        
        # Parse the stored JSON data
        import json
        transcript_data = json.loads(transcript_json_str.replace("'", '"'))
        
        # Extract plain text
        plain_text = transcript_data.get('text', '')
        
        # Update database with plain text
        cursor.execute('''
            UPDATE transcriptions 
            SET plain_text = ? 
            WHERE id = ?
        ''', (plain_text, db_id))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Text regenerated successfully', 'text': plain_text})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/transcriptions/<int:db_id>', methods=['GET'])
def get_transcription_detail(db_id):
    print(f"📄 [ENDPOINT] GET /transcriptions/{db_id} - Getting transcription details")
    try:
        conn = sqlite3.connect('transcriptions.db')
        cursor = conn.cursor()
        
        # Get transcription details
        cursor.execute('''
            SELECT id, title, audio_url, language, plain_text, vtt_content, created_at
            FROM transcriptions 
            WHERE id = ?
        ''', (db_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({'error': 'Transcription not found'}), 404
        
        transcription = {
            'id': row[0],
            'title': row[1],
            'audio_url': row[2],
            'language': row[3],
            'plain_text': row[4],
            'vtt_content': row[5],
            'created_at': row[6]
        }
        
        # Get translations
        cursor.execute('''
            SELECT id, target_language, translated_text, translated_vtt, created_at
            FROM translations 
            WHERE transcription_id = ?
            ORDER BY created_at DESC
        ''', (db_id,))
        translation_rows = cursor.fetchall()
        
        translations = []
        for t_row in translation_rows:
            translations.append({
                'id': t_row[0],
                'target_language': t_row[1],
                'translated_text': t_row[2],
                'translated_vtt': t_row[3],
                'created_at': t_row[4]
            })
        
        conn.close()
        
        return jsonify({
            'transcription': transcription,
            'translations': translations
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/transcriptions/<int:db_id>/translations', methods=['POST'])
def add_translation(db_id):
    print(f"🌐 [ENDPOINT] POST /transcriptions/{db_id}/translations - Adding translation")
    try:
        data = request.get_json()
        target_language = data.get('target_language')
        translated_text = data.get('translated_text')
        translated_vtt = data.get('translated_vtt', '')
        
        if not target_language or not translated_text:
            return jsonify({'error': 'target_language and translated_text are required'}), 400
        
        conn = sqlite3.connect('transcriptions.db')
        cursor = conn.cursor()
        
        # Check if transcription exists
        cursor.execute('SELECT id FROM transcriptions WHERE id = ?', (db_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Transcription not found'}), 404
        
        # Insert translation
        cursor.execute('''
            INSERT INTO translations (transcription_id, target_language, translated_text, translated_vtt)
            VALUES (?, ?, ?, ?)
        ''', (db_id, target_language, translated_text, translated_vtt))
        
        translation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Translation added successfully',
            'translation_id': translation_id
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
