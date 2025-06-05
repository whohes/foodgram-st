from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from .models import Recipe

def copy_short_link(request, pk):
    recipe = get_object_or_404(Recipe, id=pk)
    return redirect(reverse('api:recipe_detail', kwargs={'pk': recipe.id})) 