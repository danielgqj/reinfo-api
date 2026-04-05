from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import geopandas as gpd
from sqlalchemy import create_engine
import os
from pathlib import Path
from dotenv import load_dotenv
import json
import uvicorn

# 1. Cargar variables de entorno (.env)
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

app = FastAPI(title="API REINFO - Modo Nube")

# 2. Configurar CORS (Vital para que el mapa funcione en la web)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Conexión a Neon
# Obtenemos la URL larga que pegaste en el .env
DATABASE_URL = os.getenv('DATABASE_URL')

# Creamos el motor de conexión con soporte para SSL (requerido por Neon)
engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})

@app.get("/")
def home():
    return {
        "status": "online", 
        "database": "Neon Cloud",
        "endpoint": "/puntos-reinfo"
    }

@app.get("/puntos-reinfo")
def obtener_puntos():
    try:
        # Consulta a la tabla que acabas de subir
        query = "SELECT * FROM reinfo_residuos"
        
        # Leemos de PostGIS usando GeoPandas
        gdf = gpd.read_postgis(query, engine, geom_col='geometry')
        
        # Convertimos el resultado a GeoJSON
        return json.loads(gdf.to_json())
    
    except Exception as e:
        return {"error": str(e), "detalle": "Asegúrate de que la tabla 'reinfo_residuos' exista en Neon"}

if __name__ == "__main__":
    # El puerto 8000 es el estándar, pero Render usará el que le asigne el sistema
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)