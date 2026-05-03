import { useState, useRef, useEffect } from 'react'

// Enhanced markdown renderer
function renderMarkdown(text) {
  if (!text) return ''
  
  let html = text
  
  // Escape HTML first
  html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  
  // Code blocks with language
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (match, lang, code) => {
    const language = lang || 'text'
    return `<pre class="code-block" data-language="${language}"><code class="language-${language}">${code.trim()}</code></pre>`
  })
  
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
  
  // Bold
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  
  // Italic
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  
  // Strikethrough
  html = html.replace(/~~([^~]+)~~/g, '<del>$1</del>')
  
  // Headers
  html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>')
  html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>')
  
  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
  
  // Blockquotes
  html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
  
  // Horizontal rule
  html = html.replace(/^---$/gm, '<hr>')
  
  // Unordered lists
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul class="md-list">$&</ul>')
  
  // Paragraphs
  html = html.replace(/\n\n/g, '</p><p>')
  html = '<p>' + html + '</p>'
  
  // Clean up
  html = html.replace(/<p>\s*<\/p>/g, '')
  html = html.replace(/<p>(<pre|<ul|<blockquote|<h[234]>)/g, '$1')
  html = html.replace(/(<\/pre>|<\/ul>|<\/blockquote>|<\/h[234]>)<\/p>/g, '$1')
  html = html.replace(/\n/g, '<br>')
  
  return html
}

export default function ChatArea({ messages, onSend, messagesEndRef, disabled }) {
  const [input, setInput] = useState('')
  const inputRef = useRef(null)
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim() || disabled) return
    onSend(input)
    setInput('')
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
    }
  }
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }
  
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 200) + 'px'
    }
  }, [input])
  
  return (
    <div className="chat">
      {messages.length === 0 ? (
        <div className="chat-empty fade-in">
          <div className="chat-empty-icon">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="0.8">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <h1 className="chat-empty-title">RadCode</h1>
          <p className="chat-empty-subtitle">
            Autonomous AI Software Engineer<br/>
            <span className="chat-empty-hint">Describe what you want to build</span>
          </p>
          
          <div className="example-prompts">
            <button onClick={() => onSend('Create a FastAPI REST API with user authentication')}>
              Create a REST API
            </button>
            <button onClick={() => onSend('Build a React dashboard with charts')}>
              Build a React dashboard
            </button>
            <button onClick={() => onSend('Write tests for my Python code')}>
              Write tests
            </button>
          </div>
        </div>
      ) : (
        <div className="chat-messages">
          {messages.map((msg) => (
            <div key={msg.id} className={`message message-${msg.role === 'user' ? 'user' : 'assistant'} ${msg.status || ''}`}>
              {msg.loading ? (
                <div className="message-loading">
                  <div className="loading-dots">
                    <span></span><span></span><span></span>
                  </div>
                  <span className="loading-text">RadCode is thinking</span>
                </div>
              ) : (
                <>
                  <div className="message-content" dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}/>
                  <div className="message-footer">
                    <span className="message-time">
                      {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    {msg.status === 'success' && (
                      <span className="message-status success">✓ Done</span>
                    )}
                    {msg.status === 'error' && (
                      <span className="message-status error">✕ Failed</span>
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
        <div className="input-container">
          <textarea
            ref={inputRef}
            className="input"
            placeholder={disabled ? "RadCode is working..." : "Message RadCode..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            rows={1}
          />
          <button type="submit" className="input-submit" disabled={!input.trim() || disabled}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </div>
        <div className="input-footer">
          <span className="input-hint">
            <kbd>Enter</kbd> to send · <kbd>Shift + Enter</kbd> for new line
          </span>
        </div>
      </form>
    </div>
  )
}
