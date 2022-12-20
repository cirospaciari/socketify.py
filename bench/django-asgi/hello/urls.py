from django.urls import path
from world.views import plaintext, json

urlpatterns = [
    path('plaintext', plaintext, name='plaintext'),
    path('json', json, name='json'),
]
