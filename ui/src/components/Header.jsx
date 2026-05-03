import { useState, useEffect } from 'react'

export default function Header({ onMenuClick, workspace, taskStatus, onWorkspaceChange }) {
  const [showWsDropdown, setShowWsDropdown] = useState(false)
  const [wsList, setWsList] = useState([])
  
  useEffect(() => {
    fetch('/api/v1/workspaces')
      .then(r => r.json())
      .then(d => setWsList(d.workspaces || []))
      .catch(() => setWsList([{ name: 'default' }]))
  }, [])
  
  const statusColors = {
    running: 'task-status-running',
    success: 'task-status-success',
    failed: 'task-status-error',
    pending: 'task-status-pending'
  }
  
  return (
    <>
      <div className="mobile-header">
        <button className="menu-btn" onClick={onMenuClick}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 12h18M3 6h18M3 18h18"/>
          </svg>
        </button>
        <span className="logo">
          <span className="logo-accent">Rad</span>Code
        </span>
      </div>
      
      <header className="header">
        <div className="header-left" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
          <div 
            className="workspace-selector"
            onClick={() => setShowWsDropdown(!showWsDropdown)}
            style={{ position: 'relative' }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2v11z"/>
            </svg>
            {workspace}
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 9l6 6 6-6"/>
            </svg>
            
            {showWsDropdown && (
              <div style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                marginTop: 'var(--space-xs)',
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-xs)',
                zIndex: 100,
                boxShadow: 'var(--shadow-lg)'
              }}>
                {wsList.map(ws => (
                  <div 
                    key={ws.name}
                    onClick={(e) => {
                      e.stopPropagation()
                      onWorkspaceChange(ws.name)
                      setShowWsDropdown(false)
                    }}
                    style={{
                      padding: 'var(--space-sm) var(--space-md)',
                      borderRadius: 'var(--radius-sm)',
                      cursor: 'pointer',
                      background: ws.name === workspace ? 'var(--accent-glow)' : 'transparent'
                    }}
                  >
                    {ws.name}
                  </div>
                ))}
              </div>
            )}
          </div>
          
          {taskStatus && (
            <div className={`task-status ${statusColors[taskStatus] || 'task-status-pending'}`}>
              {taskStatus === 'running' && <div className="loading-spinner" />}
              {taskStatus}
            </div>
          )}
        </div>
        
        <div className="header-actions">
          <button className="header-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 20V10M12 20V4M6 20v-6"/>
            </svg>
          </button>
          <button className="header-btn">Settings</button>
        </div>
      </header>
    </>
  )
}