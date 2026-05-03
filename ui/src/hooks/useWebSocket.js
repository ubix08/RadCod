import { useEffect, useRef, useCallback } from 'react'

export function useWebSocket(url = '/ws') {
  const wsRef = useRef(null)
  const listenersRef = useRef(new Set())
  
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}${url}`
    
    try {
      wsRef.current = new WebSocket(wsUrl)
      
      wsRef.current.onopen = () => {
        console.log('WS connected')
      }
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          listenersRef.current.forEach(fn => fn(data))
        } catch (e) {
          console.error('WS parse error:', e)
        }
      }
      
      wsRef.current.onclose = () => {
        console.log('WS disconnected')
        // Reconnect after 3s
        setTimeout(connect, 3000)
      }
      
      wsRef.current.onerror = (error) => {
        console.error('WS error:', error)
      }
    } catch (e) {
      console.error('WS connect error:', e)
    }
  }, [url])
  
  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
    }
  }, [connect])
  
  const onMessage = useCallback((fn) => {
    listenersRef.current.add(fn)
    return () => listenersRef.current.delete(fn)
  }, [])
  
  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])
  
  return { onMessage, send, connected: wsRef.current?.readyState === WebSocket.OPEN }
}

export function useTaskPolling(taskId, onUpdate) {
  useEffect(() => {
    if (!taskId) return
    
    const poll = async () => {
      try {
        const res = await fetch(`/api/v1/tasks/${taskId}`)
        const data = await res.json()
        onUpdate(data)
        
        if (!['pending', 'running'].includes(data.status)) {
          return true // Stop polling
        }
      } catch (e) {
        console.error('Poll error:', e)
      }
      return false
    }
    
    let interval = setInterval(async () => {
      const stop = await poll()
      if (stop) clearInterval(interval)
    }, 2000)
    
    poll()
    
    return () => clearInterval(interval)
  }, [taskId, onUpdate])
}