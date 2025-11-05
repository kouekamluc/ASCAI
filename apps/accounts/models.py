"""
User models for ASCAI platform.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with email and password."""
        if not email:
            raise ValueError(_("The Email field must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model with role-based access control."""

    class Role(models.TextChoices):
        ADMIN = "admin", _("Admin")
        BOARD = "board", _("Board Member")
        MEMBER = "member", _("Member")
        PUBLIC = "public", _("Public")

    username = None  # Remove username field
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)
    role = models.CharField(
        max_length=10, choices=Role.choices, default=Role.PUBLIC
    )
    is_active = models.BooleanField(_("active"), default=True)
    date_joined = models.DateTimeField(_("date joined"), auto_now_add=True)
    last_login = models.DateTimeField(_("last login"), auto_now=True)
    profile_picture = models.ImageField(
        upload_to="profiles/", blank=True, null=True
    )
    bio = models.TextField(_("bio"), blank=True)
    phone = models.CharField(_("phone"), max_length=20, blank=True)
    verification_token_created_at = models.DateTimeField(
        _("verification token created at"), blank=True, null=True
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["is_active", "role"]),
            models.Index(fields=["date_joined"]),
            models.Index(fields=["verification_token_created_at"]),
        ]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}"

    def is_admin(self):
        """Check if user is an admin."""
        return self.role == self.Role.ADMIN or self.is_superuser

    def is_board_member(self):
        """Check if user is a board member."""
        return self.role == self.Role.BOARD or self.is_admin()

    def is_member(self):
        """Check if user is a member."""
        return self.role in [self.Role.MEMBER, self.Role.BOARD, self.Role.ADMIN]


class FailedLoginAttempt(models.Model):
    """Track failed login attempts for account lockout mechanism."""

    email = models.EmailField(_("email address"), db_index=True)
    ip_address = models.GenericIPAddressField(_("IP address"), db_index=True)
    attempted_at = models.DateTimeField(_("attempted at"), auto_now_add=True, db_index=True)
    user_agent = models.TextField(_("user agent"), blank=True)

    class Meta:
        verbose_name = _("failed login attempt")
        verbose_name_plural = _("failed login attempts")
        ordering = ["-attempted_at"]
        indexes = [
            models.Index(fields=["email", "attempted_at"]),
            models.Index(fields=["ip_address", "attempted_at"]),
        ]

    def __str__(self):
        return f"Failed login: {self.email} from {self.ip_address} at {self.attempted_at}"

    @classmethod
    def get_recent_attempts_for_email(cls, email, minutes=15):
        """Get recent failed attempts for an email address."""
        cutoff = timezone.now() - timezone.timedelta(minutes=minutes)
        return cls.objects.filter(email=email, attempted_at__gte=cutoff)

    @classmethod
    def get_recent_attempts_for_ip(cls, ip_address, minutes=60):
        """Get recent failed attempts for an IP address."""
        cutoff = timezone.now() - timezone.timedelta(minutes=minutes)
        return cls.objects.filter(ip_address=ip_address, attempted_at__gte=cutoff)

    @classmethod
    def is_email_locked(cls, email, max_attempts=5, lockout_minutes=15):
        """Check if email is locked due to too many failed attempts."""
        recent_attempts = cls.get_recent_attempts_for_email(email, minutes=lockout_minutes)
        return recent_attempts.count() >= max_attempts

    @classmethod
    def is_ip_locked(cls, ip_address, max_attempts=10, lockout_minutes=60):
        """Check if IP is locked due to too many failed attempts."""
        recent_attempts = cls.get_recent_attempts_for_ip(ip_address, minutes=lockout_minutes)
        return recent_attempts.count() >= max_attempts

    @classmethod
    def record_failed_attempt(cls, email, ip_address, user_agent=""):
        """Record a failed login attempt."""
        return cls.objects.create(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @classmethod
    def clear_attempts_for_email(cls, email):
        """Clear all failed attempts for an email (after successful login)."""
        cls.objects.filter(email=email).delete()
