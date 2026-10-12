from django.db import models


class FAQCategory(models.Model):
    name = models.CharField(max_length=50, null=False)

    class Meta:
        db_table = "faq_category"
        verbose_name_plural = "faq category"

    def __str__(self):
        return self.name
