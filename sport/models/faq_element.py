from django.db import models
from tinymce.models import HTMLField


class FAQElement(models.Model):
    category = models.ForeignKey('FAQCategory', on_delete=models.DO_NOTHING, null=False)
    question = models.CharField(max_length=1000, null=False)
    answer = HTMLField()

    class Meta:
        db_table = "faq_element"
        verbose_name_plural = "faq element"

    def __str__(self):
        return self.question
