from django.contrib.auth.forms import UserCreationForm

class CadastroForm(UserCreationForm):
    """O cadastro local solicita somente identificador e senha."""
    pass
