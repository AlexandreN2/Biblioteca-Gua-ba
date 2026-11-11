from django.urls import path
from . import views
app_name = "core"
urlpatterns = [path("", views.inicio, name="inicio"), path("sobre/", views.sobre, name="sobre"), path("atendimento/", views.atendimento, name="atendimento"), path("como-reservar/", views.como_reservar, name="como_reservar")]
