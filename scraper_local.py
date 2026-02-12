import requests
import firebase_admin
from firebase_admin import credentials, db
import time

# Configuración de Firebase
# Asegúrate de tener el archivo serviceAccountKey.json en la misma carpeta
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://test-gh-actions-cron-default-rtdb.firebaseio.com/'
    })

def get_crypto_price():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        response = requests.get(url, timeout=10)
        data = response.json()
        return float(data['price'])
    except Exception as e:
        print(f"Error al obtener precio: {e}")
        return None

def upload_to_firebase():
    price = get_crypto_price()
    if price:
        ref = db.reference('prices')
        ref.push({
            'price': price,
            'timestamp': int(time.time() * 1000)
        })
        print(f"[{time.strftime('%H:%M:%S')}] Subido: ${price}")

if __name__ == "__main__":
    print("Iniciando scraper local cada 10 segundos... (Ctrl+C para detener)")
    try:
        while True:
            upload_to_firebase()
            time.sleep(10) # Pausa de 10 segundos
    except KeyboardInterrupt:
        print("\nScraper detenido por el usuario.")