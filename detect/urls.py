from django.urls import path, re_path
from . import views

urlpatterns = [
    path(r'parameters/', views.PublicParameters.as_view(), name='public_parameters'),
    path(r'available_models/', views.AvailableModels.as_view(), name='available_models'),
    re_path(r'detect/?', views.Detection.as_view(), name='detection'),
]
