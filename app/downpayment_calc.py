import re
from decimal import Decimal
from app.db import get_connection


def extract_down_payment(text, price):

    if not text:
        return None, None

    text = text.lower()

    percent = None
    amount = None

    # ----------------------------------
    # 1. Mixed pattern ($5000 + 20%)
    # ----------------------------------

    mixed = re.search(r"\$([0-9,]+)\s*\+\s*([0-9]{1,2})%", text)
    if mixed:
        amount = Decimal(mixed.group(1).replace(",", ""))
        percent = Decimal(mixed.group(2))
        return percent, amount


    # ----------------------------------
    # 2. Down payment amount
    # ----------------------------------

    amount_patterns = [
        r"\$([0-9,]+)\s*down\s*payment",
        r"\$([0-9,]+)\s*downpayment",
        r"down\s*payment[:\s]*\$([0-9,]+)",
        r"reservation\s*deposit[:\s]*\$([0-9,]+)",
        r"deposit[:\s]*\$([0-9,]+)",
        r"reserve\s*with\s*\$([0-9,]+)"
    ]

    for pattern in amount_patterns:
        match = re.search(pattern, text)
        if match:
            amount = Decimal(match.group(1).replace(",", ""))
            break


    # ----------------------------------
    # 3. Percent down payment
    # ----------------------------------

    percent_patterns = [
        r"([0-9]{1,2})%\s*down",
        r"down\s*payment[:\s]*([0-9]{1,2})%",
        r"([0-9]{1,2})%\s*deposit",
        r"([0-9]{1,2})%\s*of\s*purchase\s*price"
    ]

    for pattern in percent_patterns:
        match = re.search(pattern, text)
        if match:
            percent = Decimal(match.group(1))
            break


    # ----------------------------------
    # 4. Payment plan (first percent)
    # ----------------------------------

    if percent is None:

        plan_match = re.search(r"payment\s*plan[:\s]*([0-9]{1,2})%", text)

        if plan_match:
            percent = Decimal(plan_match.group(1))


    # ----------------------------------
    # 5. Any percent list fallback
    # ----------------------------------

    if percent is None:

        percents = re.findall(r"([0-9]{1,2})%", text)

        if percents:
            percent = Decimal(percents[0])


    # ----------------------------------
    # 6. Compute amount if missing
    # ----------------------------------

    if percent and not amount and price:
        amount = (Decimal(price) * percent) / Decimal(100)


    return percent, amount


def update_down_payments():

    conn = get_connection()

    updated = 0

    with conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT id, embedding_text, price
                FROM properties
            """)

            rows = cur.fetchall()

            for row in rows:

                property_id = row[0]
                text = row[1]
                price = row[2]

                percent, amount = extract_down_payment(text, price)

                if percent or amount:

                    cur.execute("""
                        UPDATE properties
                        SET down_payment_percent = %s,
                            down_payment_amount = %s
                        WHERE id = %s
                    """, (percent, amount, property_id))

                    updated += 1

    conn.close()

    print("Rows updated:", updated)


if __name__ == "__main__":
    update_down_payments()
