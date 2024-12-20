import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class AllMarketPricesView(APIView):
    def get(self, request):
        try:
            # Realizar solicitud al endpoint de precios de mercado
            response = requests.get("https://faas-lon1-917a94a7.doserverless.co/api/v1/web/fn-e0f31110-7521-4cb9-86a2-645f66eefb63/default/market-prices-simulator")
            response.raise_for_status()  # Verificar si la solicitud fue exitosa
            market_prices = response.json()
            return Response(market_prices, status=status.HTTP_200_OK)
        except requests.RequestException:
            return Response({"detail": "Error retrieving market prices"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IndividualMarketPriceView(APIView):
    def get(self, request, asset_symbol):
        try:
            # Realizar solicitud al endpoint de precios de mercado
            response = requests.get("https://faas-lon1-917a94a7.doserverless.co/api/v1/web/fn-e0f31110-7521-4cb9-86a2-645f66eefb63/default/market-prices-simulator")
            response.raise_for_status()
            market_prices = response.json()

            # Verificar si el símbolo del activo está en los datos de mercado
            if asset_symbol in market_prices:
                return Response({asset_symbol: market_prices[asset_symbol]}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": f"Price for asset {asset_symbol} not found"}, status=status.HTTP_404_NOT_FOUND)
        except requests.RequestException:
            return Response({"detail": "Error retrieving market prices"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
