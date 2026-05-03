import { useState, useEffect } from 'react'

export default function Sidebar({ isOpen, onClose, currentWorkspace, onWorkspaceChange }) {
  const [workspaces, setWorkspaces] = useState([])
  const [stats, setStats] = useState({ tasks_completed: 0, tasks_failed: 0 })
  
  useEffect(() => {
    fetchWorkspaces()
  }, [])
  
  const fetchWorkspaces = async () => {
    try {
      const res = await fetch('/api/v1/workspaces')
      const data = await res.json()
      setWorkspaces(data.workspaces || [])
    } catch (e) {
      setWorkspaces([{ name: 'default', task_count: 0 }])
    }
    
    try {
      const res = await fetch('/api/v1/metrics')
      const data = await res.json()
      setStats(data)
    } catch (e) {}
  }
  
  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        <span className="logo">
          <span className="logo-accent">Rad</span>Code
        </span>
      </div>
      
      <nav className="sidebar-nav">
        <div className="nav-section">
          <div className="nav-section-title">Workspace</div>
          <div 
            className={`nav-item ${currentWorkspace === 'default' ? 'active' : ''}`}
            onClick={() => onWorkspaceChange('default')}
          >
            <svg className="nav-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/>
            </svg>
            Default
          </div>
          
          {workspaces.map(ws => (
            ws.name !== 'default' && (
              <div 
                key={ws.name}
                className={`nav-item ${currentWorkspace === ws.name ? 'active' : ''}`}
                onClick={() => onWorkspaceChange(ws.name)}
              >
                <svg className="nav-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2v11z"/>
                </svg>
                {ws.name}
              </div>
            )
          ))}
        </div>
        
        <div className="nav-section">
          <div className="nav-section-title">Quick Actions</div>
          <div className="nav-item">
            <svg className="nav-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14"/>
            </svg>
            New Task
          </div>
          <div className="nav-item">
            <svg className="nav-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>
            </svg>
            Files
          </div>
        </div>
        
        <div className="nav-section">
          <div className="nav-section-title">System</div>
          <div className="nav-item">
            <svg className="nav-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
            Health
          </div>
          <div className="nav-item">
            <svg className="nav-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 20V10M12 20V4M6 20v-6"/>
            </svg>
            Metrics
          </div>
        </div>
        
        <div className="nav-section" style={{ marginTop: 'auto' }}>
          <div style={{ padding: 'var(--space-md)', borderTop: '1px solid var(--border)' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              {stats.tasks_completed} completed
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              {stats.tasks_failed} failed
            </div>
          </div>
        </div>
      </nav>
    </aside>
  )
}