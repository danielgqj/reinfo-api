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

app = FastAPI(title="API REINFO & ENAHO - Dashboard Mode")

# ---------------------------------------------------------
# CONFIGURACIÓN DE CORS
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        "endpoints": ["/puntos-reinfo", "/capa-enaho"]
    }

# --- RUTA EXISTENTE: Puntos REINFO ---
@app.get("/puntos-reinfo")
def obtener_puntos():
    try:
        query = "SELECT * FROM reinfo_residuos"
        gdf = gpd.read_postgis(query, engine, geom_col='geometry')
        
        # Coordenadas para Leaflet
        gdf['lat'] = gdf.geometry.y
        gdf['lon'] = gdf.geometry.x
        
        df_final = gdf.drop(columns=['geometry'])
        return json.loads(df_final.to_json(orient='records'))
    
    except Exception as e:
        return {"error": str(e), "detalle": "Error en tabla 'reinfo_residuos'"}

# --- NUEVA RUTA: Capa ENAHO (Polígonos/Áreas) ---
@app.get("/capa-enaho")
def obtener_enaho():
    try:
        # Usamos el nombre exacto de la tabla que subiste con el script anterior
        query = "SELECT * FROM indice_dependencia_enaho_2024"
        
        # Leemos de Neon
        gdf = gpd.read_postgis(query, engine, geom_col='geometry')
        
        # Importante: Como son polígonos, usamos GeoJSON puro (to_json)
        # Esto permite que Leaflet dibuje las formas de los distritos correctamente
        return json.loads(gdf.to_json())
    
    except Exception as e:
        return {"error": str(e), "detalle": "Error en tabla 'indice_dependencia_enaho_2024'"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
