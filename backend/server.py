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
        
        if not audio_url:
            return jsonify({'error': 'audio_url is required'}), 400

        res = session.post(
            f"{api_base}/v1/transcriptions",
            json={
                "audio_url": audio_url,
                "model": "stt-async-preview",
                "language_hints": ["en", "es"],
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
