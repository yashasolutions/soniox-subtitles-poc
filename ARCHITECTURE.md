# Architecture Documentation

## System Overview

The Audio Transcription & Translation Platform is a full-stack web application built with a React TypeScript frontend and a Python Flask backend. The system integrates with external APIs (Soniox for transcription, OpenAI for translation) and uses SQLite for persistent data storage.

## Architecture Diagram

```
┌─────────────────┐    HTTP/REST    ┌─────────────────┐
│   React Frontend│◄──────────────►│  Flask Backend  │
│   (TypeScript)  │                 │    (Python)     │
└─────────────────┘                 └─────────────────┘
                                            │
                                            ▼
                                    ┌─────────────────┐
                                    │ SQLite Database │
                                    │  (Local File)   │
                                    └─────────────────┘
                                            │
                                            ▼
                                    ┌─────────────────┐
                                    │  External APIs  │
                                    │ • Soniox API    │
                                    │ • OpenAI API    │
                                    └─────────────────┘
```

## Component Architecture

### Frontend Architecture

#### Main Components
- **App.tsx**: Root component managing routing and main transcription interface
- **SavedTranscriptions.tsx**: Component for displaying and managing saved transcriptions
- **TranscriptView.tsx**: Detailed view for individual transcriptions and translations

#### State Management
- Uses React's built-in `useState` and `useEffect` hooks
- No external state management library (Redux, Zustand) - keeps it simple
- State is managed at the component level with prop drilling for shared data

#### Key Frontend Features
- Real-time polling for transcription status updates
- Responsive design with modern CSS
- File download functionality for VTT files
- Form validation and error handling

### Backend Architecture

#### Core Components
- **Flask Application**: Main web server handling HTTP requests
- **Database Layer**: SQLite with direct SQL queries (no ORM)
- **External API Integration**: Soniox and OpenAI API clients
- **Auto-save System**: Automatic persistence of completed transcriptions

#### Key Backend Features
- RESTful API design
- CORS enabled for cross-origin requests
- Comprehensive error handling and logging
- Automatic cleanup of temporary transcription data

## Database Schema

### Tables

#### transcriptions
```sql
CREATE TABLE transcriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    audio_url TEXT NOT NULL,
    language TEXT NOT NULL,
    vtt_content TEXT,
    plain_text TEXT,
    transcript_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### translations
```sql
CREATE TABLE translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcription_id INTEGER NOT NULL,
    target_language TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    translated_vtt TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transcription_id) REFERENCES transcriptions (id)
);
```

### Data Flow
1. **Initial Record**: Created when transcription starts (title, audio_url, language)
2. **Completion Update**: Auto-populated when transcription completes (vtt_content, plain_text, transcript_json)
3. **Translation Addition**: New records in translations table linked to transcription

## API Integration

### Soniox API Integration
- **Authentication**: Bearer token authentication
- **Endpoints Used**:
  - `POST /v1/transcriptions` - Start transcription
  - `GET /v1/transcriptions/{id}` - Check status
  - `GET /v1/transcriptions/{id}/transcript` - Get results
  - `DELETE /v1/transcriptions/{id}` - Cleanup

### OpenAI API Integration
- **Model Used**: GPT-4o for high-quality translations
- **Translation Strategy**: Context-aware block translation for VTT files
- **Chunk Size**: 40 lines per translation request to balance context and token limits

## Key Algorithms

### VTT Generation Algorithm
```python
def generate_vtt(transcript_data):
    # 1. Extract tokens from transcript data
    # 2. Reconstruct complete words from token fragments
    # 3. Group words into subtitle chunks (6 words per chunk)
    # 4. Generate timestamps in VTT format (HH:MM:SS.mmm)
    # 5. Format as WebVTT content
```

### Context-Aware VTT Translation
```python
def translate_vtt_content(vtt_content, target_language):
    # 1. Parse VTT content, separating text from timestamps
    # 2. Group text lines into blocks for context
    # 3. Combine blocks into chunks (~40 lines each)
    # 4. Translate chunks with numbered lines for structure
    # 5. Parse translated content back to individual lines
    # 6. Reconstruct VTT with original timestamps
```

### Auto-Save System
```python
def auto_save_completed_transcription(transcription_id, db_id):
    # 1. Verify database record exists
    # 2. Check if already saved (avoid duplicates)
    # 3. Fetch transcript data from Soniox
    # 4. Generate VTT content
    # 5. Update database with all content
    # 6. Cleanup temporary Soniox data
