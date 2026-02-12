import requests
import firebase_admin
from firebase_admin import credentials, db
import time
import os
import json
import random

# --- CONFIGURACIÓN DE IDENTIFICACIÓN ---
ORIGEN = "ghac" # ghac (GitHub Actions Cron) o tcm (Termux Cron Mobile)

# --- CONFIGURACIÓN DE RUTAS ---
base_path = os.path.dirname(os.path.abspath(__file__))
ruta_json = os.path.join(base_path, 'serviceAccountKey.json')

# --- CONFIGURACIÓN DE FIREBASE ---
if not firebase_admin._apps:
    sec_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
    if sec_json:
        cred = credentials.Certificate(json.loads(sec_json))
    else:
        cred = credentials.Certificate(ruta_json)
    firebase_admin.initialize_app(cred, {'databaseURL': 'https://test-gh-actions-cron-default-rtdb.firebaseio.com/'})

# --- PROVEEDORES (APIS) ---
def get_from_coingecko():
    res = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10).json()
    return float(res['bitcoin']['usd'])

def get_from_cryptocompare():
    res = requests.get("https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD", timeout=10).json()
    return float(res['USD'])

def get_from_kucoin():
    res = requests.get("https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=BTC-USDT", timeout=10).json()
    return float(res['data']['price'])

# --- LÓGICA DE ROTACIÓN ---
def get_robust_price():
    sources = [
        ("CoinGecko", get_from_coingecko),
        ("CryptoCompare", get_from_cryptocompare),
        ("KuCoin", get_from_kucoin)
    ]
    
    random.shuffle(sources)
    
    for name, func in sources:
        try:
            print(f"🔄 {ORIGEN} intentando con: {name}...")
            price = func()
            return price, name
        except Exception as e:
            print(f"⚠️ {name} falló. Saltando...")
            continue
            
    return None, None

def upload_to_firebase():
    price, api_usada = get_robust_price()
    if price:
        # Guardamos en la DB con los nuevos marcadores
        db.reference('prices').push({
            'price': price,
            'timestamp': int(time.time() * 1000),
            'api_source': api_usada, # Ejemplo: "CoinGecko"
            'device_origin': ORIGEN   # Ejemplo: "tcm" o "ghac"
        })
        print(f"✅ [{ORIGEN}] Sincronización exitosa vía {api_usada}.")
    else:
        print(f"🚨 [{ORIGEN}] ERROR: Todas las APIs fallaron.")

if __name__ == "__main__":
    upload_to_firebase()