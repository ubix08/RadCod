from flask import Flask, jsonify, request
import subprocess
import os
import json

app = Flask(__name__)
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
APPS_JSON_PATH = os.path.join(DASHBOARD_DIR, 'public', 'apps.json')

@app.route('/api/apps', methods=['GET'])
def get_apps():
    if not os.path.exists(APPS_JSON_PATH):
        return jsonify([])
    with open(APPS_JSON_PATH, 'r') as f:
        return jsonify(json.load(f))

@app.route('/api/generate', methods=['POST'])
def generate_app():
    data = request.json
    app_name = data.get('name')
    template = data.get('template')

    # Trigger RadCod generation logic
    # In a real scenario, this would be an asynchronous job or sub-process
    print(f"Generating app '{app_name}' from template '{template}'...")
    
    # Initialize app state
    if os.path.exists(APPS_JSON_PATH):
        with open(APPS_JSON_PATH, 'r') as f:
            apps = json.load(f)
    else:
        apps = []
    
    apps.append({
        "id": f"app-{len(apps)+1}",
        "name": app_name,
        "template": template,
        "status": "generating",
        "url": None
    })
    
    with open(APPS_JSON_PATH, 'w') as f:
        json.dump(apps, f, indent=2)
    
    # Assuming 'radcod' is available as a command-line tool after 'pip install -e .'
    # We use subprocess.Popen to avoid blocking the API response
    try:
        subprocess.Popen([
            "radcod", 
            "--agentic", 
            f"Build a business application named '{app_name}' using the '{template}' template. Once done, update the status to 'running' and set the URL in dashboard/public/apps.json."
        ])
        status = "generating"
    except Exception as e:
        print(f"Error triggering generation: {e}")
        status = "error"

    return jsonify({"status": status, "message": f"Started generation for {app_name}"})

if __name__ == '__main__':
    app.run(port=5000)
