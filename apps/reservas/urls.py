from django.urls import path
from . import views
app_name = "reservas"
urlpatterns = [path("", views.minhas, name="minhas"), path("solicitar/<int:pk>/", views.solicitar, name="solicitar"), path("cancelar/<int:pk>/", views.cancelar, name="cancelar")]
