from django.urls import path
from .views import *

urlpatterns = [
    path('users/register', UserRegistrationView.as_view(), name='user-register'),
    path('users/login', UserLoginView.as_view(), name='user-login'),
    path('dashboard/user', GetUserInfoView.as_view(), name='user-info'),
    path('dashboard/account', GetAccountInfoView.as_view(), name='account-info'),
    path('users/logout', LogoutView.as_view(), name='user-logout'),
    path('auth/password-reset/send-otp', SendOTPView.as_view(), name='send-otp'),
    path('auth/password-reset/verify-otp', VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/password-reset', ResetPasswordView.as_view(), name='reset-password'),
    path('account/create-pin', CreatePINView.as_view(), name='create-pin'),
    path('account/update-pin', UpdatePINView.as_view(), name='update-pin'),
    path('account/deposit', DepositMoneyView.as_view(), name='account-deposit'),
    path('account/withdraw', WithdrawMoneyView.as_view(), name='account-withdraw'),
    path('account/fund-transfer', TransferFundsView.as_view(), name='fund-transfer'),
    path('account/transactions', TransactionHistoryView.as_view(), name='transaction-history'),
    path('account/buy-asset', BuyAssetView.as_view(), name='buy-asset'),
    path('account/sell-asset', SellAssetView.as_view(), name='sell-asset'),
    path('account/assets', UserAssetInfoView.as_view(), name='user-assets'),
    path('account/net-worth', NetWorthView.as_view(), name='user-net-worth'),
    path('user-actions/suscribe', CreateSubscriptionView.as_view(), name='suscribe'),
    path('user-actions/enable-auto-invest', EnableAutoInvestView.as_view(), name='enable-auto-invest')
]
