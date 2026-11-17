from pathlib import Path

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from fpdf import FPDF
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.filters import RecipeFilter
from recipes.models import Favorite, IngredientAmount, Recipe, ShoppingCart
from recipes.permissions import AuthorOrReadOnly
from recipes.serializers import RecipeSerializer, SmallRecipeSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (AuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add(self, model, user, pk, name):
        recipe = get_object_or_404(Recipe, pk=pk)
        relation = model.objects.filter(user=user, recipe=recipe)
        if relation.exists():
            return Response(
                {'errors': f'Нельзя повторно добавить мастер-класс в {name}'},
                status=status.HTTP_400_BAD_REQUEST)
        model.objects.create(user=user, recipe=recipe)
        serializer = SmallRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_relation(self, model, user, pk, name):
        recipe = get_object_or_404(Recipe, pk=pk)
        relation = model.objects.filter(user=user, recipe=recipe)
        if not relation.exists():
            return Response(
                {'errors': f'Нельзя повторно удалить мастер-класс из {name}'},
                status=status.HTTP_400_BAD_REQUEST)
        relation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post', 'delete'], detail=True, url_path='favorite',
            url_name='favorite', permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        user = request.user
        if request.method == 'POST':
            name = 'избранное'
            return self.add(Favorite, user, pk, name)
        if request.method == 'DELETE':
            name = 'избранного'
            return self.delete_relation(Favorite, user, pk, name)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(methods=['post', 'delete'], detail=True, url_path='shopping_cart',
            url_name='shopping_cart', permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        user = request.user
        if request.method == 'POST':
            name = 'список материалов'
            return self.add(ShoppingCart, user, pk, name)
        if request.method == 'DELETE':
            name = 'списка материалов'
            return self.delete_relation(ShoppingCart, user, pk, name)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(methods=['get'], detail=False, url_path='download_shopping_cart',
            url_name='download_shopping_cart', permission_classes=[IsAuthenticated])
    def download_cart(self, request):
        user = request.user
        ingredients = IngredientAmount.objects.filter(
            recipe__sh_cart__user=user).values(
                'ingredient__name', 'ingredient__measurement_unit').annotate(
                    Sum('amount')).order_by('ingredient__name')
        pdf = FPDF()
        pdf.add_page()
        pdf.add_font(
            'DejaVu', '', str(Path(__file__).parent / 'fonts' / 'DejaVuSansCondensed.ttf'))
        pdf.set_font('DejaVu', size=14)
        pdf.cell(text='Список материалов', center=True)
        pdf.ln(8)
        for i, ingredient in enumerate(ingredients):
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['amount__sum']
            pdf.multi_cell(
                0, 8, f'{i + 1}) {name} - {amount} {unit}',
                new_x='LMARGIN', new_y='NEXT')
        file = pdf.output()
        response = HttpResponse(
            content_type='application/pdf', status=status.HTTP_200_OK)
        response['Content-Disposition'] = (
            'attachment; filename="craftlab-materials.pdf"')
        response.write(bytes(file))
        return response
