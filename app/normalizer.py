import re
import html


def clean_html(text):
    if not text:
        return None

    # Remove script, style, iframe, and figure blocks completely
    text = re.sub(r'<(script|style|iframe|figure).*?>.*?</\1>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # Replace paragraph and line break tags with newline
    text = re.sub(r'</p>|<br\s*/?>', '\n', text, flags=re.IGNORECASE)

    # Remove all remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Decode HTML entities (&amp;, &#8217;, etc.)
    text = html.unescape(text)

    # Normalize whitespace
    text = re.sub(r'\n\s*\n+', '\n\n', text)   # collapse multiple blank lines
    text = re.sub(r'[ \t]+', ' ', text)        # collapse multiple spaces
    text = text.strip()

    return text


def to_float(value):
    if not value:
        return None
    cleaned=str(value).strip()
    cleaned=cleaned.replace(",","")
    cleaned=cleaned.replace("$","")
    try:
        return float(cleaned)
    except:
        return None

def to_int(value):
    if not value:
        return None
    cleaned=str(value).strip()
    cleaned=cleaned.replace(",","")
    try:
        return int(cleaned)
    except:
        return None

def build_property_object(property_data):
    slug = property_data.get("slug")
    modified = property_data.get("modified")
    status = property_data.get("status")
    is_active=True if status and status.lower()=="publish" else False
    property_type = property_data.get("type")
    link = property_data.get("link")
    title=property_data.get("title",{}).get("rendered")
    title=title.strip() if title else None
    description=property_data.get("content",{}).get("rendered")
    description = clean_html(description)
    feature_ids=property_data.get("property-features",[])
    meta=property_data.get("property_meta",{})
    price = to_float(meta.get("REAL_HOMES_property_price"))
    old_price = to_float(meta.get("REAL_HOMES_property_old_price"))
    raw_bedrooms = meta.get("REAL_HOMES_property_bedrooms")
    if raw_bedrooms == "S" or raw_bedrooms == "Studio":
        bedrooms = 1
    else:
        bedrooms = to_int(raw_bedrooms)
    bathrooms = to_int(meta.get("REAL_HOMES_property_bathrooms"))
    size = to_float(meta.get("REAL_HOMES_property_size"))
    lot_size = to_float(meta.get("REAL_HOMES_property_lot_size"))
    year_built = to_int(meta.get("REAL_HOMES_property_year_built"))
    address=meta.get("REAL_HOMES_property_address")  
    address = address.strip() if address else None
    location = meta.get("REAL_HOMES_property_location", {})
    latitude = to_float(location.get("latitude"))
    longitude = to_float(location.get("longitude"))
    if not isinstance(feature_ids, list):
        feature_ids = []
    cleaned_feature_ids = []

    for fid in feature_ids:
        try:
            cleaned_feature_ids.append(int(fid))
        except:
            continue
    feature_ids = cleaned_feature_ids
    return{"slug":slug,
            "modified":modified,
            "status":status,
            "is_active":is_active,
            "property_type":property_type,
            "link":link,
            "title":title,
            "description":description,
            "feature_ids":feature_ids,
            "price":price,
            "old_price":old_price,
            "bedrooms":bedrooms,
            "bathrooms":bathrooms,
            "size":size,
            "lot_size":lot_size,
            "year_built":year_built,
            "address":address,
            "latitude":latitude,
            "longitude":longitude
    }

def build_feature_object(feature_data):
    feature_id = feature_data.get("id")
    count = feature_data.get("count")
    name = feature_data.get("name")
    name = name.strip() if name else None
    slug = feature_data.get("slug")
    return{"id":feature_id,
           "slug":slug,
           "count":count,
           "name":name,}