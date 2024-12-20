from rest_framework import serializers
from django.core.validators import EmailValidator
from .models import CustomUser, Transaction, UserAsset, Subscription
from decimal import Decimal


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(
        validators=[EmailValidator(message="Invalid email")]
    )

    class Meta:
        model = CustomUser
        fields = ["name", "email", "password",
                    "address", "phoneNumber", "countryCode"]

    def validate_password(self, value):
        errors = []
        if ' ' in value:
            errors.append("Password cannot contain whitespace.")
        if len(value) < 8:
            errors.append("Password must be at least 8 characters long.")
        if len(value) > 128:
            errors.append("Password must be less than 128 characters long.")
        if not any(char.isupper() for char in value):
            errors.append(
                "Password must contain at least one uppercase letter.")
        if not any(char.isdigit() for char in value):
            errors.append("Password must contain at least one digit.")
        if not any(char in '@$!%*#?&' for char in value):
            errors.append(
                "Password must contain at least one special character.")

        if errors:
            raise serializers.ValidationError(errors)

        return value

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(f"Invalid email: {value}")
        return value

    def validate_phoneNumber(self, value):
        if CustomUser.objects.filter(phoneNumber=value).exists():
            raise serializers.ValidationError("Phone number already exists")
        return value

    def create(self, validated_data):
        user = CustomUser(
            email=validated_data["email"],
            name=validated_data["name"],
            address=validated_data["address"],
            phoneNumber=validated_data["phoneNumber"],
            countryCode=validated_data["countryCode"]
        )
        # Guarda la contraseña en formato hash
        user.set_password(validated_data["password"])
        user.save()
        return user

    def to_representation(self, instance):
        """Modifica la representación para incluir la contraseña hasheada y accountNumber en la respuesta"""
        representation = super().to_representation(instance)
        representation['accountNumber'] = instance.accountNumber
        representation['hashedPassword'] = instance.password
        return representation


class TransactionSerializer(serializers.ModelSerializer):
    # Asegúrate de que los nombres sean los mismos en el modelo y el serializer
    source_account_number = serializers.CharField(source="sourceAccount.accountNumber", read_only=True)
    target_account_number = serializers.SerializerMethodField()
    transaction_date = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'transactionType', 'transaction_date',
                    'source_account_number', 'target_account_number']

    def get_target_account_number(self, obj):
        # Devolver "N/A" si target_account es None
        return obj.targetAccount.accountNumber if obj.targetAccount else "N/A"

    def get_transaction_date(self, obj):
        # Convertir la fecha al formato de timestamp
        return int(obj.transactionDate.timestamp() * 1000)


class DepositSerializer(serializers.Serializer):
    pin = serializers.CharField(max_length=4, required=True)
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=True, min_value=Decimal('0.01'))


class WithdrawSerializer(serializers.Serializer):
    pin = serializers.CharField(max_length=4, required=True)
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=True, min_value=Decimal('0.01'))


class TransferFundsSerializer(serializers.Serializer):
    targetAccountNumber = serializers.CharField(max_length=6, required=True)
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=True, min_value=Decimal('0.01'))
    pin = serializers.CharField(max_length=4, required=True)


class BuyAssetSerializer(serializers.Serializer):
    assetSymbol = serializers.CharField(max_length=10, required=True)
    amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=True, min_value=Decimal('0.01'))
    pin = serializers.CharField(max_length=4, required=True)

    def create_or_update_user_asset(self, user, assetSymbol, quantity, purchase_price):
        """
        Actualiza o crea un activo para el usuario al comprar, manejando la cantidad y precio de compra.
        """
        asset, created = UserAsset.objects.get_or_create(
            user=user,
            assetSymbol=assetSymbol,
            defaults={'quantity': quantity, 'purchase_price': purchase_price}
        )

        if not created:
            total_quantity = asset.quantity + quantity
            weighted_price = (
                (asset.quantity * asset.purchase_price) +
                (quantity * purchase_price)
            ) / total_quantity

            asset.quantity = total_quantity
            asset.purchase_price = weighted_price
            asset.save()

        return asset


class SellAssetSerializer(serializers.Serializer):
    assetSymbol = serializers.CharField(
        max_length=10,
        required=True,
        help_text="Símbolo del activo que se va a vender, por ejemplo 'GOLD'."
    )
    quantity = serializers.DecimalField(
        max_digits=15,
        decimal_places=8,
        required=True,
        min_value=Decimal('0.01'),
        help_text="Cantidad del activo a vender. Debe ser mayor a 0.01."
    )
    pin = serializers.CharField(
        max_length=4,
        required=True,
        help_text="PIN de 4 dígitos del usuario para verificar la transacción."
    )


class UserAssetInfoSerializer(serializers.ModelSerializer):
    assetSymbol = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=15, decimal_places=10)

    class Meta:
        model = UserAsset
        fields = ['assetSymbol', 'quantity']


class SubscriptionSerializer(serializers.Serializer):
    pin = serializers.CharField(max_length=4)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    intervalSeconds = serializers.IntegerField(min_value=1)

    def validate_pin(self, value):
        user = self.context['request'].user
        if not user.check_pin(value):
            raise serializers.ValidationError("Invalid PIN")
        return value


class AutoInvestBotSerializer(serializers.Serializer):
    pin = serializers.CharField(max_length=4)

    def validate_pin(self, value):
        user = self.context['request'].user
        if not user.check_pin(value):
            raise serializers.ValidationError("Invalid PIN")
        return value