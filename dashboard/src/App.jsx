import React, { useState, useEffect } from 'react'

function App() {
  const [apps, setApps] = useState([])

  useEffect(() => {
    const fetchApps = () => {
      fetch('/api/apps')
        .then(response => response.json())
        .then(data => setApps(data))
        .catch(error => console.error('Error fetching apps:', error))
    }

    fetchApps() // Initial fetch
    const interval = setInterval(fetchApps, 3000) // Poll every 3 seconds

    return () => clearInterval(interval) // Cleanup
  }, [])

  const createNewApp = async () => {
    const name = prompt("Enter app name:")
    if (!name) return
    const template = prompt("Enter template (crm/inventory):")
    if (!template) return

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, template })
      })
      const result = await response.json()
      alert(result.message)
    } catch (error) {
      console.error('Error generating app:', error)
    }
  }

  return (
    <div className="App" style={{ padding: '20px' }}>
      <h1>RadCod Central Dashboard</h1>
      <section>
        <h2>Managed Applications</h2>
        <button onClick={createNewApp}>Create New App</button>
        <ul>
          {apps.map(app => (
            <li key={app.id} style={{ marginBottom: '10px' }}>
              <strong>{app.name}</strong> ({app.template}) - 
              Status: <span style={{ color: app.status === 'running' ? 'green' : 'red' }}>{app.status}</span>
              {app.url && <a href={app.url} target="_blank" rel="noopener noreferrer"> View</a>}
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

export default App
