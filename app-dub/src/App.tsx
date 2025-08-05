import { useState, useEffect } from 'react'
import SavedTranscriptions from './SavedTranscriptions'
import TranscriptView from './TranscriptView'
import './App.css'

function App() {
  const [currentPage, setCurrentPage] = useState('transcribe')
  const [selectedTranscriptId, setSelectedTranscriptId] = useState<number | null>(null)
  const [audioUrl, setAudioUrl] = useState('https://soniox.com/media/examples/coffee_shop.mp3')
  const [title, setTitle] = useState('')
  const [language, setLanguage] = useState('he')
  const [useVtt, setUseVtt] = useState(false)
  const [status, setStatus] = useState('')
  const [transcript, setTranscript] = useState('')
  const [transcriptionId, setTranscriptionId] = useState('')
  const [dbId, setDbId] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [savedTranscriptions, setSavedTranscriptions] = useState([])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')
    setTranscript('')
    setTranscriptionId('')
    setDbId('')
    setStatus('Starting transcription...')

    try {
      // Start transcription
      const startResponse = await fetch('http://localhost:5000/transcribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ audio_url: audioUrl, title: title, language: language }),
      })

      if (!startResponse.ok) {
        throw new Error(`HTTP error! status: ${startResponse.status}`)
      }

      const { transcription_id, db_id } = await startResponse.json()
      setStatus(`Transcription started. ID: ${transcription_id}`)
      setDbId(db_id)

      // Poll for completion
      let completed = false
      while (!completed) {
        setStatus(`Polling for completion... ID: ${transcription_id}`)
        
        const pollResponse = await fetch(`http://localhost:5000/transcribe/${transcription_id}/status?db_id=${db_id}`)
        if (!pollResponse.ok) {
          throw new Error(`HTTP error! status: ${pollResponse.status}`)
        }

        const statusData = await pollResponse.json()
        
        if (statusData.status === 'completed') {
          completed = true
          setStatus('Transcription completed! Fetching transcript...')
          
          // Get transcript or VTT based on user selection
          if (useVtt) {
            const vttResponse = await fetch(`http://localhost:5000/transcribe/${transcription_id}/vtt?db_id=${dbId}`)
            if (!vttResponse.ok) {
              throw new Error(`HTTP error! status: ${vttResponse.status}`)
            }
            
            const vttContent = await vttResponse.text()
            setTranscript(vttContent)
            setStatus('VTT file generated and saved successfully!')
          } else {
            const transcriptResponse = await fetch(`http://localhost:5000/transcribe/${transcription_id}/transcript?db_id=${dbId}`)
            if (!transcriptResponse.ok) {
              throw new Error(`HTTP error! status: ${transcriptResponse.status}`)
            }
            
            const transcriptData = await transcriptResponse.json()
            setTranscript(transcriptData.text)
            setStatus('Transcription completed and saved successfully!')
          }
          
          // Store transcription ID for VTT download
          setTranscriptionId(transcription_id)
          
          // Refresh saved transcriptions list
          loadSavedTranscriptions()
          
        } else if (statusData.status === 'error') {
          throw new Error(`Transcription failed: ${statusData.error_message || 'Unknown error'}`)
        }
        
        // Wait 1 second before polling again
        if (!completed) {
          await new Promise(resolve => setTimeout(resolve, 1000))
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred')
      setStatus('')
    } finally {
      setIsLoading(false)
    }
  }

  const loadSavedTranscriptions = async () => {
    try {
      const response = await fetch('http://localhost:5000/transcriptions')
      if (response.ok) {
        const data = await response.json()
        setSavedTranscriptions(data.transcriptions)
      }
    } catch (err) {
      console.error('Failed to load saved transcriptions:', err)
    }
  }

  // Load saved transcriptions on component mount
  useEffect(() => {
    loadSavedTranscriptions()
  }, [])

  if (currentPage === 'saved') {
    return (
      <SavedTranscriptions 
        onViewTranscript={(id) => {
          setSelectedTranscriptId(id)
          setCurrentPage('transcript-view')
        }}
      />
    )
  }

  if (currentPage === 'transcript-view' && selectedTranscriptId) {
    return (
      <TranscriptView 
        transcriptionId={selectedTranscriptId}
        onBack={() => {
          setCurrentPage('saved')
          setSelectedTranscriptId(null)
        }}
      />
    )
  }

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Soniox Audio Transcription</h1>
        <button
          onClick={() => setCurrentPage('saved')}
          style={{
            padding: '10px 20px',
            backgroundColor: '#17a2b8',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          📁 View Saved Transcriptions
        </button>
      </div>
      
      <form onSubmit={handleSubmit} className="transcription-form">
        <div className="form-group">
          <label htmlFor="title">Title:</label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Enter a title for this transcription"
            disabled={isLoading}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="audioUrl">Audio URL:</label>
          <input
            type="url"
            id="audioUrl"
            value={audioUrl}
            onChange={(e) => setAudioUrl(e.target.value)}
            required
            disabled={isLoading}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="language">Language:</label>
          <select
            id="language"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            disabled={isLoading}
          >
            <option value="he">Hebrew</option>
            <option value="en">English</option>
            <option value="ru">Russian</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="de">German</option>
            <option value="it">Italian</option>
            <option value="pt">Portuguese</option>
            <option value="ja">Japanese</option>
            <option value="ko">Korean</option>
            <option value="zh">Chinese</option>
          </select>
        </div>
        
        <div className="form-group">
          <div className="checkbox-group">
            <input
              type="checkbox"
              id="useVtt"
              checked={useVtt}
              onChange={(e) => setUseVtt(e.target.checked)}
              disabled={isLoading}
            />
            <label htmlFor="useVtt">Generate VTT format (with timestamps)</label>
          </div>
        </div>
        
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Transcribing...' : 'Start Transcription'}
        </button>
      </form>

      {status && (
        <div className={`status ${isLoading ? 'loading' : 'success'}`}>
          {status}
        </div>
      )}

      {error && (
        <div className="status error">
          Error: {error}
        </div>
      )}

      {transcript && (
        <div>
          <h2>{useVtt ? 'VTT Content:' : 'Transcript:'}</h2>
          <div className="transcript">
            {transcript}
          </div>
          {!useVtt && (
            <div style={{ marginTop: '20px' }}>
              <a
                href={`http://localhost:5000/transcribe/${transcriptionId}/vtt`}
                download={`transcript_${transcriptionId}.vtt`}
                style={{
                  display: 'inline-block',
                  padding: '10px 20px',
                  backgroundColor: '#28a745',
                  color: 'white',
                  textDecoration: 'none',
                  borderRadius: '4px',
                  fontSize: '16px'
                }}
              >
                Download VTT File
              </a>
            </div>
          )}
        </div>
      )}

      {savedTranscriptions.length > 0 && (
        <div style={{ marginTop: '40px' }}>
          <h2>Saved Transcriptions</h2>
          <div style={{ display: 'grid', gap: '10px' }}>
            {savedTranscriptions.map((item: any) => (
              <div key={item.id} style={{
                padding: '15px',
                border: '1px solid #ddd',
                borderRadius: '8px',
                backgroundColor: '#f9f9f9'
              }}>
                <h3 style={{ margin: '0 0 10px 0' }}>{item.title}</h3>
                <p style={{ margin: '5px 0', fontSize: '14px', color: '#666' }}>
                  Language: {item.language} | Created: {new Date(item.created_at).toLocaleString()}
                </p>
                <p style={{ margin: '5px 0', fontSize: '14px', color: '#666' }}>
                  URL: <a href={item.audio_url} target="_blank" rel="noopener noreferrer">{item.audio_url}</a>
                </p>
                {item.has_vtt && (
                  <a
                    href={`http://localhost:5000/transcriptions/${item.id}/vtt`}
                    download={`${item.title}.vtt`}
                    style={{
                      display: 'inline-block',
                      padding: '5px 10px',
                      backgroundColor: '#28a745',
                      color: 'white',
                      textDecoration: 'none',
                      borderRadius: '4px',
                      fontSize: '14px',
                      marginTop: '10px'
                    }}
                  >
                    Download VTT
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default App
