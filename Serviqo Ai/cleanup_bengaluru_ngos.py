import database
import json

def clean_bengaluru_ngos():
    with database.get_db() as conn:
        cursor = conn.cursor()

        # 1. Update ID 1 to ISKCON Mangalore if it was Bangalore Akshaya Patra
        cursor.execute("SELECT id, name, address FROM ngos WHERE id = 1")
        row1 = cursor.fetchone()
        if row1:
            cursor.execute("""
                UPDATE ngos
                SET name = 'ISKCON Food Relief Foundation - Mangalore',
                    address = 'ISKCON Temple, Arya Samaj Road, Balmatta, Mangalore',
                    manager = 'Anita Desai',
                    phone = '+91 824 242 1234',
                    email = 'iskcon.mangalore@serviqo.ai',
                    latitude = 12.8698,
                    longitude = 74.8430
                WHERE id = 1
            """)
            print("Updated NGO #1 to ISKCON Mangalore.")

        # 2. Re-assign any donations linked to other Bengaluru NGOs (2, 3, 4, 5) to Mangalore NGOs
        cursor.execute("UPDATE donations SET ngo_id = 1, ngo_name = 'ISKCON Food Relief Foundation - Mangalore' WHERE ngo_id IN (2, 3, 4, 5)")
        print("Reassigned donations from Bengaluru NGOs to ISKCON Mangalore.")

        # 3. Delete any NGO whose address or name mentions Bengaluru / Bangalore
        cursor.execute("""
            DELETE FROM ngos 
            WHERE LOWER(address) LIKE '%bengaluru%' 
               OR LOWER(address) LIKE '%bangalore%' 
               OR LOWER(name) LIKE '%bengaluru%' 
               OR LOWER(name) LIKE '%bangalore%'
        """)
        deleted_count = cursor.rowcount
        print(f"Deleted {deleted_count} Bengaluru NGOs from database.")

        # 4. Ensure Mangalore NGOs exist
        mangalore_ngos = [
            ("ISKCON Food Relief Foundation - Mangalore", "Food Relief & Ashram Support", "high", 12.8698, 74.8430, "ISKCON Temple, Arya Samaj Road, Balmatta, Mangalore", "Anita Desai", "+91 824 242 1234", "iskcon.mangalore@serviqo.ai", 450, json.dumps(["Cooked Rice", "Dal", "Sambar", "Vegetables", "Curd"])),
            ("Sri Ramakrishna Ashram & Orphanage", "Ashram & Orphanage", "high", 12.9200, 74.8500, "Mangaladevi Road, Bolar, Mangalore", "Swami Prakash", "+91 98450 12345", "contact@ramakrishnaashram.org", 150, json.dumps(["Dal", "Rice", "Idli", "Sambar", "Vegetable Curry"])),
            ("Karunya Community Feeding Kitchen", "Community Kitchen", "high", 12.9180, 74.8580, "Near Hampankatta Circle, Mangalore", "Mahesh Prabhu", "+91 99001 88776", "karunyafeeding@gmail.com", 180, json.dumps(["All Cooked Meals", "Rice", "Dal", "Idli", "Sambar"])),
            ("Robin Hood Army - Mangalore Chapter", "Volunteer Food Rescue & Hunger Relief", "high", 12.8700, 74.8800, "City Center Area, K.S. Rao Road, Mangalore", "Priya Sharma", "+91 98200 45678", "rescue.mangalore@robinhoodarmy.com", 300, json.dumps(["Prepared Meals", "Rice", "Chapatis", "Curries", "Fruits"])),
            ("Sneha Sadan Care Home - Mangalore", "Care Home & Shelter", "high", 12.9450, 74.9300, "Gurpur, Kaikamba, Mangalore", "Fr. Mathew", "+91 94480 33221", "contact@snehasadan.org", 140, json.dumps(["Cooked Rice", "Dal", "Vegetables", "Milk"]))
        ]

        for ngo in mangalore_ngos:
            cursor.execute("SELECT id FROM ngos WHERE name = %s", (ngo[0],))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO ngos (name, ngo_type, need_level, latitude, longitude, address, manager, phone, email, capacity_persons, requested_items)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, ngo)
                print(f"Added Mangalore NGO: {ngo[0]}")

        conn.commit()

        # 5. List all active NGOs
        cursor.execute("SELECT id, name, address, manager FROM ngos ORDER BY id ASC")
        rows = cursor.fetchall()
        print("\nAll Active Partner NGOs (MANGALORE ONLY):")
        for r in rows:
            print(f"ID {r['id']}: {r['name']} | Address: {r['address']}")

if __name__ == "__main__":
    clean_bengaluru_ngos()
