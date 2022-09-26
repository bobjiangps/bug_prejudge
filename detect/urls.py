from django.urls import path
from . import views

urlpatterns = [
    path(r'parameters/', views.PublicParameters.as_view(), name='public_parameters'),
]
