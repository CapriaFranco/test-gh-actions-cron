import requests
import firebase_admin
from firebase_admin import credentials, db
import time
import os
import json

# Configuración de Firebase
if not firebase_admin._apps:
    sec_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
    if sec_json:
        cred_dict = json.loads(sec_json)
        cred = credentials.Certificate(cred_dict)
    else:
        cred = credentials.Certificate("serviceAccountKey.json")
        
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://test-gh-actions-cron-default-rtdb.firebaseio.com/'
    })

def get_crypto_price():
    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
    # Añadimos un Header para "engañar" un poco a Binance
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if 'price' in data:
            return float(data['price'])
        else:
            # ESTO ES CLAVE: Si falla, veremos en el log de GitHub qué respondió Binance
            print(f"DEBUG - Respuesta completa de Binance: {data}")
            return None
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

def upload_to_firebase():
    price = get_crypto_price()
    if price:
        ref = db.reference('prices')
        ref.push({
            'price': price,
            'timestamp': int(time.time() * 1000)
        })
        print(f"Subido con éxito: ${price}")
    else:
        print("No se pudo subir nada debido al error en la API.")

if __name__ == "__main__":
    upload_to_firebase()