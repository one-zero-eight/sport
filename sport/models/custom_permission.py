from django.db import models


class CustomPermission(models.Model):
    name = models.CharField(max_length=50, null=False)
    description = models.TextField(max_length=1000, null=False)

    class Meta:
        permissions = [
            ('choose_sport', "Can choose type of sport"),
            ("go_to_another_sport", "Can go to group of the another type of sport"),
            ("see_calendar", "Can see calendar"),
            ("go_to_another_group", "Can go to another group in the same type of sport"),
            ("choose_group", "Can choose group"),
            ("more_than_10_hours_of_self_sport", "Can have more then 10 hours of self sport"),
            ("change_fitness_test", "Can change fitness test results"),
        ]
        db_table = "custom_permission"
        verbose_name_plural = "custom permissions"

    def __str__(self):
        return self.name
