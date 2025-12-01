from django.urls import path
from . import views

app_name = 'prediction'

urlpatterns = [
    path('', views.home, name='home'),
    path('predict/', views.predict_image, name='predict'),
    path('health/', views.health_check, name='health_check'),
    path('model-info/', views.model_info, name='model_info'),
]
