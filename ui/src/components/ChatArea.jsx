import { useState, useRef } from 'react'

export default function ChatArea({ messages, onSend, messagesEndRef }) {
  const [input, setInput] = useState('')
  const inputRef = useRef(null)
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim()) return
    onSend(input)
    setInput('')
  }
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }
  
  return (
    <div className="chat">
      {messages.length === 0 ? (
        <div className="chat-empty fade-in">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="1.5" style={{ marginBottom: 'var(--space-md)', opacity: 0.8 }}>
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2v10z"/>
          </svg>
          <div className="chat-empty-title">What would you like to build?</div>
          <div className="chat-empty-subtitle">
            Describe what you want to create. RadCode will plan, implement, and deploy your project.
          </div>
        </div>
      ) : (
        <div className="chat-messages">
          {messages.map(msg => (
            <div 
              key={msg.id} 
              className={`message message-${msg.role === 'user' ? 'user' : 'assistant'} fade-in`}
            >
              {msg.loading ? (
                <div className="loading">
                  <div className="loading-spinner" />
                  <span>Thinking...</span>
                </div>
              ) : (
                <>
                  <div className="message-content">{msg.content}</div>
                  <div className="message-time">
                    {new Date(msg.timestamp).toLocaleTimeString()}
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
            placeholder="Describe what you want to build..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
          />
          <button 
            type="submit" 
            className="input-submit"
            disabled={!input.trim()}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
            </svg>
          </button>
        </div>
      </form>
    </div>
  )
}