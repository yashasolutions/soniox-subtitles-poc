import os
import time
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv
from openai import OpenAI
import json
import re

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

# Retrieve the API keys from environment variables
soniox_api_key = os.environ.get("SONIOX_API_KEY")
if not soniox_api_key:
    raise ValueError("SONIOX_API_KEY environment variable is required")

openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")

api_base = "https://api.soniox.com"

session = requests.Session()
session.headers["Authorization"] = f"Bearer {soniox_api_key}"

# Initialize OpenAI client
openai_client = OpenAI(api_key=openai_api_key)

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

def translate_text_with_openai(text, target_language):
    """Translate text using OpenAI API"""
    language_names = {
        'en': 'English',
        'he': 'Hebrew',
        'ru': 'Russian',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh': 'Chinese'
    }
    
    target_lang_name = language_names.get(target_language, target_language)
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a professional translator. Translate the following text to {target_lang_name}. Maintain the original meaning and tone. Only return the translated text, no explanations."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=2000,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI translation error: {e}")
        raise e

def translate_vtt_content(vtt_content, target_language):
    """Translate VTT content while preserving timestamps and format"""
    if not vtt_content or not vtt_content.strip():
        return ""
    
    lines = vtt_content.split('\n')
    translated_lines = lines.copy()  # Initialize with original lines
    text_blocks = []
    current_block = []
    current_block_indices = []
    
    # First pass: identify text lines and group them into blocks
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Skip empty lines, WEBVTT header, and timestamp lines
        if not line_stripped or line_stripped == 'WEBVTT' or '-->' in line_stripped:
            # If we have accumulated text in current block, save it
            if current_block:
                text_blocks.append({
                    'text_lines': current_block.copy(),
                    'indices': current_block_indices.copy()
                })
                current_block.clear()
                current_block_indices.clear()
        else:
            # This is subtitle text, add to current block
            current_block.append(line_stripped)
            current_block_indices.append(i)
    
    # Don't forget the last block
    if current_block:
        text_blocks.append({
            'text_lines': current_block.copy(),
            'indices': current_block_indices.copy()
        })
    
    # Group text blocks into larger chunks for translation (aim for ~30-50 lines per chunk)
    chunk_size = 40  # Target lines per translation call
    chunks = []
    current_chunk = {'text_lines': [], 'indices': []}
    
    for block in text_blocks:
        # If adding this block would exceed chunk size and we already have content, start new chunk
        if len(current_chunk['text_lines']) + len(block['text_lines']) > chunk_size and current_chunk['text_lines']:
            chunks.append(current_chunk)
            current_chunk = {'text_lines': [], 'indices': []}
        
        current_chunk['text_lines'].extend(block['text_lines'])
        current_chunk['indices'].extend(block['indices'])
    
    # Don't forget the last chunk
    if current_chunk['text_lines']:
        chunks.append(current_chunk)
    
    # Translate each chunk
    for chunk in chunks:
        if not chunk['text_lines']:
            continue
            
        # Combine text lines with line numbers for context
        text_to_translate = '\n'.join(f"{i+1}. {text}" for i, text in enumerate(chunk['text_lines']))
        
        try:
            print(f"Translating chunk with {len(chunk['text_lines'])} lines...")
            translated_chunk = translate_text_with_openai(text_to_translate, target_language)
            
            # Parse the translated chunk back into individual lines
            translated_lines_chunk = []
            for line in translated_chunk.split('\n'):
                line = line.strip()
                if line and '. ' in line:
                    # Remove the line number prefix
                    translated_line = line.split('. ', 1)[1] if '. ' in line else line
                    translated_lines_chunk.append(translated_line)
                elif line:
                    # Fallback if format is unexpected
                    translated_lines_chunk.append(line)
            
            # Update the translated_lines array at the correct indices
            for i, original_index in enumerate(chunk['indices']):
                if i < len(translated_lines_chunk):
                    translated_lines[original_index] = translated_lines_chunk[i]
                else:
                    # Fallback to original if we don't have enough translated lines
                    print(f"Warning: Not enough translated lines for index {original_index}")
                    
        except Exception as e:
            print(f"Error translating chunk: {e}")
            # Keep original text for this chunk if translation fails
            for original_index in chunk['indices']:
                # translated_lines already contains the original text
                pass
    
    return '\n'.join(translated_lines)

@app.route('/transcriptions/<int:db_id>/translations', methods=['POST'])
def add_translation(db_id):
    print(f"🌐 [ENDPOINT] POST /transcriptions/{db_id}/translations - Adding translation")
    try:
        data = request.get_json()
        target_language = data.get('target_language')
        manual_translation = data.get('translated_text')  # Optional manual translation
        auto_translate = data.get('auto_translate', False)  # Whether to use AI translation
        
        if not target_language:
            return jsonify({'error': 'target_language is required'}), 400
        
        if not manual_translation and not auto_translate:
            return jsonify({'error': 'Either translated_text or auto_translate must be provided'}), 400
        
        conn = sqlite3.connect('transcriptions.db')
        cursor = conn.cursor()
        
        # Get transcription details
        cursor.execute('SELECT id, plain_text, vtt_content FROM transcriptions WHERE id = ?', (db_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'error': 'Transcription not found'}), 404
        
        transcription_id, original_text, original_vtt = row
        
        if auto_translate:
            # Use AI to translate
            if not original_text:
                conn.close()
                return jsonify({'error': 'No original text available for translation'}), 400
            
            print(f"Auto-translating text to {target_language}...")
            translated_text = translate_text_with_openai(original_text, target_language)
            
            # Translate VTT if available
            translated_vtt = ""
            if original_vtt:
                print(f"Auto-translating VTT to {target_language}...")
                translated_vtt = translate_vtt_content(original_vtt, target_language)
        else:
            # Use manual translation
            translated_text = manual_translation
            translated_vtt = data.get('translated_vtt', '')
        
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
            'translation_id': translation_id,
            'translated_text': translated_text,
            'translated_vtt': translated_vtt
        })
    
    except Exception as e:
        print(f"Translation error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
