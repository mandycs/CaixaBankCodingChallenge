import requests

def get_market_price(asset_symbol):
    url = "https://faas-lon1-917a94a7.doserverless.co/api/v1/web/fn-e0f31110-7521-4cb9-86a2-645f66eefb63/default/market-prices-simulator"
    
    try:
        # Realizar la solicitud GET a la API
        response = requests.get(url)
        response.raise_for_status()  # Lanza un error si el código de estado es 4xx o 5xx
        data = response.json()
        
        # Verificar que el símbolo del activo está presente en la respuesta
        if asset_symbol not in data:
            raise ValueError(f"El precio para el activo '{asset_symbol}' no se encontró en la respuesta.")
        
        # Retornar el precio del activo
        return float(data[asset_symbol])
    
    except requests.RequestException as e:
        print(f"Error al conectar con la API de precios: {e}")
        raise ValueError(f"No se pudo obtener el precio para el activo '{asset_symbol}'.")
