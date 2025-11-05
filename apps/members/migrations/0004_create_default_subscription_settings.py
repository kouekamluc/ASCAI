# Generated manually to create default subscription settings

from django.db import migrations


def create_default_settings(apps, schema_editor):
    """Create default membership subscription settings."""
    MembershipSubscriptionSettings = apps.get_model('members', 'MembershipSubscriptionSettings')
    # Create default settings if they don't exist
    MembershipSubscriptionSettings.objects.get_or_create(
        pk=1,
        defaults={
            'default_subscription_duration_years': 2,
        }
    )


def reverse_default_settings(apps, schema_editor):
    """Remove default settings (optional - can be left empty)."""
    MembershipSubscriptionSettings = apps.get_model('members', 'MembershipSubscriptionSettings')
    MembershipSubscriptionSettings.objects.filter(pk=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0003_membershipsubscriptionsettings'),
    ]

    operations = [
        migrations.RunPython(create_default_settings, reverse_default_settings),
    ]

