from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("acervo/", include("apps.catalogo.urls")),
    path("reservas/", include("apps.reservas.urls")),
    path("conta/", include("apps.usuarios.urls")),
    path("conta/entrar/", auth_views.LoginView.as_view(), name="login"),
    path("conta/sair/", auth_views.LogoutView.as_view(), name="logout"),
]
admin.site.site_header = "Biblioteca de Guaíba • Demonstração"
admin.site.site_title = "Biblioteca • Administração"
admin.site.index_title = "Gestão do ambiente demonstrativo"
handler400 = "apps.core.views.erro_400"
handler403 = "apps.core.views.erro_403"
handler404 = "apps.core.views.erro_404"
handler500 = "apps.core.views.erro_500"
