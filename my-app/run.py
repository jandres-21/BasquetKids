import os
from app import app

# Importa tus routers para registrar las rutas
from routers.router_login import *
from routers.router_home import *
from routers.router_page_not_found import *

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))  # Puerto que Cloud Run asigna (8080)
    app.run(host='0.0.0.0', port=port)
