import base64
from io import BytesIO
import tempfile

from django.test import override_settings
from PIL import Image
from pypdf import PdfReader
from rest_framework.test import APITestCase

from recipes.models import IngredientAmount, Recipe
from tags_ingr.models import Ingredient, Tag
from users.models import User


class CraftLabTests(APITestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.media.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.author = User.objects.create_user(
            username='maker', email='maker@example.org', password='test-only-pass',
            first_name='Мастер', last_name='Декора')
        self.reader = User.objects.create_user(
            username='reader', email='reader@example.org', password='test-only-pass')
        self.material = Ingredient.objects.create(name='Шнур хлопковый', measurement_unit='м')
        self.tag = Tag.objects.create(name='Макраме', slug='macrame', color='#447755')
        self.other_tag = Tag.objects.create(name='Шитьё', slug='sewing', color='#AA7755')
        image = BytesIO()
        Image.new('RGB', (2, 2), '#447755').save(image, format='PNG')
        self.image = 'data:image/png;base64,' + base64.b64encode(image.getvalue()).decode()

    def payload(self, **changes):
        data = {
            'name': 'Браслет из хлопкового шнура', 'text': 'Отмерьте шнур. Завяжите узлы.',
            'cooking_time': 25, 'image': self.image, 'tags': [self.tag.pk],
            'ingredients': [{'id': self.material.pk, 'amount': 3}],
        }
        data.update(changes)
        return data

    def create_workshop(self, **changes):
        self.client.force_authenticate(self.author)
        response = self.client.post('/api/recipes/', self.payload(**changes), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        return response.data['id']

    def test_publish_instruction_with_materials(self):
        pk = self.create_workshop()
        self.client.force_authenticate(None)
        response = self.client.get(f'/api/recipes/{pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['ingredients'][0]['name'], 'Шнур хлопковый')
        self.assertEqual(response.data['ingredients'][0]['amount'], 3)
        self.assertEqual(response.data['tags'][0]['slug'], 'macrame')

    def test_only_author_can_edit_instruction(self):
        pk = self.create_workshop()
        self.client.force_authenticate(self.reader)
        response = self.client.patch(f'/api/recipes/{pk}/', {'name': 'Чужое'}, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Recipe.objects.get(pk=pk).name, 'Браслет из хлопкового шнура')

    def test_partial_edit_preserves_materials_and_tags(self):
        pk = self.create_workshop()
        response = self.client.patch(f'/api/recipes/{pk}/', {'text': 'Новая инструкция'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(IngredientAmount.objects.get(recipe_id=pk).amount, 3)
        self.assertEqual(list(Recipe.objects.get(pk=pk).tags.all()), [self.tag])

    def test_update_material_quantity(self):
        pk = self.create_workshop()
        response = self.client.patch(f'/api/recipes/{pk}/', {
            'ingredients': [{'id': self.material.pk, 'amount': 7}],
            'tags': [self.other_tag.pk],
        }, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(IngredientAmount.objects.get(recipe_id=pk).amount, 7)
        self.assertEqual(list(Recipe.objects.get(pk=pk).tags.all()), [self.other_tag])

    def test_invalid_materials_do_not_publish_instruction(self):
        self.client.force_authenticate(self.author)
        for materials in ([], [{'id': self.material.pk}],
                          [{'id': self.material.pk, 'amount': 0}],
                          [{'id': self.material.pk, 'amount': 'invalid'}],
                          [{'id': self.material.pk, 'amount': 1}] * 2):
            with self.subTest(materials=materials):
                response = self.client.post('/api/recipes/', self.payload(ingredients=materials), format='json')
                self.assertEqual(response.status_code, 400, response.data)
                self.assertFalse(Recipe.objects.exists())

    def test_invalid_tag_does_not_leave_instruction(self):
        self.client.force_authenticate(self.author)
        response = self.client.post('/api/recipes/', self.payload(tags=[99999]), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Recipe.objects.exists())

    def test_favorite_duplicate_and_filter(self):
        pk = self.create_workshop()
        self.client.force_authenticate(self.reader)
        url = f'/api/recipes/{pk}/favorite/'
        self.assertEqual(self.client.post(url).status_code, 201)
        self.assertEqual(self.client.post(url).status_code, 400)
        response = self.client.get('/api/recipes/?is_favorited=1')
        self.assertEqual([item['id'] for item in response.data['results']], [pk])
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.delete(url).status_code, 400)

    def test_subscription_feed_and_duplicate(self):
        pk = self.create_workshop()
        self.client.force_authenticate(self.reader)
        url = f'/api/users/{self.author.pk}/subscribe/'
        self.assertEqual(self.client.post(url).status_code, 201)
        self.assertEqual(self.client.post(url).status_code, 400)
        response = self.client.get('/api/users/subscriptions/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['recipes'][0]['id'], pk)
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_tag_filter_and_material_search(self):
        pk = self.create_workshop()
        response = self.client.get('/api/recipes/?tags=macrame')
        self.assertEqual([item['id'] for item in response.data['results']], [pk])
        response = self.client.get('/api/recipes/?tags=sewing')
        self.assertEqual(response.data['count'], 0)
        response = self.client.get('/api/ingredients/?name=Шнур')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['name'], self.material.name)

    def test_pdf_sums_equal_quantities_across_instructions_and_isolates_users(self):
        first = self.create_workshop(name='Браслет')
        second = self.create_workshop(name='Брелок')
        extra = self.create_workshop(name='Чужой список')
        self.client.post(f'/api/recipes/{extra}/shopping_cart/')
        self.client.force_authenticate(self.reader)
        for pk in (first, second):
            url = f'/api/recipes/{pk}/shopping_cart/'
            self.assertEqual(self.client.post(url).status_code, 201)
            self.assertEqual(self.client.post(url).status_code, 400)
        response = self.client.get('/api/recipes/download_shopping_cart/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))
        text = PdfReader(BytesIO(response.content)).pages[0].extract_text()
        self.assertIn('Список материалов', text)
        self.assertIn('Шнур хлопковый - 6 м', text)
        self.assertNotIn('9 м', text)

    def test_private_lists_require_authentication(self):
        pk = self.create_workshop()
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/recipes/download_shopping_cart/').status_code, 401)
        self.assertEqual(self.client.post(f'/api/recipes/{pk}/shopping_cart/').status_code, 401)
        self.assertEqual(self.client.post(f'/api/recipes/{pk}/favorite/').status_code, 401)
        for query in ('is_favorited=1', 'is_in_shopping_cart=1'):
            response = self.client.get(f'/api/recipes/?{query}')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['count'], 0)

    def test_registration_and_token_login(self):
        response = self.client.post('/api/users/', {
            'email': 'new@example.org', 'username': 'new_maker',
            'password': 'test-only-long-pass', 'first_name': 'Новый', 'last_name': 'Мастер',
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertNotIn('password', response.data)
        response = self.client.post('/api/auth/token/login/', {
            'email': 'new@example.org', 'password': 'test-only-long-pass',
        }, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn('auth_token', response.data)
