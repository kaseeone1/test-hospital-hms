from app import app
from config import HOST, PORT, DEBUG

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    import os
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    
    # Run the application
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG
    )
