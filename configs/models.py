from django.db import models

class ForecastConfig(models.Model):
    FREQUENCIA_CHOICES = [
        ('diaria', 'Diária'),
        ('semanal', 'Semanal'),
        ('mensal', 'Mensal'),
    ]

    start_date = models.DateField()
    frequencia = models.CharField(max_length=10, choices=FREQUENCIA_CHOICES, default='diaria')
    include_promotions = models.BooleanField(default=True)
    dia_semana = models.CharField(
        max_length=10,
        choices=[('segunda','Segunda'),('terca','Terça'),('quarta','Quarta'),
                 ('quinta','Quinta'),('sexta','Sexta'),('sabado','Sábado'),('domingo','Domingo')],
        null=True,
        blank=True
    )
    dia_mes = models.PositiveSmallIntegerField(null=True, blank=True)
    forecast_horizon = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Configuração {self.id} - {self.start_date}"
