# Audio Transcription & Translation Platform

A full-stack web application for transcribing audio files using Soniox API and translating transcriptions using OpenAI GPT models. The platform supports multiple languages, generates VTT subtitle files, and provides a comprehensive management interface for saved transcriptions.

## Features

### Core Functionality
- **Audio Transcription**: Convert audio files to text using Soniox's advanced speech-to-text API
- **Multi-language Support**: Transcribe audio in Hebrew, English, Russian, Spanish, French, German, Italian, Portuguese, Japanese, Korean, and Chinese
- **VTT Generation**: Automatically generate WebVTT subtitle files with precise timestamps
- **AI Translation**: Translate transcriptions to different languages using OpenAI GPT-4
- **Context-aware Translation**: VTT files are translated in blocks to preserve context and improve quality

### User Interface
- **Real-time Status Updates**: Live polling of transcription progress
- **Saved Transcriptions Management**: View, download, and manage all transcriptions
- **Translation Management**: Add and manage multiple translations per transcription
- **Responsive Design**: Modern, clean interface that works on all devices

### Data Management
- **SQLite Database**: Persistent storage for transcriptions and translations
- **Auto-save**: Completed transcriptions are automatically saved to the database
- **Regeneration**: Regenerate VTT or text content from stored JSON data
- **Download Support**: Download VTT files directly from the interface

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

### Creating a Transcription
1. Enter a title for your transcription
2. Provide the audio file URL
3. Select the source language
4. Choose whether to generate VTT format
5. Click "Start Transcription"
6. Monitor the real-time progress updates
7. View the completed transcription or download the VTT file

### Managing Saved Transcriptions
1. Click "📁 View Saved Transcriptions" to see all saved transcriptions
2. Use the "Regenerate VTT" or "Regenerate Text" buttons to recreate content
3. Click "View Details" to see full transcription details and translations
4. Download VTT files directly from the list

### Adding Translations
1. Navigate to a transcription's detail view
2. Select a target language
3. Choose between manual translation or AI-powered translation
4. The system will translate both text and VTT content while preserving timestamps

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

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development and building
- **Modern CSS** for styling
- **Fetch API** for HTTP requests

### Backend
- **Flask** web framework
- **SQLite** database
- **Soniox API** for speech-to-text
- **OpenAI API** for translations
- **CORS** enabled for cross-origin requests

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

### Frontend Development
```bash
cd app-dub
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
```

### Backend Development
The Flask server runs in debug mode by default, providing hot reloading during development.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the ARCHITECTURE.md file for technical details
2. Review the API documentation
3. Create an issue in the repository

## Changelog

See the git commit history for detailed changes and improvements.
