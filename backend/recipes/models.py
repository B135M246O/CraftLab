from django.core.validators import MinValueValidator
from django.db import models

from recipes.validators import validate_time
from tags_ingr.models import Ingredient, Tag
from users.models import User


class Recipe(models.Model):
    tags = models.ManyToManyField(Tag, related_name='recipes', verbose_name='Техники')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes', verbose_name='Автор'
    )
    pub_date = models.DateTimeField(
        'Дата публикации', auto_now_add=True, db_index=True
    )
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientAmount', verbose_name='Материалы'
    )
    name = models.CharField('Название мастер-класса', max_length=200)
    image = models.ImageField(
        'Изображение', upload_to='recipes/'
    )
    text = models.TextField('Пошаговая инструкция')
    cooking_time = models.IntegerField('Время выполнения, мин.', validators=[validate_time])

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Мастер-класс'
        verbose_name_plural = 'Мастер-классы'

    def __str__(self):
        return self.name


class IngredientAmount(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name='Мастер-класс')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, verbose_name='Материал')
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[MinValueValidator(1, 'Не может быть менее 1')]
    )

    class Meta:
        verbose_name = 'Материал мастер-класса'
        verbose_name_plural = 'Материалы мастер-классов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Мастер-класс',
    )

    class Meta:
        verbose_name = 'Избранный мастер-класс'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_favorite_recipe'
            )
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sh_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='sh_cart',
        verbose_name='Мастер-класс',
    )

    class Meta:
        verbose_name = 'Мастер-класс в списке материалов'
        verbose_name_plural = 'Список материалов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_cart_recipe'
            )
        ]
