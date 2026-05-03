import { useState, useRef, useEffect } from 'react'

// Simple markdown renderer
function renderMarkdown(text) {
  if (!text) return ''
  
  // Code blocks
  let html = text.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre><code class="language-${lang}">${escapeHtml(code.trim())}</code></pre>`
  })
  
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')
  
  // Bold
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  
  // Italic
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  
  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
  
  // Lists
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
  
  // Line breaks
  html = html.replace(/\n/g, '<br>')
  
  return html
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

export default function ChatArea({ messages, onSend, messagesEndRef, disabled }) {
  const [input, setInput] = useState('')
  const inputRef = useRef(null)
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim() || disabled) return
    onSend(input)
    setInput('')
  }
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }
  
  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 150) + 'px'
    }
  }, [input])
  
  return (
    <div className="chat">
      {messages.length === 0 ? (
        <div className="chat-empty fade-in">
          <div className="chat-empty-icon">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div className="chat-empty-title">RadCode</div>
          <div className="chat-empty-subtitle">
            Autonomous AI Software Engineer<br/>
            Describe what you want to build, and I'll implement it.
          </div>
        </div>
      ) : (
        <div className="chat-messages">
          {messages.map((msg) => (
            <div 
              key={msg.id} 
              className={`message message-${msg.role === 'user' ? 'user' : 'assistant'} ${msg.status || ''}`}
            >
              {msg.loading ? (
                <div className="loading">
                  <div className="loading-spinner" />
                  <span>Thinking...</span>
                  {msg.progress && (
                    <span className="loading-step">Step {msg.progress.step}</span>
                  )}
                </div>
              ) : (
                <>
                  <div 
                    className="message-content" 
                    dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
                  />
                  <div className="message-meta">
                    <span className="message-time">
                      {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    {msg.status === 'success' && (
                      <span className="message-status success">✓</span>
                    )}
                    {msg.status === 'error' && (
                      <span className="message-status error">✕</span>
                    )}
                  </div>
                </>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      )}
      
      <form className="input-area" onSubmit={handleSubmit}>
        <div className="input-wrapper">
          <textarea
            ref={inputRef}
            className="input"
            placeholder="Message RadCode..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            rows={1}
          />
          <button 
            type="submit" 
            className="input-submit"
            disabled={!input.trim() || disabled}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
            </svg>
          </button>
        </div>
        <div className="input-hint">
          Press <kbd>Enter</kbd> to send, <kbd>Shift + Enter</kbd> for new line
        </div>
      </form>
    </div>
  )
}
