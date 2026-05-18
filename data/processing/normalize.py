# In the name of Allah , The most gracious , The most merciful 
def normalize_row(row: dict) -> dict:
    return {
        "price": row.get("Price") or row.get('price'),
        "location": row.get("Location") or row.get('location'),
        "title": row.get("Title") or row.get("title"),
        "beds": row.get("Beds") or  row.get("beds") or row.get('rooms'),
        "baths": row.get("Baths") or  row.get("baths"),
        "area": row.get("Area") or row.get("area"),
        "property_type": row.get("Type") or row.get('type'),
        "furnishing": row.get("Furnishing", None) or row.get('furnishing',None),
        "amenities": row.get("Amenities", "[]") or row.get('amenities',"[]"),
        "link": row.get("Link") or row.get('link'),
        "reactivated_date": row.get("Reactivated date", None) or row.get('Reactivated_Date',None),
    }
