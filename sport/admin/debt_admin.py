from django.contrib import admin
from django.utils.html import format_html, format_html_join
from import_export import fields, resources
from import_export.admin import ImportExportActionModelAdmin
from import_export.results import RowResult
from import_export.widgets import ForeignKeyWidget

from sport.models.debt import Debt

from ..models import Semester, Student
from .admin_site import site
from .admin_utils import DefaultFilterMixIn


class DebtResource(resources.ModelResource):
    student = fields.Field(column_name="student", attribute="student", widget=ForeignKeyWidget(Student, "user__email"))
    semester = fields.Field(column_name="semester", attribute="semester", widget=ForeignKeyWidget(Semester, "name"))

    def import_row(self, row, instance_loader, **kwargs):
        # overriding import_row to ignore errors and skip rows that fail to import
        # without failing the entire import
        import_result = super().import_row(row, instance_loader, **kwargs)
        if import_result.import_type == RowResult.IMPORT_TYPE_ERROR:
            # Copy the values to display in the preview report
            import_result.diff = [row[val] for val in row]
            # Add a column with the error message
            import_result.diff.append(
                format_html(
                    "Errors:<ul>{}</ul>",
                    format_html_join("", "<li>{}</li>", ((err.error,) for err in import_result.errors)),
                )
            )
            # clear errors and mark the record to skip
            import_result.errors = []
            import_result.import_type = RowResult.IMPORT_TYPE_SKIP

        return import_result

    class Meta:
        model = Debt
        fields = ("student", "semester", "debt")
        import_id_fields = (
            "student",
            "semester",
        )


@admin.register(Debt, site=site)
class DebtAdmin(ImportExportActionModelAdmin, DefaultFilterMixIn):
    semester_filter = "semester__id__exact"
    resource_class = DebtResource

    list_filter = ("semester",)

    autocomplete_fields = ("student",)

    list_display = (
        "student",
        "semester",
        "debt",
    )
