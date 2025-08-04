import { useState, useEffect } from 'react'
import './App.css'

interface Transcription {
  id: number
  title: string
  audio_url: string
  language: string
  plain_text: string
  vtt_content: string
  created_at: string
}

interface Translation {
  id: number
  target_language: string
  translated_text: string
  translated_vtt: string
  created_at: string
}

interface TranscriptViewProps {
  transcriptionId: number
  onBack: () => void
}

function TranscriptView({ transcriptionId, onBack }: TranscriptViewProps) {
  const [transcription, setTranscription] = useState<Transcription | null>(null)
  const [translations, setTranslations] = useState<Translation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showAddTranslation, setShowAddTranslation] = useState(false)
  const [newTranslation, setNewTranslation] = useState({
    target_language: 'en',
    translated_text: '',
    auto_translate: false
  })

  const loadTranscriptionDetails = async () => {
    try {
      setLoading(true)
      const response = await fetch(`http://localhost:5000/transcriptions/${transcriptionId}`)
      if (response.ok) {
        const data = await response.json()
        setTranscription(data.transcription)
        setTranslations(data.translations)
      } else {
        setError('Failed to load transcription details')
      }
    } catch (err) {
      setError('Failed to load transcription details')
      console.error('Failed to load transcription details:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAddTranslation = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate input
    if (!newTranslation.auto_translate && !newTranslation.translated_text.trim()) {
      setError('Please provide a translation or enable auto-translate')
      return
    }

    try {
      const response = await fetch(`http://localhost:5000/transcriptions/${transcriptionId}/translations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newTranslation),
      })

      if (response.ok) {
        setNewTranslation({ target_language: 'en', translated_text: '', auto_translate: false })
        setShowAddTranslation(false)
        loadTranscriptionDetails() // Reload to show new translation
        setError('') // Clear any previous errors
      } else {
        const errorData = await response.json()
        setError(errorData.error || 'Failed to add translation')
      }
    } catch (err) {
      setError('Failed to add translation')
      console.error('Failed to add translation:', err)
    }
  }

  useEffect(() => {
    loadTranscriptionDetails()
  }, [transcriptionId])

  if (loading) {
    return (
      <div className="container">
        <div className="status loading">Loading transcription details...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container">
        <div className="status error">Error: {error}</div>
        <button onClick={loadTranscriptionDetails} style={{ marginTop: '10px' }}>
          Retry
        </button>
      </div>
    )
  }

  if (!transcription) {
    return (
      <div className="container">
        <div className="status error">Transcription not found</div>
        <button onClick={onBack} style={{ marginTop: '10px' }}>
          ← Back
        </button>
      </div>
    )
  }

  return (
    <div className="container">
      <div style={{ marginBottom: '20px' }}>
        <button
          onClick={onBack}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          ← Back
        </button>
      </div>

      <div className="transcription-card">
        <h1>{transcription.title}</h1>
        
        <div style={{ marginBottom: '15px', fontSize: '14px', color: '#666' }}>
          <strong>Language:</strong> {transcription.language.toUpperCase()} | 
          <strong> Created:</strong> {new Date(transcription.created_at).toLocaleString()}
        </div>
        
        <div style={{ marginBottom: '15px', fontSize: '14px' }}>
          <strong>Audio URL:</strong>{' '}
          <a 
            href={transcription.audio_url} 
            target="_blank" 
            rel="noopener noreferrer"
            style={{ color: '#007bff', wordBreak: 'break-all' }}
          >
            {transcription.audio_url}
          </a>
        </div>

        {transcription.plain_text && (
          <div>
            <h3>Original Transcript:</h3>
            <div className="transcript" style={{ marginBottom: '20px' }}>
              {transcription.plain_text}
            </div>
          </div>
        )}

        {transcription.vtt_content && (
          <div style={{ marginBottom: '20px' }}>
            <a
              href={`http://localhost:5000/transcriptions/${transcription.id}/vtt`}
              download={`${transcription.title}.vtt`}
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
              📥 Download VTT
            </a>
          </div>
        )}
      </div>

      <div style={{ marginTop: '30px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2>Translations ({translations.length})</h2>
          <button
            onClick={() => setShowAddTranslation(!showAddTranslation)}
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
            {showAddTranslation ? '✕ Cancel' : '+ Add Translation'}
          </button>
        </div>

        {showAddTranslation && (
          <form onSubmit={handleAddTranslation} className="transcription-form" style={{ marginBottom: '20px' }}>
            <div className="form-group">
              <label htmlFor="target_language">Target Language:</label>
              <select
                id="target_language"
                value={newTranslation.target_language}
                onChange={(e) => setNewTranslation({ ...newTranslation, target_language: e.target.value })}
              >
                <option value="en">English</option>
                <option value="he">Hebrew</option>
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
              <div className="checkbox-group" style={{ marginBottom: '10px' }}>
                <input
                  type="checkbox"
                  id="auto_translate"
                  checked={newTranslation.auto_translate}
                  onChange={(e) => setNewTranslation({ 
                    ...newTranslation, 
                    auto_translate: e.target.checked,
                    translated_text: e.target.checked ? '' : newTranslation.translated_text
                  })}
                />
                <label htmlFor="auto_translate">Use AI Auto-Translation (OpenAI)</label>
              </div>
              
              {!newTranslation.auto_translate && (
                <>
                  <label htmlFor="translated_text">Manual Translation:</label>
                  <textarea
                    id="translated_text"
                    value={newTranslation.translated_text}
                    onChange={(e) => setNewTranslation({ ...newTranslation, translated_text: e.target.value })}
                    placeholder="Enter the translation here..."
                    required={!newTranslation.auto_translate}
                    style={{
                      width: '100%',
                      minHeight: '150px',
                      padding: '8px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontSize: '16px',
                      boxSizing: 'border-box',
                      fontFamily: 'inherit',
                      resize: 'vertical'
                    }}
                  />
                </>
              )}
              
              {newTranslation.auto_translate && (
                <div style={{
                  padding: '10px',
                  backgroundColor: '#e7f3ff',
                  border: '1px solid #b3d9ff',
                  borderRadius: '4px',
                  fontSize: '14px',
                  color: '#0066cc'
                }}>
                  🤖 AI will automatically translate both the text and VTT content to {newTranslation.target_language.toUpperCase()}
                </div>
              )}
            </div>
            
            <button type="submit">
              Add Translation
            </button>
          </form>
        )}

        {translations.length === 0 ? (
          <div className="status">
            No translations available yet.
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '15px' }}>
            {translations.map((translation) => (
              <div key={translation.id} className="transcription-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                  <h3 style={{ margin: 0 }}>
                    Translation to {translation.target_language.toUpperCase()}
                  </h3>
                  <span style={{ fontSize: '12px', color: '#666' }}>
                    {new Date(translation.created_at).toLocaleString()}
                  </span>
                </div>
                
                <div className="transcript" style={{ marginBottom: '15px' }}>
                  {translation.translated_text}
                </div>
                
                {translation.translated_vtt && (
                  <div>
                    <button
                      onClick={() => {
                        const blob = new Blob([translation.translated_vtt], { type: 'text/vtt' })
                        const url = URL.createObjectURL(blob)
                        const a = document.createElement('a')
                        a.href = url
                        a.download = `${transcription?.title || 'transcript'}_${translation.target_language}.vtt`
                        document.body.appendChild(a)
                        a.click()
                        document.body.removeChild(a)
                        URL.revokeObjectURL(url)
                      }}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: '#28a745',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        fontSize: '14px',
                        cursor: 'pointer'
                      }}
                    >
                      📥 Download Translated VTT
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default TranscriptView
