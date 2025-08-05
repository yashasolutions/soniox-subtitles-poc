# Audio Transcription Tool

A simple web application for transcribing audio files using the Soniox API and translating results with OpenAI. Basic functionality for converting audio to text and VTT subtitle files.

## Features

- **Audio Transcription**: Convert audio files to text using Soniox API
- **Multi-language Support**: Supports Hebrew, English, Russian, Spanish, French, German, Italian, Portuguese, Japanese, Korean, and Chinese
- **VTT Generation**: Generate WebVTT subtitle files with timestamps
- **Basic Translation**: Translate transcriptions using OpenAI GPT
- **Simple Storage**: Save transcriptions to SQLite database
- **File Downloads**: Download VTT files

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- Soniox API key
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Create a `.env` file in the backend directory:
   ```env
   SONIOX_API_KEY=your_soniox_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Set up the frontend**
   ```bash
   cd app-dub
   npm install
   ```

### Running the Application

1. **Start the backend server**
   ```bash
   cd backend
   python server.py
   ```
   The backend will run on `http://localhost:5000`

2. **Start the frontend development server**
   ```bash
   cd app-dub
   npm run dev
   ```
   The frontend will run on `http://localhost:5173`

3. **Access the application**
   Open your browser and navigate to `http://localhost:5173`

## Usage

1. Enter a title and audio file URL
2. Select the source language
3. Choose text or VTT format
4. Click "Start Transcription"
5. Wait for completion and view results
6. Download VTT files if needed
7. View saved transcriptions in the list

## API Endpoints

### Transcription Endpoints
- `POST /transcribe` - Start a new transcription
- `GET /transcribe/{id}/status` - Check transcription status
- `GET /transcribe/{id}/transcript` - Get plain text transcript
- `GET /transcribe/{id}/vtt` - Get VTT format transcript

### Management Endpoints
- `GET /transcriptions` - List all saved transcriptions
- `GET /transcriptions/{id}` - Get transcription details
- `GET /transcriptions/{id}/vtt` - Download saved VTT file
- `POST /transcriptions/{id}/regenerate-vtt` - Regenerate VTT content
- `POST /transcriptions/{id}/regenerate-text` - Regenerate text content

### Translation Endpoints
- `POST /transcriptions/{id}/translations` - Add a new translation

## Technology Stack

- **Frontend**: React + TypeScript + Vite (basic setup)
- **Backend**: Flask (Python)
- **Database**: SQLite
- **APIs**: Soniox (transcription), OpenAI (translation)

## Configuration

### Environment Variables
- `SONIOX_API_KEY`: Your Soniox API key for speech-to-text services
- `OPENAI_API_KEY`: Your OpenAI API key for translation services

### Supported Languages
- Hebrew (he)
- English (en)
- Russian (ru)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Japanese (ja)
- Korean (ko)
- Chinese (zh)

## Development

Start the backend:
```bash
cd backend
python server.py
```

Start the frontend:
```bash
cd app-dub
npm run dev
```

## Notes

This is a basic prototype with minimal error handling and a simple UI. The code is functional but not production-ready.
