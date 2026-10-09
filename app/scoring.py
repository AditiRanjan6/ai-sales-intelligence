def calculate_lead_score(lead):
    score = 0

    # Company size
    size_scores = {
        "11-50": 5,
        "51-200": 10,
        "201-500": 15,
        "501-1000": 18,
        "1001-5000": 20,
    }

    score += size_scores.get(lead["company_size"], 0)

    # Website activity
    activity_scores = {
        "Low": 3,
        "Medium": 8,
        "High": 12,
    }

    score += activity_scores.get(lead["website_activity"], 0)

    # Email engagement
    engagement_scores = {
        "Low": 3,
        "Medium": 8,
        "High": 12,
    }

    score += engagement_scores.get(lead["email_engagement"], 0)

    # Technology fit
    technology_scores = {
        "Low": 2,
        "Medium": 7,
        "High": 12,
    }

    score += technology_scores.get(lead["technology_fit"], 0)

    # Buying signal
    buying_signal_scores = {
        "Weak": 3,
        "Moderate": 8,
        "Strong": 15,
    }

    score += buying_signal_scores.get(lead["buying_signal"], 0)

    # Recency of last activity
    days_since_activity = int(lead["last_activity_days"])

    if days_since_activity <= 3:
        score += 10
    elif days_since_activity <= 7:
        score += 7
    elif days_since_activity <= 14:
        score += 4
    else:
        score += 1

    return min(score, 100)


def get_priority(score):
    if score >= 70:
        return "HOT"
    elif score >= 45:
        return "WARM"
    else:
        return "COLD"