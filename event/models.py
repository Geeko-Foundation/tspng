from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


# ---------- Core domain ----------

class Budget(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, db_index=True, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name or f"Budget #{self.pk}"


class Event(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    country_code = models.CharField(max_length=10, null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    validated = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    visa_letters = models.BooleanField(default=False)
    request_creation_deadline = models.DateTimeField(null=True, blank=True)
    reimbursement_creation_deadline = models.DateTimeField(null=True, blank=True)
    budget = models.ForeignKey(
        Budget, null=True, blank=True, on_delete=models.SET_NULL, related_name="events", db_index=True
    )
    shipment_type = models.CharField(max_length=255, null=True, blank=True)

    # Many-to-many (wired via through table)
    organizers = models.ManyToManyField(
        "User",
        through="EventOrganizer",
        related_name="organized_events",
        blank=True,
    )

    def __str__(self):
        return self.name


class PostalAddress(models.Model):
    line1 = models.CharField(max_length=255, null=True, blank=True)
    line2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    county = models.CharField(max_length=255, null=True, blank=True)
    country_code = models.CharField(max_length=10, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        bits = [self.name, self.line1, self.city]
        return ", ".join([b for b in bits if b]) or f"Address #{self.pk}"


class User(models.Model):
    email = models.CharField(max_length=255, unique=True)
    encrypted_password = models.CharField(max_length=255, default="")
    reset_password_token = models.CharField(max_length=255, null=True, blank=True, unique=True)
    reset_password_sent_at = models.DateTimeField(null=True, blank=True)
    remember_created_at = models.DateTimeField(null=True, blank=True)
    sign_in_count = models.IntegerField(default=0)
    current_sign_in_at = models.DateTimeField(null=True, blank=True)
    last_sign_in_at = models.DateTimeField(null=True, blank=True)
    current_sign_in_ip = models.CharField(max_length=255, null=True, blank=True)
    last_sign_in_ip = models.CharField(max_length=255, null=True, blank=True)
    nickname = models.CharField(max_length=255)
    locale = models.CharField(max_length=10, default="en")
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["email"], name="index_users_on_email"),
            models.Index(fields=["reset_password_token"], name="index_users_on_reset_password_token"),
        ]

    def __str__(self):
        return self.nickname or self.email


class Request(models.Model):
    state = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="requests", db_index=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="requests", db_index=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    state_updated_at = models.DateTimeField(null=True, blank=True)
    visa_letter = models.BooleanField(default=False)
    postal_address = models.ForeignKey(
        PostalAddress, null=True, blank=True, on_delete=models.SET_NULL, related_name="requests", db_index=True
    )
    contact_phone_number = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    def __str__(self):
        return f"Request #{self.pk} for {self.event}"


class RequestExpense(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="expenses")
    subject = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    estimated_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_currency = models.CharField(max_length=10, null=True, blank=True)
    approved_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    approved_currency = models.CharField(max_length=10, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    authorized_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.subject or f"Expense #{self.pk}"


class Reimbursement(models.Model):
    state = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reimbursements")
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="reimbursements")
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    state_updated_at = models.DateTimeField(null=True, blank=True)
    acceptance_file = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Reimbursement #{self.pk}"


class BankAccount(models.Model):
    holder = models.CharField(max_length=255, null=True, blank=True)
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    format = models.CharField(max_length=255, null=True, blank=True)
    iban = models.CharField(max_length=255, null=True, blank=True)
    bic = models.CharField(max_length=255, null=True, blank=True)
    national_bank_code = models.CharField(max_length=255, null=True, blank=True)
    national_account_code = models.CharField(max_length=255, null=True, blank=True)
    country_code = models.CharField(max_length=10, null=True, blank=True)
    bank_postal_address = models.CharField(max_length=255, null=True, blank=True)
    reimbursement = models.ForeignKey(
        Reimbursement, null=True, blank=True, on_delete=models.CASCADE, related_name="bank_accounts"
    )
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.iban or f"BankAccount #{self.pk}"


class Payment(models.Model):
    reimbursement = models.ForeignKey(
        Reimbursement, null=True, blank=True, on_delete=models.CASCADE, related_name="payments"
    )
    date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, null=True, blank=True)
    cost_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_currency = models.CharField(max_length=10, null=True, blank=True)
    method = models.CharField(max_length=255, null=True, blank=True)
    code = models.CharField(max_length=255, null=True, blank=True)
    subject = models.CharField(max_length=255, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    file = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.subject or f"Payment #{self.pk}"


class ReimbursementAttachment(models.Model):
    reimbursement = models.ForeignKey(Reimbursement, on_delete=models.CASCADE, related_name="attachments")
    title = models.CharField(max_length=255)
    file = models.CharField(max_length=255)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class ReimbursementLink(models.Model):
    reimbursement = models.ForeignKey(Reimbursement, on_delete=models.CASCADE, related_name="links")
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


# ---------- Polymorphic / generic ----------

class Audit(models.Model):
    # auditable
    auditable_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="audits_as_auditable", null=True, blank=True
    )
    auditable_object_id = models.IntegerField(null=True, blank=True)
    auditable = GenericForeignKey("auditable_content_type", "auditable_object_id")

    # user (polymorphic in Rails)
    user_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="audits_as_user", null=True, blank=True
    )
    user_object_id = models.IntegerField(null=True, blank=True)
    user = GenericForeignKey("user_content_type", "user_object_id")

    action = models.CharField(max_length=255, null=True, blank=True)
    audited_changes = models.TextField(null=True, blank=True)
    version = models.IntegerField(default=0)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    remote_address = models.CharField(max_length=255, null=True, blank=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    request_uuid = models.CharField(max_length=255, null=True, blank=True)

    # associated
    associated_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="audits_as_associated", null=True, blank=True
    )
    associated_object_id = models.IntegerField(null=True, blank=True)
    associated = GenericForeignKey("associated_content_type", "associated_object_id")

    class Meta:
        indexes = [
            models.Index(fields=["associated_content_type", "associated_object_id"], name="associated_index"),
            models.Index(fields=["auditable_content_type", "auditable_object_id", "version"], name="auditable_index"),
            models.Index(fields=["created_at"], name="index_audits_on_created_at"),
            models.Index(fields=["request_uuid"], name="index_audits_on_request_uuid"),
            models.Index(fields=["user_content_type", "user_object_id"], name="user_index"),
        ]

    def __str__(self):
        return f"Audit #{self.pk} {self.action or ''}".strip()


