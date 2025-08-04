import { useState } from 'react'
import './App.css'

function App() {
  const [audioUrl, setAudioUrl] = useState('https://soniox.com/media/examples/coffee_shop.mp3')
  const [language, setLanguage] = useState('he')
  const [useVtt, setUseVtt] = useState(false)
  const [status, setStatus] = useState('')
  const [transcript, setTranscript] = useState('')
  const [transcriptionId, setTranscriptionId] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')
    setTranscript('')
    setTranscriptionId('')
    setStatus('Starting transcription...')

    try {
      // Start transcription
      const startResponse = await fetch('http://localhost:5000/transcribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ audio_url: audioUrl, language: language }),
      })

      if (!startResponse.ok) {
        throw new Error(`HTTP error! status: ${startResponse.status}`)
      }

      const { transcription_id } = await startResponse.json()
      setStatus(`Transcription started. ID: ${transcription_id}`)

      // Poll for completion
      let completed = false
      while (!completed) {
        setStatus(`Polling for completion... ID: ${transcription_id}`)
        
        const pollResponse = await fetch(`http://localhost:5000/transcribe/${transcription_id}/status`)
        if (!pollResponse.ok) {
          throw new Error(`HTTP error! status: ${pollResponse.status}`)
        }

        const statusData = await pollResponse.json()
        
        if (statusData.status === 'completed') {
          completed = true
          setStatus('Transcription completed! Fetching transcript...')
          
          // Get transcript or VTT based on user selection
          if (useVtt) {
            const vttResponse = await fetch(`http://localhost:5000/transcribe/${transcription_id}/vtt`)
            if (!vttResponse.ok) {
              throw new Error(`HTTP error! status: ${vttResponse.status}`)
            }
            
            const vttContent = await vttResponse.text()
            setTranscript(vttContent)
            setStatus('VTT file generated successfully!')
          } else {
            const transcriptResponse = await fetch(`http://localhost:5000/transcribe/${transcription_id}/transcript`)
            if (!transcriptResponse.ok) {
              throw new Error(`HTTP error! status: ${transcriptResponse.status}`)
            }
            
            const transcriptData = await transcriptResponse.json()
            setTranscript(transcriptData.text)
            setStatus('Transcription completed successfully!')
          }
          
          // Store transcription ID for VTT download
          setTranscriptionId(transcription_id)
          
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

  return (
    <div className="container">
      <h1>Soniox Audio Transcription</h1>
      
      <form onSubmit={handleSubmit} className="transcription-form">
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
    </div>
  )
}

export default App