```

## Security Considerations

### API Key Management
- Environment variables for sensitive data
- No API keys exposed in frontend code
- Server-side API calls only

### Input Validation
- URL validation for audio inputs
- Language code validation
- Database ID validation for all operations

### Error Handling
- Comprehensive try-catch blocks
- Graceful degradation on API failures
- User-friendly error messages

## Performance Optimizations

### Frontend Optimizations
- Efficient polling with 1-second intervals
- Conditional rendering to avoid unnecessary re-renders
- Lazy loading of transcription details

### Backend Optimizations
- Connection pooling for database operations
- Efficient SQL queries with proper indexing
- Cleanup of temporary data to prevent storage bloat

### Translation Optimizations
- Block-based translation to reduce API calls
- Context preservation for better translation quality
- Fallback to original content on translation failures

## Scalability Considerations

### Current Limitations
- SQLite database (single-file, limited concurrent writes)
- No user authentication or multi-tenancy
- Local file storage only

### Potential Improvements
- **Database**: Migrate to PostgreSQL for better concurrency
- **Authentication**: Add user management and session handling
- **Storage**: Implement cloud storage for audio files
- **Caching**: Add Redis for session and result caching
- **Queue System**: Implement background job processing for long transcriptions

## Deployment Architecture

### Development Setup
- Frontend: Vite dev server (localhost:5173)
- Backend: Flask dev server (localhost:5000)
- Database: Local SQLite file

### Production Considerations
- **Frontend**: Build static files, serve via CDN or web server
- **Backend**: WSGI server (Gunicorn) behind reverse proxy (Nginx)
- **Database**: Migrate to PostgreSQL with proper backup strategy
- **Environment**: Docker containers for consistent deployment

## Error Handling Strategy

### Frontend Error Handling
- Try-catch blocks around all API calls
- User-friendly error messages
- Graceful degradation when features fail
- Loading states and progress indicators

### Backend Error Handling
- Comprehensive logging with different levels
- Proper HTTP status codes
- Detailed error messages for debugging
- Fallback behaviors for external API failures

## Testing Strategy

### Current State
- No automated tests implemented
- Manual testing during development

### Recommended Testing Approach
- **Frontend**: Jest + React Testing Library for component tests
- **Backend**: pytest for API endpoint testing
- **Integration**: End-to-end tests with Playwright or Cypress
- **API Mocking**: Mock external APIs for reliable testing

## Monitoring and Logging

### Current Logging
- Print statements for debugging
- Basic error logging in backend
- Browser console for frontend errors

### Production Logging Recommendations
- Structured logging with JSON format
- Log aggregation system (ELK stack or similar)
- Application performance monitoring (APM)
- Error tracking service (Sentry)

## Configuration Management

### Environment Variables
```env
SONIOX_API_KEY=your_soniox_key
OPENAI_API_KEY=your_openai_key
```

### Configuration Files
- `package.json`: Frontend dependencies and scripts
- `requirements.txt`: Backend Python dependencies
- `vite.config.ts`: Frontend build configuration
- `tsconfig.json`: TypeScript configuration

## Development Workflow

### Git Workflow
- Feature branches for new development
- Descriptive commit messages
- Regular commits with atomic changes

### Code Style
- TypeScript for frontend type safety
- Python PEP 8 style guidelines
- Consistent naming conventions
- Comprehensive comments for complex logic

## Future Enhancements

### Short-term Improvements
- Add user authentication
- Implement batch transcription
- Add more translation languages
- Improve error handling and user feedback

### Long-term Vision
- Multi-user support with role-based access
- Real-time collaboration features
- Advanced audio processing options
- Integration with more transcription services
- Mobile application development

## Troubleshooting Guide

### Common Issues
1. **Transcription not saving**: Check db_id parameter in status polling
2. **Translation errors**: Verify OpenAI API key and model availability
3. **VTT format issues**: Check token data structure from Soniox
4. **CORS errors**: Ensure Flask-CORS is properly configured

### Debug Steps
1. Check browser console for frontend errors
2. Review backend logs for API call failures
3. Verify database schema and data integrity
4. Test external API connectivity independently

This architecture documentation provides a comprehensive overview of the system design, implementation details, and considerations for future development and deployment.
