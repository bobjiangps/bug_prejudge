from django.urls import path
from . import views

urlpatterns = [
    path(r'test_round/<int:round_id>/', views.PrejudgeRound.as_view(), name='prejudge_round'),
    path(r'test_round/<int:round_id>/test_script/<int:script_id>/', views.PrejudgeScript.as_view(), name='prejudge_script'),
    path(r'test_round/<int:round_id>/test_script/<int:script_id>/test_case/<int:case_id>/', views.PrejudgeCase.as_view(), name='prejudge_case'),
]
