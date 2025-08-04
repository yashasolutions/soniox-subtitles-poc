import { useState, useEffect } from 'react'
import './App.css'

interface Transcription {
  id: number
  title: string
  audio_url: string
  language: string
  created_at: string
  has_vtt: boolean
  has_text: boolean
}

function SavedTranscriptions() {
  const [transcriptions, setTranscriptions] = useState<Transcription[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadTranscriptions = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:5000/transcriptions')
      if (response.ok) {
        const data = await response.json()
        setTranscriptions(data.transcriptions)
      } else {
        setError('Failed to load transcriptions')
      }
    } catch (err) {
      setError('Failed to load transcriptions')
      console.error('Failed to load saved transcriptions:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTranscriptions()
  }, [])

  if (loading) {
    return (
      <div className="container">
        <h1>Saved Transcriptions</h1>
        <div className="status loading">Loading transcriptions...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container">
        <h1>Saved Transcriptions</h1>
        <div className="status error">Error: {error}</div>
        <button onClick={loadTranscriptions} style={{ marginTop: '10px' }}>
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="container">
      <h1>Saved Transcriptions</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <a 
          href="/" 
          style={{
            display: 'inline-block',
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            textDecoration: 'none',
            borderRadius: '4px',
            fontSize: '16px'
          }}
        >
          ← Back to Transcription
        </a>
      </div>

      {transcriptions.length === 0 ? (
        <div className="status">
          No saved transcriptions found.
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '15px' }}>
          {transcriptions.map((item) => (
            <div key={item.id} style={{
              padding: '20px',
              border: '1px solid #ddd',
              borderRadius: '8px',
              backgroundColor: '#f9f9f9'
            }}>
              <h3 style={{ margin: '0 0 15px 0', color: '#333' }}>
                {item.title || 'Untitled Transcription'}
              </h3>
              
              <div style={{ marginBottom: '10px' }}>
                <strong>Language:</strong> {item.language.toUpperCase()}
                <span style={{ margin: '0 15px', color: '#666' }}>|</span>
                <strong>Created:</strong> {new Date(item.created_at).toLocaleString()}
              </div>
              
              <div style={{ marginBottom: '15px', fontSize: '14px' }}>
                <strong>Audio URL:</strong>{' '}
                <a 
                  href={item.audio_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style={{ color: '#007bff', wordBreak: 'break-all' }}
                >
                  {item.audio_url}
                </a>
              </div>

              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                {item.has_vtt ? (
                  <a
                    href={`http://localhost:5000/transcriptions/${item.id}/vtt`}
                    download={`${item.title || 'transcript'}.vtt`}
                    style={{
                      display: 'inline-block',
                      padding: '8px 16px',
                      backgroundColor: '#28a745',
                      color: 'white',
                      textDecoration: 'none',
                      borderRadius: '4px',
                      fontSize: '14px'
                    }}
                  >
                    📥 Download VTT
                  </a>
                ) : (
                  <span style={{ 
                    padding: '8px 16px',
                    backgroundColor: '#6c757d',
                    color: 'white',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}>
                    VTT Not Available
                  </span>
                )}
                
                <div style={{ fontSize: '12px', color: '#666' }}>
                  Status: {item.has_text ? '✅ Text' : '❌ Text'} | {item.has_vtt ? '✅ VTT' : '❌ VTT'}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      <div style={{ marginTop: '30px', textAlign: 'center' }}>
        <button 
          onClick={loadTranscriptions}
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
          🔄 Refresh List
        </button>
      </div>
    </div>
  )
}

export default SavedTranscriptions
