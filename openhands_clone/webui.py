"""
RadCod Web UI
============
Web-based interface for the coding agent.

Features:
- Chat interface
- Code editor
- Terminal output
- File browser
"""

import os
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# Templates
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RadCod - Agentic Coding</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1e1e2e;
            color: #cdd6f4;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        header {
            background: #181825;
            padding: 12px 20px;
            border-bottom: 1px solid #313244;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        h1 { font-size: 18px; color: #89b4fa; }
        .status { font-size: 12px; color: #a6adc8; }
        .main { flex: 1; display: flex; overflow: hidden; }
        .sidebar {
            width: 250px;
            background: #181825;
            border-right: 1px solid #313244;
            padding: 10px;
            overflow-y: auto;
        }
        .chat {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
        }
        .message {
            margin-bottom: 16px;
            padding: 12px 16px;
            border-radius: 8px;
            max-width: 80%;
        }
        .message.user {
            background: #45475a;
            margin-left: auto;
        }
        .message.assistant {
            background: #313244;
        }
        .message .content { white-space: pre-wrap; }
        .input-area {
            padding: 16px;
            background: #181825;
            border-top: 1px solid #313244;
            display: flex;
            gap: 10px;
        }
        input {
            flex: 1;
            padding: 12px 16px;
            border-radius: 8px;
            border: 1px solid #45475a;
            background: #313244;
            color: #cdd6f4;
            font-size: 14px;
        }
        input:focus { outline: none; border-color: #89b4fa; }
        button {
            padding: 12px 24px;
            border-radius: 8px;
            border: none;
            background: #89b4fa;
            color: #1e1e2e;
            font-weight: 600;
            cursor: pointer;
        }
        button:hover { background: #b4befe; }
        .tabs { display: flex; gap: 2px; margin-bottom: 10px; }
        .tab {
            padding: 8px 16px;
            background: #313244;
            border: none;
            color: #a6adc8;
            cursor: pointer;
            font-size: 12px;
        }
        .tab.active { background: #45475a; color: #cdd6f4; }
        .file-tree { font-size: 12px; }
        .file-item {
            padding: 4px 8px;
            cursor: pointer;
            border-radius: 4px;
        }
        .file-item:hover { background: #313244; }
        .terminal {
            background: #11111b;
            padding: 10px;
            font-family: monospace;
            font-size: 12px;
            height: 200px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <header>
        <h1>🤖 RadCod</h1>
        <span class="status" id="status">Ready</span>
    </header>
    <div class="main">
        <div class="sidebar">
            <div class="tabs">
                <button class="tab active" onclick="showTab('files')">Files</button>
                <button class="tab" onclick="showTab('terminal')">Terminal</button>
            </div>
            <div id="files" class="file-tree"></div>
            <div id="terminal" class="terminal" style="display:none;"></div>
        </div>
        <div class="chat">
            <div class="messages" id="messages"></div>
            <div class="input-area">
                <input type="text" id="input" placeholder="Enter task..." onkeypress="handleKey(event)">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>
    <script>
        const input = document.getElementById('input');
        const messages = document.getElementById('messages');
        
        function handleKey(e) { if (e.key === 'Enter') sendMessage(); }
        
        function showTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('files').style.display = tab === 'files' ? 'block' : 'none';
            document.getElementById('terminal').style.display = tab === 'terminal' ? 'block' : 'none';
        }
        
        function addMessage(role, content) {
            const div = document.createElement('div');
            div.className = `message ${role}`;
            div.innerHTML = `<div class="content">${escapeHtml(content)}</div>`;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function escapeHtml(text) {
            return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }
        
        async function sendMessage() {
            const task = input.value.trim();
            if (!task) return;
            input.value = '';
            addMessage('user', task);
            document.getElementById('status').textContent = 'Running...';
            
            try {
                const response = await fetch('/api/execute', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({task})
                });
                const result = await response.json();
                addMessage('assistant', result.result || result.error);
            } catch (e) {
                addMessage('assistant', 'Error: ' + e.message);
            }
            document.getElementById('status').textContent = 'Ready';
        }
        
        // Load files
        fetch('/api/files').then(r => r.json()).then(files => {
            document.getElementById('files').innerHTML = files.map(f => 
                `<div class="file-item">📄 ${f}</div>`
            ).join('');
        });
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    """Main page."""
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/execute", methods=["POST"])
def execute():
    """Execute a task."""
    from openhands_clone.agentic import execute_task
    
    data = request.get_json()
    task = data.get("task", "")
    
    try:
        result = execute_task(task=task, verbose=True)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/files", methods=["GET"])
def list_files():
    """List workspace files."""
    workspace = os.getcwd()
    files = []
    for root, dirs, filenames in os.walk(workspace):
        for f in filenames:
            if not f.startswith('.'):
                rel = os.path.relpath(os.path.join(root, f), workspace)
                files.append(rel)
    return jsonify(files[:50])  # Limit


@app.route("/api/workspace", methods=["GET", "POST"])
def workspace():
    """Get/set workspace path."""
    global workspace_path
    if request.method == "POST":
        data = request.get_json()
        workspace_path = data.get("path", os.getcwd())
    return jsonify({"workspace": workspace_path})


if __name__ == "__main__":
    workspace_path = os.getcwd()
    app.run(host="0.0.0.0", port=8080)