import requests
import firebase_admin
from firebase_admin import credentials, db
import time
import os

# Configuración de Firebase (usando variables de entorno por seguridad)
# Debes descargar tu archivo .json de Firebase y poner su contenido en un Secret de GitHub
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://test-gh-actions-cron-default-rtdb.firebaseio.com/'
    })

def get_crypto_price():
    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
    response = requests.get(url)
    data = response.json()
    return float(data['price'])

def upload_to_firebase():
    price = get_crypto_price()
    ref = db.reference('prices')
    ref.push({
        'price': price,
        'timestamp': int(time.time() * 1000)
    })
    print(f"Subido: ${price}")

if __name__ == "__main__":
    upload_to_firebase()