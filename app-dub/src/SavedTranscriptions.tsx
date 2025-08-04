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

interface SavedTranscriptionsProps {
  onViewTranscript?: (id: number) => void
}

function SavedTranscriptions({ onViewTranscript }: SavedTranscriptionsProps) {
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

  const regenerateVtt = async (id: number) => {
    try {
      const response = await fetch(`http://localhost:5000/transcriptions/${id}/regenerate-vtt`, {
        method: 'POST'
      })
      if (response.ok) {
        // Reload transcriptions to update the status
        loadTranscriptions()
      } else {
        setError('Failed to regenerate VTT')
      }
    } catch (err) {
      setError('Failed to regenerate VTT')
      console.error('Failed to regenerate VTT:', err)
    }
  }

  const regenerateText = async (id: number) => {
    try {
      const response = await fetch(`http://localhost:5000/transcriptions/${id}/regenerate-text`, {
        method: 'POST'
      })
      if (response.ok) {
        // Reload transcriptions to update the status
        loadTranscriptions()
      } else {
        setError('Failed to regenerate text')
      }
    } catch (err) {
      setError('Failed to regenerate text')
      console.error('Failed to regenerate text:', err)
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

              <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
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
                  <button
                    onClick={() => regenerateVtt(item.id)}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#ffc107',
                      color: '#212529',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '14px',
                      cursor: 'pointer'
                    }}
                  >
                    🔄 Generate VTT
                  </button>
                )}
                
                {!item.has_text && (
                  <button
                    onClick={() => regenerateText(item.id)}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#17a2b8',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '14px',
                      cursor: 'pointer'
                    }}
                  >
                    🔄 Generate Text
                  </button>
                )}
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    Status: {item.has_text ? '✅ Text' : '❌ Text'} | {item.has_vtt ? '✅ VTT' : '❌ VTT'}
                  </div>
                  
                  {onViewTranscript && (
                    <button
                      onClick={() => onViewTranscript(item.id)}
                      style={{
                        padding: '6px 12px',
                        backgroundColor: '#007bff',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        fontSize: '12px',
                        cursor: 'pointer'
                      }}
                    >
                      👁️ View Details
                    </button>
                  )}
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
