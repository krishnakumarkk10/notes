from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import json


app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, cors_allowed_origins="*")

docs = {}  # In-memory store for document contents per room


def get_doc_path(doc_id):
    return f"documents/{doc_id}.json"


def load_document(doc_id):
    path = get_doc_path(doc_id)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except json.JSONDecodeError:
            print(f"⚠️ Warning: Corrupted JSON in {path}, starting fresh.")
            return []
    return []


def save_document(doc_id, content):
    os.makedirs("documents", exist_ok=True)
    path = get_doc_path(doc_id)
    with open(path, "w") as f:
        json.dump(content, f)


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("join")
def handle_join(data):
    room = data["room"]
    join_room(room)

    if room not in docs:
        docs[room] = load_document(room)

    emit("load", docs[room], room=request.sid)


@socketio.on("edit")
def handle_edit(data):
    room = data["room"]
    delta = data["delta"]

    # Ensure room exists
    if room not in docs:
        docs[room] = load_document(room)  # Fallback to loading from file

    docs[room].append(delta)
    save_document(room, docs[room])
    emit("update", delta, room=room, include_self=False)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
