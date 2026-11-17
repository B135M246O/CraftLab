from django.core.validators import RegexValidator
from django.db import models


class Tag(models.Model):
    name = models.CharField(
        'Техника',
        max_length=200,
        unique=True,
    )
    color = models.CharField(
        'Цвет',
        max_length=7,
        unique=True
    )
    slug = models.SlugField(
        'Идентификатор',
        max_length=200,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[-a-zA-Z0-9_]+$',
                message='Только латинские буквы и символы "-" "_"',
            ),
        ]
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Техника'
        verbose_name_plural = 'Техники'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название материала', max_length=200)
    measurement_unit = models.CharField('Единица измерения', max_length=200)

    class Meta:
        ordering = ('id',)
        verbose_name = 'Материал'
        verbose_name_plural = 'Материалы'

    def __str__(self):
        return self.name
