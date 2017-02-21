from django.db import models


class ModelA(models.Model):
    field_2 = models.IntegerField()
    field_1 = models.CharField(max_length=255)

    class Meta:
        app_label = 'conf'
