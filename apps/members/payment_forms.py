"""
Payment forms for membership payments.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from apps.dashboard.models import Payment
from .payment_utils import MEMBERSHIP_FEE


class MembershipPaymentForm(forms.Form):
    """Form for initiating membership payment."""
    
    payment_method = forms.ChoiceField(
        label=_("Payment Method"),
        choices=[
            ("manual", _("Manual Payment (Bank Transfer)")),
            ("stripe", _("Credit Card (Stripe)")),
            ("paypal", _("PayPal")),
        ],
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        initial="manual",
    )
    
    notes = forms.CharField(
        label=_("Notes (optional)"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": _("Any additional information about your payment..."),
            }
        ),
    )
    
    amount = forms.DecimalField(
        label=_("Amount"),
        initial=MEMBERSHIP_FEE,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "readonly": True,
                "step": "0.01",
            }
        ),
    )


class ManualPaymentConfirmationForm(forms.Form):
    """Form for confirming manual payment."""
    
    transaction_reference = forms.CharField(
        label=_("Transaction Reference"),
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Your bank transfer reference number"),
            }
        ),
        help_text=_("Optional: Provide your bank transfer reference if available."),
    )
    
    notes = forms.CharField(
        label=_("Additional Notes"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": _("Any additional information..."),
            }
        ),
    )

