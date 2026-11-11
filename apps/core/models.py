from django.db import models

PENDENTE = 'Pendente de confirmação pela instituição.'


class Configuracao(models.Model):
    nome = models.CharField(max_length=240, default='Biblioteca Pública Municipal Darcy Azambuja — Guaíba/RS')
    endereco = models.TextField('endereço', default=PENDENTE)
    horarios = models.TextField('horários', default=PENDENTE)
    telefone = models.CharField(max_length=120, default=PENDENTE)
    email = models.EmailField('e-mail', blank=True)
    orientacoes_cadastro = models.TextField('orientações para cadastro', default='Neste protótipo, crie uma conta demonstrativa com nome de usuário e senha. O cadastro presencial oficial está pendente de confirmação.')
    regras_emprestimo = models.TextField('regras de empréstimo', default='As regras oficiais de empréstimo estão pendentes de confirmação. As operações deste portal são apenas demonstrativas.')
    orientacoes_reserva = models.TextField('orientações para reservas', default='Pesquise uma obra, entre na sua conta e confirme a reserva demonstrativa. Acompanhe a situação em Minhas reservas. Nenhum pedido será enviado à biblioteca real.')
    como_chegar_url = models.URLField('link de localização verificado', blank=True)
    sobre = models.TextField(default='Um espaço digital de encontro com a leitura e a cultura de Guaíba. Este protótipo apresenta serviços de consulta e reservas, sem vínculo operacional com a prefeitura. As informações institucionais aguardam confirmação.')

    class Meta:
        verbose_name = 'configuração institucional'
        verbose_name_plural = 'configurações institucionais'
        constraints = [models.CheckConstraint(condition=models.Q(pk=1), name='configuracao_unica')]

    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)

    @classmethod
    def obter(cls):
        return cls.objects.get_or_create(pk=1)[0]

    def __str__(self):
        return 'Identidade e atendimento da biblioteca'


class Comunicado(models.Model):
    titulo = models.CharField('título', max_length=200)
    texto = models.TextField()
    publicado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em', '-pk']
        verbose_name = 'comunicado'
        verbose_name_plural = 'comunicados'

    def __str__(self):
        return self.titulo
