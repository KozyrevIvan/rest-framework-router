from django.db import models


class TestModel(models.Model):
    name = models.CharField("Название", max_length=255)
    description = models.CharField("Описание", max_length=255, null=True, blank=True)
    active = models.BooleanField("Доступность", default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'TestModel'
        verbose_name_plural = 'TestModel'