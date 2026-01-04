import os
import mysql.connector

# ---------- CONFIG ----------
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "root",
    "database": "bandl",
    "port": 3306
}

TABLE_NAME = "labels"

IMAGE_FOLDER = r"C:\Users\ckrit\bnl\mb_images"
DB_IMAGE_BASE_PATH = "mb_images"

IMAGE_EXT = ".png"
PAGES_PER_BOOK = 16  # ⚠️ CHANGE IF NEEDED
# ----------------------------

def column_exists(cursor, table, column):
    cursor.execute("""
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
    """, (table, column))
    return cursor.fetchone()['COUNT(*)'] > 0


def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    # 1️⃣ Add column if needed
    if not column_exists(cursor, TABLE_NAME, "image_path"):
        cursor.execute(
            f"ALTER TABLE {TABLE_NAME} ADD COLUMN image_path VARCHAR(255)"
        )
        conn.commit()
        print("Added image_path column")

    # 2️⃣ Fetch rows without image_path, ORDERED by book and page
    cursor.execute(f"""
        SELECT id, book, page
        FROM {TABLE_NAME}
        WHERE image_path IS NULL OR image_path = ''
        ORDER BY book, page, id
    """)
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} rows to process")

    # 3️⃣ Build a map of all available images: {global_page: [match1, match2, ...]}
    image_map = {}
    
    for filename in os.listdir(IMAGE_FOLDER):
        if not filename.endswith(IMAGE_EXT):
            continue
        
        # Parse: match123_page17.png
        try:
            parts = filename.replace(IMAGE_EXT, "").split("_page_")
            page_num = int(parts[0].replace("match", ""))
            match_num = int(parts[1])
            
            if page_num not in image_map:
                image_map[page_num] = []
            image_map[page_num].append((match_num, filename))
        except (ValueError, IndexError):
            print(f"Skipping malformed filename: {filename}")
            continue
    
    # Sort matches within each page
    for page_num in image_map:
        image_map[page_num].sort()  # Sort by match_num
    
    print(f"Found images for {len(image_map)} pages")

    # 4️⃣ Match rows to images
    updated = 0
    page_counters = {}  # Track which match we're on for each page
    
    for row in rows:
        label_id = row["id"]
        book = row["book"]
        page = row["page"]

        # Compute global page number
        global_page = (book - 1) * PAGES_PER_BOOK + page
        
        # Check if we have images for this page
        if global_page not in image_map:
            print(f"No images found for book={book}, page={page} (global_page={global_page})")
            continue
        
        # Get the next available match for this page
        if global_page not in page_counters:
            page_counters[global_page] = 0
        
        match_index = page_counters[global_page]
        
        if match_index >= len(image_map[global_page]):
            print(f"No more images for book={book}, page={page} (global_page={global_page}) - already used {match_index} images")
            continue
        
        # Get the image filename
        _, image_filename = image_map[global_page][match_index]
        
        # Update database
        cursor.execute(
            f"""
            UPDATE {TABLE_NAME}
            SET image_path = %s
            WHERE id = %s
            """,
            (os.path.join(DB_IMAGE_BASE_PATH, image_filename), label_id)
        )
        
        updated += 1
        page_counters[global_page] += 1
        
        if updated % 100 == 0:
            print(f"Updated {updated} rows...")

    conn.commit()
    print(f"✅ Successfully updated {updated} rows")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()