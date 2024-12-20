from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from .models import CustomUser, BankAccount, Transaction, UserAsset, AutoInvest
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
import random
import uuid
import requests
from decimal import Decimal, InvalidOperation
from .tasks import process_subscriptions, auto_invest_bot


class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "name": user.name,
                "email": user.email,
                "phoneNumber": user.phoneNumber,
                "address": user.address,
                "accountNumber": user.accountNumber,
                "hashedPassword": user.password,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    def post(self, request):
        identifier = request.data.get("identifier")
        password = request.data.get("password")

        # Verifica que tanto identifier como password estén presentes
        if not identifier or not password:
            return Response(
                {"detail": "Identifier and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Intento de búsqueda del usuario por email o accountNumber
        try:
            user = CustomUser.objects.get(
                email=identifier) if "@" in identifier else CustomUser.objects.get(accountNumber=identifier)
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": f"User not found for the given identifier: {identifier}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar la contraseña
        if not user.check_password(password):
            return Response(
                {"detail": "Bad credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generar el token de acceso y el token de refresco
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            },
            status=status.HTTP_200_OK
        )


class GetUserInfoView(APIView):
    permission_classes = [IsAuthenticated]  # Requiere autenticación con JWT

    def get(self, request):
        user = request.user  # Obtiene el usuario autenticado a través del token JWT

        # Retorna la información detallada del usuario
        return Response({
            "name": user.name,
            "email": user.email,
            "phoneNumber": user.phoneNumber,
            "address": user.address,
            "accountNumber": user.accountNumber,
            "hashedPassword": user.password,  # Incluye el hash de la contraseña
        })


class GetAccountInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        account = request.user.account  # Obtiene la cuenta bancaria vinculada al usuario

        return Response({
            "accountNumber": account.accountNumber,
            "balance": account.balance
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Obtiene el token de refresco del cuerpo de la solicitud
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"detail": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Invalida el token de refresco poniéndolo en la lista negra
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"detail": "Logout successful"}, status=status.HTTP_200_RESET_CONTENT)

        except ValidationError:
            return Response({"Access Denied"}, status=status.HTTP_400_BAD_REQUEST)


class SendOTPView(APIView):
    def post(self, request):
        identifier = request.data.get("identifier")

        # Buscar al usuario
        try:
            user = CustomUser.objects.get(email=identifier)
        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Generar OTP
        otp = random.randint(100000, 999999)
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()

        # Enviar OTP por correo
        send_mail(
            subject="Password Reset OTP",
            message=f"OTP: {otp}",
            from_email="no-reply@banking.com",
            recipient_list=[user.email],
        )

        return Response({"message": f"OTP sent successfully to: {user.email}"}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    def post(self, request):
        identifier = request.data.get("identifier")
        otp = request.data.get("otp")

        try:
            user = CustomUser.objects.get(email=identifier, otp=otp)
        except CustomUser.DoesNotExist:
            return Response({"detail": "Invalid OTP or identifier"}, status=status.HTTP_400_BAD_REQUEST)

        # Verificar si el OTP ha caducado (10 minutos de validez)
        if user.otp_created_at and (timezone.now() - user.otp_created_at).total_seconds() > 600:
            return Response({"detail": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST)

        # Generar token de reinicio de contraseña
        reset_token = uuid.uuid4()
        user.password_reset_token = reset_token
        user.otp = None  # Limpiar el OTP una vez usado
        user.otp_created_at = None  # Limpiar el tiempo de creación
        user.save()

        return Response({"passwordResetToken": str(reset_token)}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    def post(self, request):
        identifier = request.data.get("identifier")
        reset_token = request.data.get("resetToken")
        new_password = request.data.get("newPassword")

        try:
            user = CustomUser.objects.get(
                email=identifier, password_reset_token=reset_token)
        except CustomUser.DoesNotExist:
            return Response({"detail": "Invalid reset token or identifier"}, status=status.HTTP_400_BAD_REQUEST)

        # Restablecer la contraseña
        user.password = make_password(new_password)
        user.password_reset_token = None  # Limpiar el token de reinicio una vez usado
        user.save()

        return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)


class CreatePINView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user  # Usuario autenticado por el token JWT
        pin = request.data.get("pin")
        password = request.data.get("password")

        # Verificar la contraseña del usuario
        if not user.check_password(password):
            return Response({"detail": "Incorrect password"}, status=status.HTTP_401_UNAUTHORIZED)

        # Verificar que el PIN no exista aún
        if user.encrypted_pin:
            return Response({"detail": "PIN already set. Use the update PIN option."}, status=status.HTTP_400_BAD_REQUEST)

        # Establecer el PIN
        user.set_pin(pin)
        user.save()
        return Response({"msg": "PIN created successfully"}, status=status.HTTP_200_OK)


class UpdatePINView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user  # Usuario autenticado por el token JWT
        old_pin = request.data.get("oldPin")
        password = request.data.get("password")
        new_pin = request.data.get("newPin")

        # Verificar la contraseña del usuario
        if not user.check_password(password):
            return Response({"detail": "Incorrect password"}, status=status.HTTP_401_UNAUTHORIZED)

        # Verificar el PIN actual
        if not user.check_pin(old_pin):
            return Response({"detail": "Incorrect old PIN"}, status=status.HTTP_401_UNAUTHORIZED)

        # Actualizar el PIN
        user.set_pin(new_pin)
        user.save()
        return Response({"msg": "PIN updated successfully"}, status=status.HTTP_200_OK)


class DepositMoneyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DepositSerializer(data=request.data)

        # Validar los datos con el serializer
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Extraer los datos validados
        pin = serializer.validated_data['pin']
        amount = serializer.validated_data['amount']

        # Verificar que el PIN sea correcto
        user = request.user
        if not user.check_pin(pin):
            return Response({"detail": "Invalid PIN"}, status=status.HTTP_403_FORBIDDEN)

        # Procesar el depósito
        user.account.balance += amount
        user.account.save()

        # Crear la transacción de depósito
        Transaction.objects.create(
            amount=amount,
            transactionType="CASH_DEPOSIT",
            sourceAccount=user.account,
            targetAccount=None,
            transactionDate=timezone.now()
        )

        return Response({"msg": "Cash deposited successfully"}, status=status.HTTP_200_OK)


class WithdrawMoneyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WithdrawSerializer(data=request.data)

        # Validar los datos con el serializer
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        pin = serializer.validated_data['pin']
        amount = serializer.validated_data['amount']
        user = request.user

        # Validar el PIN y el saldo
        if not user.check_pin(pin):
            return Response({"msg": "Invalid PIN"}, status=status.HTTP_403_FORBIDDEN)
        if user.account.balance < amount:
            return Response({"msg": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)

        # Realizar el retiro y actualizar la transacción
        user.account.balance -= amount
        user.account.save()

        Transaction.objects.create(
            amount=amount,
            transactionType="CASH_WITHDRAWAL",
            sourceAccount=user.account,
        )

        return Response({"msg": "Cash withdrawn successfully"}, status=status.HTTP_200_OK)


class TransferFundsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransferFundsSerializer(data=request.data)

        # Validar los datos con el serializer
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        amount = serializer.validated_data['amount']
        pin = serializer.validated_data['pin']
        targetAccount_number = serializer.validated_data['targetAccountNumber']
        user = request.user

        # Validación de PIN y balance
        if not user.check_pin(pin):
            return Response({"msg": "Invalid PIN"}, status=status.HTTP_403_FORBIDDEN)
        if user.account.balance < amount:
            return Response({"msg": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)

        # Validación de cuenta objetivo
        try:
            targetAccount = BankAccount.objects.get(
                accountNumber=targetAccount_number)
        except BankAccount.DoesNotExist:
            return Response({"msg": "Target account not found"}, status=status.HTTP_400_BAD_REQUEST)

        # Realizar la transferencia
        user.account.balance -= amount
        targetAccount.balance += amount
        user.account.save()
        targetAccount.save()

        # Registrar la transacción
        Transaction.objects.create(
            amount=amount,
            transactionType="CASH_TRANSFER",
            sourceAccount=user.account,
            targetAccount=targetAccount,
        )

        return Response({"msg": "Fund transferred successfully"}, status=status.HTTP_200_OK)


class TransactionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = Transaction.objects.filter(
            sourceAccount=request.user.account
        ).order_by("-transactionDate")

        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BuyAssetView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BuyAssetSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        pin = serializer.validated_data['pin']
        amount = serializer.validated_data['amount']
        assetSymbol = serializer.validated_data['assetSymbol']

        # Validar el PIN
        if not user.check_pin(pin):
            return Response({"detail": "Invalid PIN"}, status=status.HTTP_403_FORBIDDEN)

        # Consultar el precio en tiempo real del activo
        try:
            response = requests.get(
                "https://faas-lon1-917a94a7.doserverless.co/api/v1/web/fn-e0f31110-7521-4cb9-86a2-645f66eefb63/default/market-prices-simulator"
            )
            response.raise_for_status()
            prices = response.json()
            current_price = prices.get(assetSymbol)

            if current_price is None:
                return Response({"detail": "Asset not available in market data"}, status=status.HTTP_400_BAD_REQUEST)

            # Convertir el precio a Decimal, manejando errores potenciales
            current_price = Decimal(current_price)
        except (requests.RequestException, InvalidOperation) as e:
            return Response(
                {"detail": "Failed to retrieve asset price or invalid price format"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Calcular la cantidad del activo a comprar
        quantity = amount / current_price

        # Verificar si hay saldo suficiente
        if user.account.balance < amount:
            return Response({"detail": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)

        # Realizar la compra del activo
        user.account.balance -= amount
        user.account.save()

        # Obtener o crear el registro del activo del usuario
        user_asset, created = UserAsset.objects.get_or_create(
            user=user,
            assetSymbol=assetSymbol,
            defaults={'quantity': quantity, 'purchase_price': current_price}
        )

        if not created:
            # Si ya existe, actualizar la cantidad y ajustar el precio promedio de compra
            new_quantity = user_asset.quantity + quantity
            user_asset.purchase_price = (
                (user_asset.purchase_price * user_asset.quantity) +
                (current_price * quantity)
            ) / new_quantity
            user_asset.quantity = new_quantity
            user_asset.save()

        # Registrar la transacción
        Transaction.objects.create(
            amount=amount,
            transactionType="ASSET_PURCHASE",
            sourceAccount=user.account,
            transactionDate=timezone.now(),
        )

        # Preparar el contenido del correo electrónico
        asset_summary = f"{assetSymbol}: {user_asset.quantity} units purchased at ${user_asset.purchase_price:.2f}"
        email_message = f"""Dear {user.name},

            You have successfully purchased {quantity:.2f} units of {assetSymbol} for a total amount of ${amount}.

            Current holdings of {assetSymbol}: {user_asset.quantity:.2f} units

            Summary of current assets:
            - {asset_summary}

            Account Balance: ${user.account.balance:.2f}
            Net Worth: ${user.account.balance + user_asset.quantity * user_asset.purchase_price:.2f}

            Thank you for using our investment services.

            Best Regards,
            Investment Management Team
            """

        # Enviar el correo de confirmación
        send_mail(
            subject="Investment Purchase Confirmation",
            message=email_message,
            from_email="no-reply@banking.com",
            recipient_list=[user.email]
        )

        return Response({"msg": "Asset purchase successful"}, status=status.HTTP_200_OK)


class SellAssetView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SellAssetSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        pin = serializer.validated_data['pin']
        quantity = serializer.validated_data['quantity']
        assetSymbol = serializer.validated_data['assetSymbol']

        # Verificar el PIN
        if not user.check_pin(pin):
            return Response({"detail": "Invalid PIN"}, status=status.HTTP_403_FORBIDDEN)

        # Verificar que el usuario tiene el activo y la cantidad suficiente
        try:
            user_asset = UserAsset.objects.get(
                user=user, assetSymbol=assetSymbol)
            if user_asset.quantity < quantity:
                return Response({"detail": "Internal error occurred while selling the asset"}, status=status.HTTP_500_BAD_REQUEST)
        except UserAsset.DoesNotExist:
            return Response({"detail": f"No holdings found for asset {assetSymbol}"}, status=status.HTTP_404_BAD_REQUEST)

        # Obtener el precio de venta actual desde la API de precios en tiempo real
        try:
            response = requests.get(
                "https://faas-lon1-917a94a7.doserverless.co/api/v1/web/fn-e0f31110-7521-4cb9-86a2-645f66eefb63/default/market-prices-simulator")
            response.raise_for_status()
            market_data = response.json()
            asset_sale_price = Decimal(market_data.get(assetSymbol))
            if asset_sale_price is None:
                return Response({"detail": "Asset price not found"}, status=status.HTTP_400_BAD_REQUEST)
        except requests.RequestException as e:
            return Response({"detail": "Error fetching real-time asset price"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Calcular el valor total de la venta y la ganancia/pérdida
        total_sale_value = Decimal(quantity) * asset_sale_price
        gain_loss = (asset_sale_price - user_asset.purchase_price) * quantity

        # Actualizar la cuenta del usuario y la cantidad del activo
        user.account.balance += total_sale_value
        user.account.save()
        user_asset.quantity -= quantity
        user_asset.save()

        # Crear la transacción
        Transaction.objects.create(
            amount=total_sale_value,
            transactionType="ASSET_SELL",
            sourceAccount=user.account,
            transactionDate=timezone.now(),
        )

        # Enviar correo de confirmación
        send_mail(
            subject="Investment Sale Confirmation",
            message=(
                f"Dear {user.name},\n\n"
                f"You have successfully sold {quantity} units of {assetSymbol}.\n\n"
                f"Total Gain/Loss: ${gain_loss:.2f}\n\n"
                f"Remaining holdings of {assetSymbol}: {user_asset.quantity} units\n\n"
                f"Summary of current assets:\n"
                f"- {assetSymbol}: {user_asset.quantity} units purchased at ${user_asset.purchase_price}\n\n"
                f"Account Balance: ${user.account.balance}\n"
                f"Net Worth: ${user.account.balance + sum(asset.quantity * asset.purchase_price for asset in user.assets.all())}\n\n"
                "Thank you for using our investment services.\n\n"
                "Best Regards,\n"
                "Investment Management Team"
            ),
            from_email="no-reply@investment.com",
            recipient_list=[user.email],
        )

        return Response({"msg": "Asset sold successfully"}, status=status.HTTP_200_OK)


class UserAssetInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Obtener el símbolo del activo desde los parámetros de consulta (si está presente)
        assetSymbol = request.query_params.get('assetSymbol', None)

        # Si se proporciona un símbolo de activo, devolver solo ese activo
        if assetSymbol:
            try:
                user_asset = UserAsset.objects.get(
                    user=request.user, assetSymbol=assetSymbol)
                serializer = UserAssetInfoSerializer(user_asset)
                return Response({assetSymbol: serializer.data["quantity"]}, status=status.HTTP_200_OK)
            except UserAsset.DoesNotExist:
                return Response({"detail": f"No holdings found for asset {assetSymbol}"}, status=status.HTTP_404_NOT_FOUND)

        user_assets = UserAsset.objects.filter(user=request.user)
        serializer = UserAssetInfoSerializer(user_assets, many=True)

        assets_data = {asset["assetSymbol"]: asset["quantity"]
                        for asset in serializer.data}
        return Response(assets_data, status=status.HTTP_200_OK)


class NetWorthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Obtener el balance en efectivo del usuario
        cash_balance = user.account.balance

        # Obtener la lista de activos del usuario
        user_assets = UserAsset.objects.filter(user=user)

        # Obtener precios de activos en tiempo real
        response = requests.get(
            "https://faas-lon1-917a94a7.doserverless.co/api/v1/web/fn-e0f31110-7521-4cb9-86a2-645f66eefb63/default/market-prices-simulator")

        if response.status_code != 200:
            return Response({"detail": "Error retrieving market prices"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        market_prices = response.json()

        # Calcular el valor total de los activos en posesión
        total_asset_value = Decimal(0)
        for asset in user_assets:
            asset_symbol = asset.assetSymbol
            if asset_symbol in market_prices:
                current_price = Decimal(market_prices[asset_symbol])
                asset_value = current_price * asset.quantity
                total_asset_value += asset_value

        # Calcular el patrimonio neto
        net_worth = cash_balance + total_asset_value

        return Response({"netWorth": float(net_worth)}, status=status.HTTP_200_OK)


class CreateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubscriptionSerializer(
            data=request.data, context={'request': request})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        amount = serializer.validated_data['amount']
        interval_seconds = serializer.validated_data['intervalSeconds']
        pin = serializer.validated_data['pin']
        user = request.user

        # Verificar el PIN
        if not user.check_pin(pin):
            return Response({"detail": "Invalid PIN"}, status=status.HTTP_403_FORBIDDEN)

        # Verificar saldo del usuario
        if user.account.balance < amount:
            return Response({"detail": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)

        # Crear suscripción
        subscription = Subscription.objects.create(
            user=user,
            amount=amount,
            interval_seconds=interval_seconds,
            last_executed=timezone.now(),
            is_active=True
        )

        # Registrar la primera transacción de prueba
        user.account.balance -= amount
        user.account.save()

        Transaction.objects.create(
            amount=amount,
            transactionType="SUBSCRIPTION",
            sourceAccount=user.account,
            transactionDate=timezone.now(),
        )

        # Llamada a Celery para procesar suscripciones periódicamente
        process_subscriptions.delay()

        return Response({"msg": "Subscription created successfully"}, status=status.HTTP_201_CREATED)


class EnableAutoInvestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Serialización y validación del PIN
        serializer = AutoInvestBotSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            # Obtener el usuario autenticado
            user = request.user

            auto_invest, created = AutoInvest.objects.get_or_create(user=user)
            auto_invest.is_active = True
            auto_invest.save()

            # Programar la tarea de auto-inversión global para todos los usuarios con auto-inversión activa
            auto_invest_bot.apply_async(countdown=0)

            # Respuesta de éxito
            return Response({"msg": "Automatic investment enabled successfully"}, status=status.HTTP_200_OK)

        # Respuesta de error si el PIN no es válido
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)