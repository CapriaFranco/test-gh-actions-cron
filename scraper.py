import requests
import firebase_admin
from firebase_admin import credentials, db
import time
import os
import json
import random  # <-- Nueva librería para rotar

# --- Configuración de Rutas ---
base_path = os.path.dirname(os.path.abspath(__file__))
ruta_json = os.path.join(base_path, 'serviceAccountKey.json')

# --- Configuración de Firebase ---
if not firebase_admin._apps:
    sec_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
    if sec_json:
        cred = credentials.Certificate(json.loads(sec_json))
    else:
        cred = credentials.Certificate(ruta_json)
    firebase_admin.initialize_app(cred, {'databaseURL': 'https://test-gh-actions-cron-default-rtdb.firebaseio.com/'})

# --- Proveedores (APIs) ---
def get_from_coingecko():
    res = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10).json()
    return float(res['bitcoin']['usd'])

def get_from_cryptocompare():
    res = requests.get("https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD", timeout=10).json()
    return float(res['USD'])

def get_from_kucoin():
    res = requests.get("https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=BTC-USDT", timeout=10).json()
    return float(res['data']['price'])

# --- Lógica de Rotación y Fallback ---
def get_robust_price():
    sources = [
        ("CoinGecko", get_from_coingecko),
        ("CryptoCompare", get_from_cryptocompare),
        ("KuCoin", get_from_kucoin)
    ]
    
    # ROTACIÓN: Mezclamos la lista para que no siempre empiece por la misma
    random.shuffle(sources)
    
    for name, func in sources:
        try:
            print(f"🔄 Intentando con: {name}...")
            price = func()
            return price, name # Retornamos también el nombre para saber cuál ganó
        except Exception as e:
            print(f"⚠️ {name} falló o está saturada. Saltando...")
            continue
            
    return None, None

def upload_to_firebase():
    price, source_name = get_robust_price()
    if price:
        db.reference('prices').push({
            'price': price,
            'timestamp': int(time.time() * 1000),
            'source': source_name  # Guardamos cuál API se usó esta vez
        })
        print(f"✅ Sincronización exitosa vía {source_name}.")
    else:
        print("🚨 ERROR CRÍTICO: Todas las APIs fallaron.")

if __name__ == "__main__":
    upload_to_firebase()