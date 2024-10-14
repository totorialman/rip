from stocks.models import Stock
from stocks.models import AuthUser
from rest_framework import serializers


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = Stock
        # Поля, которые мы сериализуем
        fields = ["pk", "company_name", "price", "is_growing", "date_modified", "url"]

class FullStockSerializer(serializers.ModelSerializer):
    # StringRelatedField вернет строковое представление объекта, то есть его имя
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Stock
        # Сериализуем все поля
        fields = ["pk", "company_name", "price", "is_growing", "date_modified", "url", "user"]


class UserSerializer(serializers.ModelSerializer):
    stock_set = StockSerializer(many=True, read_only=True)

    class Meta:
        model = AuthUser
        fields = ["id", "first_name", "last_name", "stock_set"]