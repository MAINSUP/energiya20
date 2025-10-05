

def score_lead(lead):
    """
    lead: dict with keys: name, email, phone, service_type, kWt, status
    """
    score = 0

    # Base points for completed fields
    score += 1 if lead.get("name") else 0
    score += 1 if lead.get("email") else 0
    score += 1 if lead.get("phone") else 0
    score += 1 if lead.get("service_type") else 0

    # Weight based on service type
    service_type = lead.get("service_type", "").lower()
    if service_type == "solar":
        score += 2
    elif service_type == "storage":
        score += 1.5
    elif service_type == "wind":
        score += 2

    # Add points proportional to kWt if provided
    try:
        score += float(lead.get("kWt", 0)) / 10
    except:
        pass

    return round(score, 1)
