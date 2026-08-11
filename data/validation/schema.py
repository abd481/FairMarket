# In the name of Allah , The most gracious , The most merciful
from pydantic import BaseModel, field_validator, model_validator, Field
from typing import Optional, List, Any
import ast
from datetime import datetime


class Property(BaseModel):
    """
    Canonical data model for a real estate listing.

    Responsibilities:
    - Enforce schema (types and required fields)
    - Normalize raw scraped data into consistent formats
    - Provide safe defaults for optional/missing fields
    """

    # --- Fields ---
    price: Optional[int] = None
    location: Optional[str] = None
    title: Optional[str] = None
    beds: Optional[Any] = None
    baths: Optional[Any] = None
    area: Optional[float] = None
    property_type: Optional[str] = None
    amenities: Optional[List[str]] = None
    link: Optional[str] = None
    furnishing: Optional[str] = None
    reactivated_date: Optional[datetime] = None

    # --- System / metadata fields ---
    source: str = "unknown"
    scraped_at: datetime = Field(default_factory=datetime.now)

    @field_validator("price", mode="before")
    @classmethod
    def clean_price(cls, v):
        """Strip currency symbols, commas, and whitespace then cast to int."""
        try:
            return int(str(v).replace(",", "").replace("EGP", "").strip())
        except:
            return None

    @field_validator("beds", "baths", mode="before")
    @classmethod
    def extract_number(cls, v):
        """Extract leading integer from strings like '4 Beds' or '10+'."""
        if v is None:
            return None
        try:
            return int(str(v).split()[0].replace("+", ""))
        except:
            return str(v).strip()

    @field_validator("area", mode="before")
    @classmethod
    def clean_area(cls, v):
        """Strip units like 'sqm' and cast to float."""
        try:
            return float(str(v).split()[0].replace(",", ""))
        except:
            return None

    @field_validator("amenities", mode="before")
    @classmethod
    def parse_amenities(cls, v):
        """Ensure amenities is always a list of strings or None."""
        if not v:
            return None
        if isinstance(v, list):
            return v
        try:
            return ast.literal_eval(str(v))
        except:
            return None

    @field_validator("furnishing", mode="before")
    @classmethod
    def clean_furnishing(cls, v):
        if not v or str(v).strip() == "":
            return None
        mapping = {
            "Yes": "Furnished",
            "No": "Unfurnished",
            "Furnished": "Furnished",
            "Unfurnished": "Unfurnished",
            "Semi-Furnished": "Semi-Furnished",
        }
        return mapping.get(str(v).strip(), str(v).strip())

    @field_validator("reactivated_date", mode="before")
    @classmethod
    def parse_date(cls, v):
        """
        Parse date string into datetime.

        Handles:
        - '12 March 2024'
        - Relative strings like '2 hours ago', '3 days ago' → datetime.now()
        """
        if not v or str(v).strip() == "":
            return None
        v_str = str(v).strip()
        if any(word in v_str for word in ("ago", "hour", "minute", "day")):
            return datetime.now()
        try:
            return datetime.strptime(v_str, "%d %B %Y")
        except:
            return None

    @model_validator(mode="after")
    def detect_source(self):
        """Infer listing source from the URL."""
        link = getattr(self, "link", "") or ""
        if "bayut" in link:
            self.source = "bayut"
        elif "dubizzle" in link:
            self.source = "dubizzle"
        elif "olx" in link:
            self.source = "olx"
        elif "aqarmap" in link:
            self.source = "aqarmap"
        else:
            self.source = "unknown"
        return self