class Comment(models.Model):
    # machine
    machine_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="comments_as_machine", null=True, blank=True
    )
    machine_object_id = models.IntegerField(null=True, blank=True)
    machine = GenericForeignKey("machine_content_type", "machine_object_id")

    body = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="comments")
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    private = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["private"], name="index_comments_on_private")]

    def __str__(self):
        return (self.body or "").split("\n", 1)[0][:60]


class StateChange(models.Model):
    # machine
    machine_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="state_changes_as_machine")
    machine_object_id = models.IntegerField()
    machine = GenericForeignKey("machine_content_type", "machine_object_id")

    state_event = models.CharField(max_length=255, null=True, blank=True)
    from_state = models.CharField(max_length=255)  # Rails column "from"
    to_state = models.CharField(max_length=255)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="state_changes")
    notes = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    type = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    def __str__(self):
        return f"{self.from_state} → {self.to_state}"


# ---------- Emails & organizers ----------

class EventEmail(models.Model):
    to = models.TextField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="event_emails")
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.SET_NULL, related_name="emails")
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.subject


class EventOrganizer(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="event_organizers")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="event_organizers")

    class Meta:
        unique_together = [("event", "user")]

    def __str__(self):
        return f"{self.user} organizes {self.event}"


# ---------- Background jobs ----------

class DelayedJob(models.Model):
    priority = models.IntegerField(default=0)
    attempts = models.IntegerField(default=0)
    handler = models.TextField()
    last_error = models.TextField(null=True, blank=True)
    run_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.CharField(max_length=255, null=True, blank=True)
    queue = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["priority", "run_at"], name="delayed_jobs_priority")]

    def __str__(self):
        return f"Job #{self.pk} (prio {self.priority})"


# ---------- Profiles / roles ----------

class Role(models.Model):
    # Added because schema referenced role_id but didn't include roles table
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="profile")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="user_profiles")
    full_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    country_code = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    second_phone_number = models.CharField(max_length=20, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    website = models.CharField(max_length=255, null=True, blank=True)
    blog = models.CharField(max_length=255, null=True, blank=True)
    passport = models.CharField(max_length=255, null=True, blank=True)
    alternate_id_document = models.CharField(max_length=255, null=True, blank=True)
    zip_code = models.CharField(max_length=20, null=True, blank=True)
    postal_address = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.full_name or f"Profile of {self.user}"
