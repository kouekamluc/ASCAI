from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class AdminMessageForm(forms.Form):
    """Form for admins to send messages to users."""
    
    RECIPIENT_CHOICES = [
        ('all', _('All Users')),
        ('all_members', _('All Members')),
        ('active_members', _('Active Members Only')),
        ('selected', _('Selected Users')),
    ]
    
    recipient_type = forms.ChoiceField(
        choices=RECIPIENT_CHOICES,
        label=_('Recipient Type'),
        widget=forms.RadioSelect(attrs={'class': 'radio-group'}),
        initial='selected'
    )
    
    selected_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).exclude(role__in=['admin', 'board']).order_by('first_name', 'last_name'),
        required=False,
        label=_('Select Users'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'user-checkboxes'}),
        help_text=_('Select individual users to send the message to')
    )
    
    subject = forms.CharField(
        max_length=200,
        required=False,
        label=_('Subject (Optional)'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Message subject...')}),
        help_text=_('Optional subject line for the message')
    )
    
    content = forms.CharField(
        label=_('Message Content'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': _('Enter your message here...')
        }),
        help_text=_('The message content to send to selected users')
    )
    
    def clean(self):
        cleaned_data = super().clean()
        recipient_type = cleaned_data.get('recipient_type')
        selected_users = cleaned_data.get('selected_users')
        
        if recipient_type == 'selected' and not selected_users:
            raise forms.ValidationError(
                _('Please select at least one user when using "Selected Users" option.')
            )
        
        return cleaned_data

