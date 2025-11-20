"""
Forms for members app.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Member, MemberApplication, MemberBadge, MemberAchievement


class MemberProfileForm(forms.ModelForm):
    """Form for member profile editing."""
    
    class Meta:
        model = Member
        fields = [
            'university', 'course', 'year_of_study', 'graduation_year',
            'city', 'country_of_origin', 'date_of_birth',
            'profile_public', 'email_public',
            'linkedin', 'website',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }


class MemberAdminForm(forms.ModelForm):
    """Form for admin member management."""
    
    class Meta:
        model = Member
        fields = '__all__'


class MemberApplicationForm(forms.ModelForm):
    """Form for membership application."""
    
    class Meta:
        model = MemberApplication
        fields = ['notes']


class MemberApplicationReviewForm(forms.ModelForm):
    """Form for reviewing member applications."""
    
    class Meta:
        model = MemberApplication
        fields = ['status', 'review_notes']


class BulkEmailForm(forms.Form):
    """Form for sending bulk emails to members."""
    
    RECIPIENT_CHOICES = [
        ('all', _('All Active Members')),
        ('students', _('Students Only')),
        ('alumni', _('Alumni Only')),
        ('honorary', _('Honorary Members Only')),
        ('custom', _('Custom Selection')),
    ]
    
    recipients = forms.ChoiceField(
        choices=RECIPIENT_CHOICES,
        label=_("Recipients"),
        widget=forms.RadioSelect,
    )
    custom_recipients = forms.ModelMultipleChoiceField(
        queryset=Member.objects.filter(status=Member.MembershipStatus.ACTIVE),
        required=False,
        label=_("Select Members"),
        widget=forms.CheckboxSelectMultiple,
    )
    subject = forms.CharField(
        max_length=200,
        label=_("Subject"),
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    message = forms.CharField(
        label=_("Message"),
        widget=forms.Textarea(attrs={'rows': 10, 'class': 'form-control'}),
    )
    send_as_html = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Send as HTML email"),
        help_text=_("If unchecked, email will be sent as plain text"),
    )
    
    def clean(self):
        cleaned_data = super().clean()
        recipients = cleaned_data.get('recipients')
        custom_recipients = cleaned_data.get('custom_recipients')
        
        if recipients == 'custom' and not custom_recipients:
            raise forms.ValidationError(
                _("Please select at least one member when using custom selection.")
            )
        
        return cleaned_data
