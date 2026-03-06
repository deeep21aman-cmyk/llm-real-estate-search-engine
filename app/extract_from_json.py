import json


def print_key_value(obj,indent=0):
    if isinstance(obj, dict):
        for key,value in obj.items():

            if isinstance(value,int) or isinstance(value,str):
                print("    " * indent + f"{key} -> {type(value)}")

            if isinstance(value, list):
                print("    " * indent + f"{key} -> list (length {len(value)})")

                if len(value) > 0:
                    first_element = value[0]

                    if isinstance(first_element, dict):
                        print_key_value(first_element, indent + 1)
                    else:
                        print("    " * (indent + 1) + f"element_type -> {type(first_element)}")

            if isinstance(value,dict):
                print("    " * indent + f"{key} -> dict")
                print_key_value(value, indent + 1)


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
    wp_id = property_data.get("id")
    modified = property_data.get("modified")
    status = property_data.get("status")
    is_active=True if status and status.lower()=="publish" else False
    property_type = property_data.get("type")
    link = property_data.get("link")
    title=property_data.get("title",{}).get("rendered")
    title=title.strip() if title else None
    description=property_data.get("content",{}).get("rendered")
    description = description.strip() if description else None
    meta=property_data.get("property_meta",{})
    print(meta.get("REAL_HOMES_property_bedrooms"))
    price = to_float(meta.get("REAL_HOMES_property_price"))
    old_price = to_float(meta.get("REAL_HOMES_property_old_price"))
    bedrooms = to_int(meta.get("REAL_HOMES_property_bedrooms"))
    bathrooms = to_int(meta.get("REAL_HOMES_property_bathrooms"))
    size = to_float(meta.get("REAL_HOMES_property_size"))
    lot_size = to_float(meta.get("REAL_HOMES_property_lot_size"))
    year_built = to_int(meta.get("REAL_HOMES_property_year_built"))
    address=meta.get("REAL_HOMES_property_address")  
    location = meta.get("REAL_HOMES_property_location", {})
    latitude = to_float(location.get("latitude"))
    longitude = to_float(location.get("longitude"))
    return{"slug":slug,
            "wp_id":wp_id,
            "modified":modified,
            "status":status,
            "is_active":is_active,
            "property_type":property_type,
            "link":link,
            "title":title,
            "description":description,
            "current_price":price,
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
