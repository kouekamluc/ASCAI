"""
URL configuration for members app.
"""

from django.urls import path
from . import views

app_name = "members"

urlpatterns = [
    path("", views.member_directory, name="directory"),
    path("profile/<int:user_id>/", views.member_profile, name="profile"),
    path("edit/", views.edit_profile, name="edit_profile"),
    path("edit/<int:user_id>/", views.edit_profile, name="edit_profile"),
    path("export/csv/", views.export_members_csv, name="export_csv"),
    path("bulk-update/", views.bulk_update_status, name="bulk_update"),
    # Application routes
    path("apply/", views.apply_for_membership, name="apply"),
    path("application/status/", views.view_application_status, name="application_status"),
    path("applications/", views.application_list, name="application_list"),
    path("applications/<int:application_id>/review/", views.review_application, name="review_application"),
    # Verification routes
    path("verify/<int:member_id>/", views.verify_member, name="verify_member"),
    # Badge routes
    path("badges/award/<int:member_id>/", views.award_badge_to_member, name="award_badge"),
    path("badges/remove/<int:achievement_id>/", views.remove_badge_from_member, name="remove_badge"),
    path("badges/check/<int:member_id>/", views.check_member_badges, name="check_badges"),
    # Payment routes
    path("pay/", views.pay_membership, name="pay_membership"),
    path("payment/<int:payment_id>/confirm/", views.payment_confirmation, name="payment_confirmation"),
    path("payment/<int:payment_id>/", views.payment_status, name="payment_status"),
    path("payments/history/", views.payment_history, name="payment_history"),
    path("payment/<int:payment_id>/approve/", views.approve_payment, name="approve_payment"),
]




















