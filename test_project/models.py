from django.db import models
from django.db.models import CharField, IntegerField


class Names(models.Model):
    custom_id_field: IntegerField = models.IntegerField(primary_key=True)
    name: CharField = models.CharField(
        max_length=254,
        choices=(("mo", "Moses"), ("moi", "Moishe"), ("mu", "Mush")),
        default=None,
        null=True,
        blank=True,
    )

    class Meta:
        app_label = "test_project"
