# In the name of Allah, The Most Gracious, The Most Merciful
from datetime import datetime


class PropertyRules:
    @staticmethod
    def validate(prop: "Property") -> tuple[bool, list[str]]:
        errors = []

        # --- Price rules ---
        if prop.price is not None and prop.price <= 0:
            errors.append("Price must be greater than 0")

        # --- Area rules ---
        if prop.area is not None and prop.area <= 0:
            errors.append("Area must be greater than 0")

        # --- Beds rules ---
        if prop.beds is not None and isinstance(prop.beds, int) and prop.beds <= 0:
            errors.append("Beds must be greater than 0")
        if prop.beds is not None and isinstance(prop.beds, int) and prop.beds > 20:
            errors.append("Unrealistic number of beds")

        # --- Baths rules ---
        if prop.baths is not None and isinstance(prop.baths, int) and prop.baths <= 0:
            errors.append("Baths must be greater than 0")

        # --- Furnishing rules ---
        if prop.furnishing is not None:
            valid_furnishing = ["Furnished", "Unfurnished", "Semi-Furnished","Yes","No"]
            if prop.furnishing not in valid_furnishing:
                errors.append(f"Invalid furnishing value: '{prop.furnishing}'")

        # --- Date rules ---
        if prop.reactivated_date and prop.reactivated_date > datetime.now():
            errors.append("Reactivated date cannot be in the future")

        # --- Link rules ---
        if prop.link is not None and "http" not in prop.link:
            errors.append("Invalid link")

        # --- Source rules ---
        valid_sources = ["bayut", "dubizzle", "olx", "aqarmap", "unknown"]
        if prop.source not in valid_sources:
            errors.append(f"Invalid source: '{prop.source}'")

        return len(errors) == 0, errors