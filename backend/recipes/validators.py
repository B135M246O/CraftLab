from rest_framework import serializers
from rest_framework.validators import ValidationError as RFError

from tags_ingr.models import Ingredient, Tag


def validate_time(value):
    if value < 1:
        raise RFError(
            ['Время не может быть менее минуты.']
        )


def validate_ingredients(data):
    if not data:
        raise RFError({'ingredients': ['Обязательное поле.']})
    if not isinstance(data, list):
        raise RFError({'ingredients': ['Ожидается список материалов.']})
    unique_ingredients = set()
    normalized = []
    integer = serializers.IntegerField(min_value=1)
    for ingredient in data:
        if not isinstance(ingredient, dict):
            raise RFError({'ingredients': ['Ожидается объект материала.']})
        try:
            ingredient_id = integer.run_validation(ingredient.get('id'))
            amount = integer.run_validation(ingredient.get('amount'))
        except RFError as exc:
            raise RFError({'ingredients': exc.detail}) from exc
        if not Ingredient.objects.filter(id=ingredient_id).exists():
            raise RFError({'ingredients': ['Материала нет в БД.']})
        if ingredient_id in unique_ingredients:
            raise RFError({'ingredients': ['Нельзя дублировать материалы.']})
        unique_ingredients.add(ingredient_id)
        normalized.append({'id': ingredient_id, 'amount': amount})
    return normalized



def validate_tags(data):
    if not data:
        raise RFError({'tags': ['Обязательное поле.']})
    if len(data) < 1:
        raise RFError({'tags': ['Хотя бы один тэг должен быть указан.']})
    for tag in data:
        if not Tag.objects.filter(id=tag).exists():
            raise RFError({'tags': ['Тэг отсутствует в БД.']})
    return data
