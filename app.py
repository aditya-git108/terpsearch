from terpsearch.website import create_app
from asgiref.wsgi import WsgiToAsgi
import os

FLASK_MODE = os.getenv("FLASK_MODE", "DEV").upper()
app = create_app()
if FLASK_MODE == 'PROD':
    app = WsgiToAsgi(app)

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=5000)