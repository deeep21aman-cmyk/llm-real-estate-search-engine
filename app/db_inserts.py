import psycopg
from config import DB_NAME, DB_USER, DB_HOST, DB_PORT

import psycopg
from config import DB_NAME, DB_USER, DB_HOST, DB_PORT

def get_connection():
    return psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        host=DB_HOST,
        port=DB_PORT
    )


def upsert_features(features):
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            for feature in features:
                cur.execute(
                    """
                    INSERT INTO features (id, name, slug, count)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id)
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        slug = EXCLUDED.slug,
                        count = EXCLUDED.count;
                    """,
                    (
                        feature["id"],
                        feature["name"],
                        feature["slug"],
                        feature["count"]
                    )
                )
    conn.close()

def upsert_properties(properties):
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            for prop in properties:
                cur.execute(
                    """
                    INSERT INTO properties (
                        slug, link, modified, status, is_active,
                        price, old_price, bedrooms, bathrooms,
                        size, lot_size, year_built,
                        latitude, longitude,
                        title, description, address
                    )
                    VALUES (%s, %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s,
                            %s, %s, %s)
                    ON CONFLICT (slug)
                    DO UPDATE SET
                        link = EXCLUDED.link,
                        modified = EXCLUDED.modified,
                        status = EXCLUDED.status,
                        is_active = EXCLUDED.is_active,
                        price = EXCLUDED.price,
                        old_price = EXCLUDED.old_price,
                        bedrooms = EXCLUDED.bedrooms,
                        bathrooms = EXCLUDED.bathrooms,
                        size = EXCLUDED.size,
                        lot_size = EXCLUDED.lot_size,
                        year_built = EXCLUDED.year_built,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        title = EXCLUDED.title,
                        description = EXCLUDED.description,
                        address = EXCLUDED.address,
                        updated_at = NOW() RETURNING id;
                    """,
                    (
                        prop["slug"],
                        prop["link"],
                        prop["modified"],
                        prop["status"],
                        prop["is_active"],
                        prop["price"],
                        prop["old_price"],
                        prop["bedrooms"],
                        prop["bathrooms"],
                        prop["size"],
                        prop["lot_size"],
                        prop["year_built"],
                        prop["latitude"],
                        prop["longitude"],
                        prop["title"],
                        prop["description"],
                        prop["address"],
                    )
                    
                )
                row=cur.fetchone()
                property_id=row[0]
                cur.execute("DELETE FROM property_features WHERE property_id=%s",(property_id,))
                for feature in prop["feature_ids"]:
                    cur.execute('''INSERT INTO property_features(property_id,feature_id) VALUES (%s,%s)
                                ''',(property_id,feature))


    conn.close()