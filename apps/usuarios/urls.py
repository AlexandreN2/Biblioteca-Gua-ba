from django.urls import path
from .views import cadastro
app_name = "usuarios"
urlpatterns = [path("cadastro/", cadastro, name="cadastro")]
