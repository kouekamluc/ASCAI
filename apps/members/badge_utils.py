"""
Badge utility functions for auto-awarding badges.
"""

from django.utils import timezone
from datetime import timedelta
from .models import Member, MemberBadge, MemberAchievement


def award_badge(member, badge, notes=""):
    """Award a badge to a member if they don't already have it."""
    if not MemberAchievement.objects.filter(member=member, badge=badge).exists():
        MemberAchievement.objects.create(member=member, badge=badge, notes=notes)
        return True
    return False


def check_and_award_badges(member):
    """Check member eligibility and award badges automatically."""
    awards = []
    
    # Active Member badge
    if member.is_active_member():
        active_badge = MemberBadge.objects.filter(
            name__icontains="active member",
            category=MemberBadge.BadgeCategory.MEMBERSHIP,
        ).first()
        if active_badge:
            if award_badge(member, active_badge, "Awarded for active membership status"):
                awards.append(active_badge)
    
    # Verified Member badge
    if member.is_verified:
        verified_badge = MemberBadge.objects.filter(
            name__icontains="verified",
            category=MemberBadge.BadgeCategory.MEMBERSHIP,
        ).first()
        if verified_badge:
            if award_badge(member, verified_badge, "Awarded for verified membership"):
                awards.append(verified_badge)
    
    # Long-term Member badge (1+ year)
    if member.joined_date:
        membership_duration = timezone.now().date() - member.joined_date
        if membership_duration >= timedelta(days=365):
            long_term_badge = MemberBadge.objects.filter(
                name__icontains="long-term",
                category=MemberBadge.BadgeCategory.MEMBERSHIP,
            ).first()
            if long_term_badge:
                if award_badge(member, long_term_badge, "Awarded for 1+ year membership"):
                    awards.append(long_term_badge)
    
    # Alumni badge
    if member.category == Member.MemberCategory.ALUMNI:
        alumni_badge = MemberBadge.objects.filter(
            name__icontains="alumni",
            category=MemberBadge.BadgeCategory.MEMBERSHIP,
        ).first()
        if alumni_badge:
            if award_badge(member, alumni_badge, "Awarded for alumni status"):
                awards.append(alumni_badge)
    
    return awards

