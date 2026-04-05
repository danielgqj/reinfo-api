from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import geopandas as gpd
from sqlalchemy import create_engine
import os
from pathlib import Path
from dotenv import load_dotenv
import json
import uvicorn

# 1. Cargar variables de entorno
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

app = FastAPI(title="API REINFO - Dashboard Mode")

# ---------------------------------------------------------
# CONFIGURACIÓN DE CORS - ESTO ARREGLA EL ERROR DE CONEXIÓN
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite que tu GitHub Pages acceda a los datos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Conexión a Neon
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})

@app.get("/")
def home():
    return {
        "status": "online", 
        "endpoint": "/puntos-reinfo"
    }

@app.get("/puntos-reinfo")
def obtener_puntos():
    try:
        # Consulta a tu tabla en Neon
        query = "SELECT * FROM reinfo_residuos"
        
        # Leemos los datos espaciales
        gdf = gpd.read_postgis(query, engine, geom_col='geometry')
        
        # Extraemos coordenadas para que Leaflet las reconozca como p.lat y p.lon
        gdf['lat'] = gdf.geometry.y
        gdf['lon'] = gdf.geometry.x
        
        # Quitamos la columna geometry (no se puede enviar por JSON estándar)
        df_final = gdf.drop(columns=['geometry'])
        
        # Convertimos a lista de diccionarios (Formato JSON simple para el Dashboard)
        return json.loads(df_final.to_json(orient='records'))
    
    except Exception as e:
        return {"error": str(e), "detalle": "Error al procesar la tabla 'reinfo_residuos'"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
