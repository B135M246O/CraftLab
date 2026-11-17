from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, ImageDraw

from recipes.models import IngredientAmount, Recipe
from tags_ingr.models import Ingredient, Tag
from users.models import User


class Command(BaseCommand):
    help = 'Загрузить материалы, техники и два открытых мастер-класса.'

    @transaction.atomic
    def handle(self, *args, **options):
        call_command('add_data', str(Path(__file__).resolve().parents[3] / 'ingredients.csv'))
        author, created = User.objects.get_or_create(
            username='craftlab_demo', defaults={
                'email': 'demo@example.org', 'first_name': 'Мастер', 'last_name': 'CraftLab'})
        if created:
            author.set_unusable_password()
            author.save()
        workshops = [
            ('Подставка из хлопкового шнура', 'Декор', 'decor', '#447755', 'Шнур хлопковый', 3,
             'Отмерьте три метра шнура. Уложите его спиралью, закрепляя каждый виток. '
             'Подшейте свободный конец. Проверьте устойчивость подставки.', 30),
            ('Браслет с деревянными бусинами', 'Плетение', 'braiding', '#AA7755', 'Бусины деревянные', 12,
             'Разложите двенадцать бусин. Нанижите их на подходящий шнур. '
             'Завяжите регулируемый узел и проверьте размер браслета.', 20),
        ]
        for name, technique, slug, color, material, amount, text, duration in workshops:
            tag, _ = Tag.objects.get_or_create(slug=slug, defaults={'name': technique, 'color': color})
            recipe, created = Recipe.objects.get_or_create(
                author=author, name=name, defaults={'text': text, 'cooking_time': duration})
            if created:
                image = Image.new('RGB', (640, 360), '#f4efe5')
                drawing = ImageDraw.Draw(image)
                for x in range(100, 560, 70):
                    drawing.ellipse((x, 140, x + 45, 185), fill=color)
                output = BytesIO()
                image.save(output, format='PNG')
                recipe.image.save(f'{slug}.png', ContentFile(output.getvalue()))
                recipe.tags.add(tag)
                IngredientAmount.objects.create(
                    recipe=recipe, ingredient=Ingredient.objects.get(name=material), amount=amount)
        self.stdout.write(self.style.SUCCESS('Демонстрационные мастер-классы готовы. У демоавтора нет пароля.'))
