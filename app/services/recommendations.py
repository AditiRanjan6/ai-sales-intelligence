from collections.abc import Mapping
from typing import Any, TypedDict


class LeadRecommendation(TypedDict):
    why_this_lead_matters: str
    key_signals: list[str]
    recommended_action: str
    next_best_action: str
    urgency: str


def generate_lead_recommendation(
    lead: Mapping[str, Any],
) -> LeadRecommendation:
    """Build a deterministic sales recommendation from an enriched lead."""
    score = int(lead["lead_score"])
    priority = str(lead["priority"]).upper()
    buying_signal = str(lead["buying_signal"]).lower()
    email_engagement = str(lead["email_engagement"]).lower()
    website_activity = str(lead["website_activity"]).lower()
    technology_fit = str(lead["technology_fit"]).lower()
    last_activity_days = int(lead["last_activity_days"])
    deal_size = float(lead["deal_size"])
    interactions = int(lead["interactions"])
    converted = str(lead["converted"]).lower() in {"1", "true", "yes"}

    formatted_deal_size = f"${deal_size:,.0f}"
    key_signals: list[str] = []

    if converted:
        key_signals.append(
            "Already converted - manage as an existing account, not a new prospect."
        )
    if buying_signal == "strong":
        key_signals.append(
            "Strong buying signal is recorded for this account."
            if converted
            else "Strong buying signal indicates active purchase intent."
        )
    elif buying_signal == "moderate":
        key_signals.append("Moderate buying signal suggests developing purchase interest.")
    else:
        key_signals.append("Weak buying signal means purchase intent needs qualification.")

    if email_engagement == "high":
        key_signals.append("High email engagement shows the lead is responding to outreach.")
    elif email_engagement == "medium":
        key_signals.append("Medium email engagement leaves room to improve outreach relevance.")
    else:
        key_signals.append("Low email engagement suggests testing a different outreach approach.")

    if website_activity == "high":
        key_signals.append("High website activity indicates active research.")
    elif website_activity == "medium":
        key_signals.append("Medium website activity shows some ongoing research.")
    else:
        key_signals.append("Low website activity indicates limited recent on-site research.")

    if technology_fit == "high":
        key_signals.append("High technology fit aligns well with the solution.")
    elif technology_fit == "medium":
        key_signals.append("Medium technology fit should be confirmed during qualification.")
    else:
        key_signals.append("Low technology fit may require additional qualification.")

    if last_activity_days <= 3:
        key_signals.append(
            f"Recent activity: last touch was {last_activity_days} "
            f"{'day' if last_activity_days == 1 else 'days'} ago."
        )
    elif last_activity_days <= 7:
        key_signals.append(f"Activity was {last_activity_days} days ago; follow up this week.")
    else:
        key_signals.append(
            f"No recent activity for {last_activity_days} days; re-engagement may be needed."
        )

    if deal_size >= 100_000:
        key_signals.append(f"Substantial commercial opportunity of {formatted_deal_size}.")
    elif deal_size >= 50_000:
        key_signals.append(f"Meaningful commercial opportunity of {formatted_deal_size}.")
    else:
        key_signals.append(f"Estimated deal size is {formatted_deal_size}.")

    if interactions >= 10:
        key_signals.append(f"High interaction volume ({interactions}) shows sustained engagement.")
    elif interactions <= 3:
        key_signals.append(f"Only {interactions} interactions so far; discovery is still needed.")
    else:
        key_signals.append(f"{interactions} interactions provide a basis for a tailored follow-up.")

    if converted:
        why_this_lead_matters = (
            f"This converted {priority.lower()} account has a lead score of "
            f"{score}/100 and an estimated {formatted_deal_size} opportunity. "
            "Focus on customer value, retention, and appropriate expansion "
            "rather than new-prospect qualification."
        )
        if priority == "HOT" or score >= 70:
            recommended_action = (
                "Prioritize prompt engagement as an existing customer; assess "
                "retention and expansion opportunities rather than qualifying a "
                "new prospect."
            )
            next_best_action = (
                f"Review the {interactions} recorded interactions, then coordinate "
                "a customer-success check-in within one business day to discuss "
                "outcomes and account goals."
            )
            urgency = "HIGH"
        elif priority == "WARM" or score >= 45:
            recommended_action = (
                "Schedule a timely existing-customer check-in focused on account "
                "health, retention, and suitable expansion."
            )
            next_best_action = (
                f"Review the {interactions} recorded interactions and current "
                "engagement, then coordinate a customer-success check-in this week."
            )
            urgency = "MEDIUM"
        else:
            recommended_action = (
                "Keep this existing account in a lower-priority customer-success "
                "nurture track; do not qualify it as a fresh prospect."
            )
            next_best_action = (
                f"Review the {interactions} recorded interactions and schedule a "
                "routine account-health touchpoint when appropriate."
            )
            urgency = "LOW"
    else:
        why_this_lead_matters = (
            f"This {priority.lower()} lead scored {score}/100 and represents an "
            f"estimated {formatted_deal_size} opportunity. Its buying signal is "
            f"{buying_signal}, with {interactions} recorded interactions."
        )

        if priority == "HOT" or score >= 70:
            recommended_action = (
                "Prioritize this lead for prompt, personalized sales outreach."
            )
            urgency = "HIGH"
            if last_activity_days <= 3:
                next_best_action = (
                    f"Contact the lead today while activity is recent; reference the "
                    f"{buying_signal} buying signal and request a discovery meeting."
                )
            else:
                next_best_action = (
                    f"Contact promptly, reference the {buying_signal} buying signal, "
                    "and request a discovery meeting."
                )
        elif priority == "WARM" or score >= 45:
            recommended_action = (
                "Nurture the lead with a relevant follow-up and qualify its timeline."
            )
            urgency = "MEDIUM"
            if last_activity_days > 7:
                next_best_action = (
                    "Re-engage with a relevant case study or insight, then confirm "
                    "the lead's current priorities and timing."
                )
            else:
                next_best_action = (
                    "Send a personalized follow-up based on the lead's research and "
                    "ask what would help move its evaluation forward."
                )
        else:
            recommended_action = (
                "Keep this lead in a lower-priority nurture track rather than "
                "assigning immediate sales attention."
            )
            urgency = "LOW"
            next_best_action = (
                "Add the lead to a low-frequency nurture sequence and revisit it "
                "when new engagement or buying intent appears."
            )

    return {
        "why_this_lead_matters": why_this_lead_matters,
        "key_signals": key_signals,
        "recommended_action": recommended_action,
        "next_best_action": next_best_action,
        "urgency": urgency,
    }
