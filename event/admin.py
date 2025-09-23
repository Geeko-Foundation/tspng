from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from . import models


# ---------- Inlines (fixed ct_field/ct_fk_field) ----------

class EventOrganizerInline(admin.TabularInline):
    model = models.EventOrganizer
    extra = 0
    autocomplete_fields = ["user"]


class PaymentInline(admin.TabularInline):
    model = models.Payment
    extra = 0


class BankAccountInline(admin.TabularInline):
    model = models.BankAccount
    extra = 0


class ReimbursementAttachmentInline(admin.TabularInline):
    model = models.ReimbursementAttachment
    extra = 0


class ReimbursementLinkInline(admin.TabularInline):
    model = models.ReimbursementLink
    extra = 0


class CommentGenericInline(GenericTabularInline):
    """
    For models referencing Comment via (machine_content_type, machine_object_id)
    """
    model = models.Comment
    ct_field = "machine_content_type"
    ct_fk_field = "machine_object_id"
    extra = 0


class StateChangeGenericInline(GenericTabularInline):
    """
    For models referencing StateChange via (machine_content_type, machine_object_id)
    """
    model = models.StateChange
    ct_field = "machine_content_type"
    ct_fk_field = "machine_object_id"
    extra = 0


class AuditGenericInline(GenericTabularInline):
    """
    For models referencing Audit via (auditable_content_type, auditable_object_id)
    """
    model = models.Audit
    ct_field = "auditable_content_type"
    ct_fk_field = "auditable_object_id"
    extra = 0


# ---------- ModelAdmins ----------

@admin.register(models.Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "amount", "currency", "created_at", "updated_at")
    list_filter = ("currency",)
    search_fields = ("name", "description")


@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "id", "name", "country_code", "start_date", "end_date",
        "validated", "budget", "shipment_type",
    )
    list_filter = ("validated", "country_code", "shipment_type", "start_date", "end_date")
    search_fields = ("name", "description", "url")
    date_hierarchy = "start_date"
    autocomplete_fields = ["budget", "organizers"]
    #filter_horizontal = ("organizers",)
    inlines = [EventOrganizerInline, CommentGenericInline, StateChangeGenericInline, AuditGenericInline]


@admin.register(models.PostalAddress)
class PostalAddressAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "line1", "city", "postal_code", "country_code")
    list_filter = ("country_code",)
    search_fields = ("name", "line1", "line2", "city", "postal_code", "county")


@admin.register(models.Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ("id", "state", "user", "event", "visa_letter", "created_at", "updated_at")
    list_filter = ("state", "visa_letter", "event")
    search_fields = ("description", "contact_phone_number")
    autocomplete_fields = ["user", "event", "postal_address"]
    date_hierarchy = "created_at"
    inlines = [CommentGenericInline, StateChangeGenericInline, AuditGenericInline]


@admin.register(models.RequestExpense)
class RequestExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "request", "subject", "estimated_amount", "approved_amount", "total_amount")
    list_filter = ("estimated_currency", "approved_currency")
    search_fields = ("subject", "description")
    autocomplete_fields = ["request"]


@admin.register(models.Reimbursement)
class ReimbursementAdmin(admin.ModelAdmin):
    list_display = ("id", "state", "request", "user", "state_updated_at", "created_at")
    list_filter = ("state",)
    search_fields = ("description",)
    autocomplete_fields = ["request", "user"]
    inlines = [
        PaymentInline,
        BankAccountInline,
        ReimbursementAttachmentInline,
        ReimbursementLinkInline,
        CommentGenericInline,
        StateChangeGenericInline,
        AuditGenericInline,
    ]


@admin.register(models.BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("id", "holder", "bank_name", "iban", "bic", "country_code", "reimbursement")
    search_fields = ("holder", "bank_name", "iban", "bic")
    list_filter = ("country_code",)
    autocomplete_fields = ["reimbursement"]


@admin.register(models.Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "reimbursement", "date", "amount", "currency", "method", "code")
    list_filter = ("currency", "method", "date")
    search_fields = ("subject", "notes", "code")
    autocomplete_fields = ["reimbursement"]
    date_hierarchy = "date"


@admin.register(models.ReimbursementAttachment)
class ReimbursementAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "reimbursement", "title", "file", "created_at")
    search_fields = ("title", "file")
    autocomplete_fields = ["reimbursement"]


@admin.register(models.ReimbursementLink)
class ReimbursementLinkAdmin(admin.ModelAdmin):
    list_display = ("id", "reimbursement", "title", "url", "created_at")
    search_fields = ("title", "url")
    autocomplete_fields = ["reimbursement"]


@admin.register(models.EventEmail)
class EventEmailAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "event", "user", "created_at")
    search_fields = ("subject", "body", "to")
    autocomplete_fields = ["event", "user"]
    date_hierarchy = "created_at"


@admin.register(models.EventOrganizer)
class EventOrganizerAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "user")
    search_fields = ("event__name", "user__username", "user__email")
    autocomplete_fields = ["event", "user"]
    list_select_related = ("event", "user")


@admin.register(models.Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = (
        "id", "action", "auditable_content_type", "auditable_object_id",
        "user", "version", "created_at", "request_uuid",
    )
    list_filter = ("auditable_content_type", "created_at")
    search_fields = ("action", "audited_changes", "comment", "request_uuid", "username")
    autocomplete_fields = ["user"]


@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "private", "created_at", "machine_content_type", "machine_object_id")
    list_filter = ("private", "created_at", "machine_content_type")
    search_fields = ("body",)
    autocomplete_fields = ["user"]


@admin.register(models.StateChange)
class StateChangeAdmin(admin.ModelAdmin):
    list_display = (
        "id", "from_state", "to_state", "state_event", "user", "created_at",
        "machine_content_type", "machine_object_id", "type"
    )
    list_filter = ("type", "created_at", "machine_content_type")
    search_fields = ("from_state", "to_state", "state_event", "notes")
    autocomplete_fields = ["user"]


@admin.register(models.DelayedJob)
class DelayedJobAdmin(admin.ModelAdmin):
    list_display = ("id", "priority", "attempts", "run_at", "failed_at", "queue", "locked_by")
    list_filter = ("priority", "queue", "run_at", "failed_at")
    search_fields = ("handler", "last_error", "locked_by")
    date_hierarchy = "run_at"


@admin.register(models.Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "role", "full_name", "country_code")
    search_fields = ("full_name", "user__username", "user__email")
    list_filter = ("role", "country_code")
    autocomplete_fields = ["user", "role"]
