from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    # Port 5001 pour éviter les conflits
    socketio.run(app, debug=True, port=10000)
