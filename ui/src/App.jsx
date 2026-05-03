import { useState, useRef, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import ChatArea from './components/ChatArea'
import Header from './components/Header'
import { useWebSocket, useTaskPolling } from './hooks/useWebSocket'

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [taskStatus, setTaskStatus] = useState(null)
  const [currentTask, setCurrentTask] = useState(null)
  const [workspace, setWorkspace] = useState('default')
  const messagesEndRef = useRef(null)
  
  const { onMessage } = useWebSocket()
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }
  
  useEffect(() => {
    scrollToBottom()
  }, [messages])
  
  // Listen for WebSocket progress updates
  useEffect(() => {
    const unsubscribe = onMessage((data) => {
      if (data.status === 'running') {
        setMessages(prev => [...prev.slice(0, -1), {
          ...prev[prev.length - 1],
          content: data.action || 'Working...'
        }])
      }
    })
    return unsubscribe
  }, [onMessage])
  
  const handleSend = async (text) => {
    if (!text.trim()) return
    
    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: text,
      timestamp: Date.now()
    }
    
    setMessages(prev => [...prev, userMsg])
    
    const assistantMsg = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      loading: true
    }
    
    setMessages(prev => [...prev, assistantMsg])
    setTaskStatus('running')
    
    try {
      const response = await fetch('/api/v1/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          request: text,
          workspace
        })
      })
      
      const data = await response.json()
      setCurrentTask(data.task_id)
      
      // Task status updated via WebSocket or polling
    } catch (err) {
      setTaskStatus('error')
      setMessages(prev => prev.map(m => 
        m.id === assistantMsg.id 
          ? { ...m, content: 'Error: ' + err.message, loading: false }
          : m
      ))
    }
  }
  
  // Poll for task completion
  useTaskPolling(currentTask, (statusData) => {
    setTaskStatus(statusData.status)
    if (statusData.status === 'success' || statusData.status === 'completed') {
      setMessages(prev => prev.map(m => 
        m.id === (currentTask + 1) ? { ...m, content: statusData.result || 'Task completed', loading: false }
          : m
      ))
    } else if (statusData.status === 'failed') {
      setMessages(prev => prev.map(m => 
        m.id === (currentTask + 1) ? { ...m, content: statusData.error || 'Task failed', loading: false }
          : m
      ))
    }
  })
  
  return (
    <div className="app">
      <Sidebar 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)}
        currentWorkspace={workspace}
        onWorkspaceChange={setWorkspace}
      />
      
      <main className="main">
        <Header 
          onMenuClick={() => setSidebarOpen(true)}
          workspace={workspace}
          taskStatus={taskStatus}
          onWorkspaceChange={setWorkspace}
        />
        
        <ChatArea 
          messages={messages}
          onSend={handleSend}
          messagesEndRef={messagesEndRef}
        />
      </main>
      
      <div 
        className={`overlay ${sidebarOpen ? 'visible' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />
    </div>
  )
}