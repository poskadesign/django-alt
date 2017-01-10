from django.db import models


class ModelA(models.Model):
    field_1 = models.CharField(max_length=255)
    field_2 = models.IntegerField()

    class Meta:
        app_label = 'conf'
