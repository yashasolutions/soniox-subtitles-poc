import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

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
    try:
        data = request.get_json()
        audio_url = data.get('audio_url')
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
        
        return jsonify({'transcription_id': transcription_id})
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/transcribe/<transcription_id>/status', methods=['GET'])
def get_transcription_status(transcription_id):
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
    
    # Group tokens into reasonable subtitle chunks (e.g., every 5-10 tokens or by time intervals)
    chunk_size = 8  # Number of tokens per subtitle
    
    for i in range(0, len(tokens), chunk_size):
        chunk = tokens[i:i + chunk_size]
        if not chunk:
            continue
            
        start_ms = chunk[0]['start_ms']
        end_ms = chunk[-1]['end_ms']
        
        # Convert milliseconds to VTT timestamp format (HH:MM:SS.mmm)
        start_time = format_vtt_timestamp(start_ms)
        end_time = format_vtt_timestamp(end_ms)
        
        # Combine text from all tokens in this chunk
        text = ''.join(token['text'] for token in chunk)
        
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
    try:
        res = session.get(f"{api_base}/v1/transcriptions/{transcription_id}/transcript")
        res.raise_for_status()
        transcript_data = res.json()
        
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
    try:
        res = session.get(f"{api_base}/v1/transcriptions/{transcription_id}/transcript")
        res.raise_for_status()
        transcript_data = res.json()
        
        # Generate VTT content
        vtt_content = generate_vtt(transcript_data)
        
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
