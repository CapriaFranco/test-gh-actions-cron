import requests
import firebase_admin
from firebase_admin import credentials, db
import time
import os
import json

# --- Configuración de Firebase ---
if not firebase_admin._apps:
    sec_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
    cred = credentials.Certificate(json.loads(sec_json)) if sec_json else credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {'databaseURL': 'https://test-gh-actions-cron-default-rtdb.firebaseio.com/'})

# --- Proveedores de Precios ---

def get_from_coingecko():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    res = requests.get(url, timeout=10).json()
    return float(res['bitcoin']['usd'])

def get_from_cryptocompare():
    url = "https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD"
    res = requests.get(url, timeout=10).json()
    return float(res['USD'])

def get_from_kucoin():
    url = "https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=BTC-USDT"
    res = requests.get(url, timeout=10).json()
    return float(res['data']['price'])

# --- Lógica Robusta ---

def get_robust_price():
    # Lista de funciones a intentar
    sources = [
        ("CoinGecko", get_from_coingecko),
        ("CryptoCompare", get_from_cryptocompare),
        ("KuCoin", get_from_kucoin)
    ]
    
    for name, func in sources:
        try:
            price = func()
            print(f"✅ Precio obtenido de {name}: ${price}")
            return price
        except Exception as e:
            print(f"❌ {name} falló: {e}")
            continue # Salta a la siguiente fuente
            
    return None # Si todas fallan

def upload_to_firebase():
    price = get_robust_price()
    if price:
        db.reference('prices').push({
            'price': price,
            'timestamp': int(time.time() * 1000),
            'source': "Multi-API" # Opcional: para saber que funcionó el fallback
        })
        print("Sincronización exitosa.")
    else:
        print("CRITICAL: Todas las fuentes fallaron.")

if __name__ == "__main__":
    upload_to_firebase()