from django.urls import path
from .views import AllMarketPricesView, IndividualMarketPriceView

urlpatterns = [
    path('prices', AllMarketPricesView.as_view(), name='all-market-prices'),
    path('prices/<str:asset_symbol>', IndividualMarketPriceView.as_view(), name='individual-market-price'),
]
