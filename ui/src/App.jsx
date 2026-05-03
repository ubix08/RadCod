import { useState, useRef, useEffect, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import ChatArea from './components/ChatArea'
import Header from './components/Header'
import { useWebSocket, useTaskPolling } from './hooks/useWebSocket'

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [taskStatus, setTaskStatus] = useState(null)
  const [currentTaskId, setCurrentTaskId] = useState(null)
  const [workspace, setWorkspace] = useState('default')
  const [isLoading, setIsLoading] = useState(false)
  const [systemStatus, setSystemStatus] = useState(null)
  const messagesEndRef = useRef(null)
  
  const { onMessage } = useWebSocket()
  
  // Fetch system health on mount
  useEffect(() => {
    fetchSystemStatus()
  }, [])
  
  const fetchSystemStatus = async () => {
    try {
      const res = await fetch('/api/v1/health')
      const data = await res.json()
      setSystemStatus(data)
    } catch (e) {
      setSystemStatus({ status: 'offline' })
    }
  }
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }
  
  useEffect(() => {
    scrollToBottom()
  }, [messages])
  
  // Listen for WebSocket progress updates
  useEffect(() => {
    const unsubscribe = onMessage((data) => {
      if (data.step !== undefined) {
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1]
          if (lastMsg?.role === 'assistant') {
            return [...prev.slice(0, -1), {
              ...lastMsg,
              content: data.action || `Step ${data.step}: Working...`,
              progress: data
            }]
          }
          return prev
        })
      }
    })
    return unsubscribe
  }, [onMessage])
  
  const handleSend = useCallback(async (text) => {
    if (!text.trim() || isLoading) return
    
    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: Date.now()
    }
    
    setMessages(prev => [...prev, userMsg])
    
    const assistantMsgId = `assistant-${Date.now()}`
    const assistantMsg = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      loading: true
    }
    
    setMessages(prev => [...prev, assistantMsg])
    setTaskStatus('running')
    setIsLoading(true)
    
    try {
      const response = await fetch('/api/v1/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          request: text,
          workspace,
          timeout_seconds: 600
        })
      })
      
      const data = await response.json()
      
      if (data.task_id) {
        setCurrentTaskId(data.task_id)
      }
    } catch (err) {
      setTaskStatus('error')
      setIsLoading(false)
      setMessages(prev => prev.map(m => 
        m.id === assistantMsgId 
          ? { ...m, content: 'Error: ' + err.message, loading: false }
          : m
      ))
    }
  }, [workspace, isLoading])
  
  // Poll for task completion
  useTaskPolling(currentTaskId, (statusData) => {
    setTaskStatus(statusData.status)
    
    if (statusData.status === 'success' || statusData.status === 'completed') {
      setIsLoading(false)
      setMessages(prev => prev.map(m => {
        if (m.loading) {
          return {
            ...m,
            content: statusData.result || 'Task completed successfully',
            loading: false,
            status: 'success'
          }
        }
        return m
      }))
    } else if (statusData.status === 'failed') {
      setIsLoading(false)
      setMessages(prev => prev.map(m => {
        if (m.loading) {
          return {
            ...m,
            content: statusData.error || 'Task failed',
            loading: false,
            status: 'error'
          }
        }
        return m
      }))
    }
  })
  
  return (
    <div className="app">
      <Sidebar 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)}
        currentWorkspace={workspace}
        onWorkspaceChange={(ws) => {
          setWorkspace(ws)
          setSidebarOpen(false)
        }}
        systemStatus={systemStatus}
      />
      
      <main className="main">
        <Header 
          onMenuClick={() => setSidebarOpen(true)}
          workspace={workspace}
          taskStatus={taskStatus}
          onWorkspaceChange={setWorkspace}
          systemStatus={systemStatus}
        />
        
        <ChatArea 
          messages={messages}
          onSend={handleSend}
          messagesEndRef={messagesEndRef}
          disabled={isLoading}
        />
      </main>
      
      <div 
        className={`overlay ${sidebarOpen ? 'visible' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />
    </div>
  )
}
