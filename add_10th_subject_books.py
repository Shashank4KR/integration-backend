import asyncio
import uuid
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

CATEGORIES = [
    {"name": "Mathematics", "desc": "Class 10 CBSE & State Board Mathematics text and reference books"},
    {"name": "Science", "desc": "Class 10 Physics, Chemistry, and Biology curriculum textbooks and laboratory manuals"},
    {"name": "Social Science", "desc": "Class 10 History, Geography, Political Science, and Economics course material"},
    {"name": "English", "desc": "Class 10 English Literature, Supplementary Readers, and Grammar textbooks"},
    {"name": "Hindi", "desc": "Class 10 Hindi Course A & B textbooks and grammar guides"},
    {"name": "Kannada", "desc": "Class 10 Regional Language Karnataka & CBSE Kannada literature textbooks"},
    {"name": "Physical Education", "desc": "Class 10 Health, Fitness, Sports Science, and Yoga textbooks"},
]

BOOKS = [
    # 1. MATHEMATICS (Code: MATH104)
    {
        "category": "Mathematics",
        "title": "NCERT Mathematics for Class X",
        "subtitle": "Standard Curriculum Textbook for CBSE Class 10",
        "author": "NCERT Editorial Board",
        "publisher": "National Council of Educational Research and Training",
        "isbn": "978-81-7450-634-4",
        "edition": "Revised 2026 Edition",
        "language": "English",
        "rack_number": "Rack M-1",
        "shelf_number": "Shelf A",
        "total_copies": 25,
        "available_copies": 25,
        "description": "Standard official CBSE textbook for Class 10 covering Real Numbers, Polynomials, Linear Equations, Quadratic Equations, Triangles, Trigonometry, Statistics, and Probability."
    },
    {
        "category": "Mathematics",
        "title": "Mathematics for Class 10 (Secondary School)",
        "subtitle": "Comprehensive Theory, Solved Examples & Practice Problems",
        "author": "Dr. R. D. Sharma",
        "publisher": "Dhanpat Rai Publications",
        "isbn": "978-93-8318-218-4",
        "edition": "2026 Board Edition",
        "language": "English",
        "rack_number": "Rack M-1",
        "shelf_number": "Shelf B",
        "total_copies": 15,
        "available_copies": 15,
        "description": "In-depth reference guide with advanced conceptual problems, board exam patterns, and high-order thinking skill (HOTS) questions for Class 10 CBSE."
    },
    {
        "category": "Mathematics",
        "title": "Secondary School Mathematics for Class 10",
        "subtitle": "Standard Practice & Revision Guide",
        "author": "R. S. Aggarwal & Vikas Aggarwal",
        "publisher": "Bharati Bhawan",
        "isbn": "978-93-5027-009-7",
        "edition": "Latest 2026 Edition",
        "language": "English",
        "rack_number": "Rack M-1",
        "shelf_number": "Shelf C",
        "total_copies": 12,
        "available_copies": 12,
        "description": "Classic textbook with step-by-step solutions, unit-wise practice tests, and standard board model questions for Class 10."
    },

    # 2. SCIENCE (Code: SCI105)
    {
        "category": "Science",
        "title": "NCERT Science Textbook for Class X",
        "subtitle": "Comprehensive Physics, Chemistry & Biology",
        "author": "NCERT Science Panel",
        "publisher": "NCERT",
        "isbn": "978-81-7450-649-8",
        "edition": "2026 Academic Edition",
        "language": "English",
        "rack_number": "Rack S-2",
        "shelf_number": "Shelf A",
        "total_copies": 30,
        "available_copies": 30,
        "description": "Prescribed textbook for Class 10 CBSE covering Chemical Reactions, Acids & Bases, Life Processes, Control & Coordination, Light, Electricity, and Magnetic Effects."
    },
    {
        "category": "Science",
        "title": "Science for Tenth Class (Part 1): Physics",
        "subtitle": "Light, Electricity, Magnetic Effects & Sources of Energy",
        "author": "Lakhmir Singh & Manjit Kaur",
        "publisher": "S. Chand Publishing",
        "isbn": "978-93-5283-789-2",
        "edition": "Multi-Color Revised Edition",
        "language": "English",
        "rack_number": "Rack S-2",
        "shelf_number": "Shelf B",
        "total_copies": 18,
        "available_copies": 18,
        "description": "Illustrated conceptual physics guide with ray diagrams, circuit problems, multiple choice questions, and board exam solutions."
    },
    {
        "category": "Science",
        "title": "Science for Tenth Class (Part 2): Chemistry",
        "subtitle": "Chemical Reactions, Metals, Carbon Compounds & Periodic Trends",
        "author": "Lakhmir Singh & Manjit Kaur",
        "publisher": "S. Chand Publishing",
        "isbn": "978-93-5283-790-8",
        "edition": "Multi-Color Revised Edition",
        "language": "English",
        "rack_number": "Rack S-2",
        "shelf_number": "Shelf C",
        "total_copies": 18,
        "available_copies": 18,
        "description": "Detailed chemistry study book with chemical equation balance worksheets, lab experiments, and board questions for Class 10."
    },
    {
        "category": "Science",
        "title": "Science for Tenth Class (Part 3): Biology",
        "subtitle": "Life Processes, Reproduction, Heredity & Environment",
        "author": "Lakhmir Singh & Manjit Kaur",
        "publisher": "S. Chand Publishing",
        "isbn": "978-93-5283-791-5",
        "edition": "Multi-Color Revised Edition",
        "language": "English",
        "rack_number": "Rack S-2",
        "shelf_number": "Shelf D",
        "total_copies": 18,
        "available_copies": 18,
        "description": "Essential Class 10 Biology book with full-colour anatomical illustrations, genetics flowcharts, and practical question bank."
    },

    # 3. SOCIAL SCIENCE (Code: SOC106)
    {
        "category": "Social Science",
        "title": "India and the Contemporary World - II",
        "subtitle": "Class 10 Textbook in History",
        "author": "NCERT Social Sciences Group",
        "publisher": "NCERT",
        "isbn": "978-81-7450-707-5",
        "edition": "National Curriculum Edition",
        "language": "English",
        "rack_number": "Rack SS-3",
        "shelf_number": "Shelf A",
        "total_copies": 20,
        "available_copies": 20,
        "description": "Covers Rise of Nationalism in Europe, Nationalism in India, Making of a Global World, and Print Culture and the Modern World."
    },
    {
        "category": "Social Science",
        "title": "Contemporary India - II",
        "subtitle": "Class 10 Textbook in Geography",
        "author": "NCERT Social Sciences Group",
        "publisher": "NCERT",
        "isbn": "978-81-7450-644-3",
        "edition": "National Curriculum Edition",
        "language": "English",
        "rack_number": "Rack SS-3",
        "shelf_number": "Shelf B",
        "total_copies": 20,
        "available_copies": 20,
        "description": "Comprehensive geography book covering Resources & Development, Forest & Wildlife, Water Resources, Agriculture, Minerals, and Manufacturing Industries."
    },
    {
        "category": "Social Science",
        "title": "Democratic Politics - II",
        "subtitle": "Class 10 Textbook in Political Science (Civics)",
        "author": "NCERT Social Sciences Group",
        "publisher": "NCERT",
        "isbn": "978-81-7450-711-2",
        "edition": "National Curriculum Edition",
        "language": "English",
        "rack_number": "Rack SS-3",
        "shelf_number": "Shelf C",
        "total_copies": 20,
        "available_copies": 20,
        "description": "Prescribed textbook on Power Sharing, Federalism, Gender, Religion & Caste, and Political Parties for Class 10."
    },
    {
        "category": "Social Science",
        "title": "Understanding Economic Development",
        "subtitle": "Class 10 Textbook in Economics",
        "author": "NCERT Social Sciences Group",
        "publisher": "NCERT",
        "isbn": "978-81-7450-655-9",
        "edition": "National Curriculum Edition",
        "language": "English",
        "rack_number": "Rack SS-3",
        "shelf_number": "Shelf D",
        "total_copies": 20,
        "available_copies": 20,
        "description": "Focuses on Development metrics, Sectors of the Indian Economy, Money & Credit, Globalization, and Consumer Rights."
    },

    # 4. ENGLISH (Code: ENG101)
    {
        "category": "English",
        "title": "First Flight - Textbook in English for Class X",
        "subtitle": "Core Prose & Poetry Reader for CBSE Class 10",
        "author": "NCERT Department of Languages",
        "publisher": "NCERT",
        "isbn": "978-81-7450-658-0",
        "edition": "NCERT Standard Edition",
        "language": "English",
        "rack_number": "Rack E-4",
        "shelf_number": "Shelf A",
        "total_copies": 25,
        "available_copies": 25,
        "description": "Prescribed English Literature textbook containing A Letter to God, Nelson Mandela, Two Stories about Flying, From the Diary of Anne Frank, The Trees, and Fog."
    },
    {
        "category": "English",
        "title": "Footprints Without Feet",
        "subtitle": "Supplementary Reader in English for Class X",
        "author": "NCERT Department of Languages",
        "publisher": "NCERT",
        "isbn": "978-81-7450-709-9",
        "edition": "NCERT Standard Edition",
        "language": "English",
        "rack_number": "Rack E-4",
        "shelf_number": "Shelf B",
        "total_copies": 22,
        "available_copies": 22,
        "description": "Supplementary English prose anthology including A Triumph of Surgery, The Thief's Story, The Midnight Visitor, A Question of Trust, and The Necklace."
    },
    {
        "category": "English",
        "title": "High School English Grammar and Composition",
        "subtitle": "Standard Reference on Functional Grammar, Writing Skills & Syntax",
        "author": "P. C. Wren & H. Martin (Revised by N.D.V. Prasada Rao)",
        "publisher": "S. Chand Publishing",
        "isbn": "978-93-5253-014-4",
        "edition": "Centenary Illustrated Edition",
        "language": "English",
        "rack_number": "Rack E-4",
        "shelf_number": "Shelf C",
        "total_copies": 15,
        "available_copies": 15,
        "description": "Indispensable grammar workbook for high school students covering Active-Passive Voice, Reported Speech, Clause Analysis, Formal Letter Writing, and Analytical Paragraphs."
    },

    # 5. HINDI (Code: HIN103)
    {
        "category": "Hindi",
        "title": "Kshitij (Part 2) - Class 10 Hindi Course A",
        "subtitle": "Main Prose and Poetry Coursebook",
        "author": "NCERT Hindi Department",
        "publisher": "NCERT",
        "isbn": "978-81-7450-662-7",
        "edition": "Standard Board Edition",
        "language": "Hindi",
        "rack_number": "Rack H-5",
        "shelf_number": "Shelf A",
        "total_copies": 20,
        "available_copies": 20,
        "description": "Standard Class 10 Hindi Course A textbook featuring classics by Surdas, Tulsidas, Jaishankar Prasad, Swayam Prakash, and Ramvriksh Benipuri."
    },
    {
        "category": "Hindi",
        "title": "Kritika (Part 2) - Class 10 Hindi Supplementary",
        "subtitle": "Supplementary Hindi Prose Collection",
        "author": "NCERT Hindi Department",
        "publisher": "NCERT",
        "isbn": "978-81-7450-716-7",
        "edition": "Standard Board Edition",
        "language": "Hindi",
        "rack_number": "Rack H-5",
        "shelf_number": "Shelf B",
        "total_copies": 18,
        "available_copies": 18,
        "description": "Engaging Hindi supplementary reader containing Mata ka Anchal, George Pancham ki Naak, and Sana Sana Hath Jodi."
    },
    {
        "category": "Hindi",
        "title": "Sparsh (Part 2) - Class 10 Hindi Course B",
        "subtitle": "Prose & Verse Textbook for Secondary Classes",
        "author": "NCERT Hindi Department",
        "publisher": "NCERT",
        "isbn": "978-81-7450-664-1",
        "edition": "Standard Board Edition",
        "language": "Hindi",
        "rack_number": "Rack H-5",
        "shelf_number": "Shelf C",
        "total_copies": 15,
        "available_copies": 15,
        "description": "CBSE Hindi Course B textbook including Kabir's Sakhi, Meera ke Pad, Bade Bhai Sahab by Premchand, and Diary ka Ek Panna."
    },

    # 6. KANNADA (Code: KAN102)
    {
        "category": "Kannada",
        "title": "Siri Kannada - Class 10 First Language Kannada",
        "subtitle": "Karnataka State & CBSE First Language Text",
        "author": "Karnataka Textbook Society (KTBS)",
        "publisher": "Government of Karnataka",
        "isbn": "978-81-9351-102-1",
        "edition": "Revised Curriculum Edition",
        "language": "Kannada",
        "rack_number": "Rack K-6",
        "shelf_number": "Shelf A",
        "total_copies": 20,
        "available_copies": 20,
        "description": "Prescribed textbook for 10th Standard Kannada language and literature, comprising classical Halegannada poetry, Vachana literature, and modern Nadageethe."
    },
    {
        "category": "Kannada",
        "title": "Sannakathegalu & Gadya Sangraha Class 10",
        "subtitle": "Kannada Supplementary Short Stories & Essays",
        "author": "KTBS Board of Kannada Studies",
        "publisher": "Karnataka Textbook Society",
        "isbn": "978-81-9351-103-8",
        "edition": "Annual Board Edition",
        "language": "Kannada",
        "rack_number": "Rack K-6",
        "shelf_number": "Shelf B",
        "total_copies": 15,
        "available_copies": 15,
        "description": "Supplementary Kannada prose collection featuring renowned works by Kuvempu, Bendre, and Masti Venkatesha Iyengar."
    },

    # 7. PHYSICAL EDUCATION (Code: PE107)
    {
        "category": "Physical Education",
        "title": "Health and Physical Education for Class X",
        "subtitle": "Comprehensive Guide on Yoga, Physical Fitness, First Aid & Sports Rules",
        "author": "Dr. V. K. Sharma",
        "publisher": "New Saraswati House",
        "isbn": "978-93-5272-187-0",
        "edition": "2026 Curriculum Edition",
        "language": "English",
        "rack_number": "Rack PE-7",
        "shelf_number": "Shelf A",
        "total_copies": 15,
        "available_copies": 15,
        "description": "Prescribed textbook for Class 10 Physical Education covering Athletics, Yoga Asanas, Team Sports rules (Football, Cricket, Basketball, Volleyball), and Nutrition."
    },
    {
        "category": "Physical Education",
        "title": "Yoga and Holistic Health for School Students",
        "subtitle": "Practical Asana, Pranayama & Stress Management Manual",
        "author": "NCERT Physical Education Cell",
        "publisher": "NCERT",
        "isbn": "978-81-7450-845-4",
        "edition": "National Health Framework Edition",
        "language": "English",
        "rack_number": "Rack PE-7",
        "shelf_number": "Shelf B",
        "total_copies": 12,
        "available_copies": 12,
        "description": "Illustrated guide for school students on daily Surya Namaskar, respiratory wellness, meditation techniques, and physical agility."
    }
]

async def seed_library():
    async with AsyncSessionLocal() as session:
        # 1. Fetch or create categories
        category_map = {}
        for cat in CATEGORIES:
            res = await session.execute(
                text("SELECT id FROM book_categories WHERE LOWER(category_name) = LOWER(:name)"),
                {"name": cat["name"]}
            )
            row = res.fetchone()
            if row:
                category_map[cat["name"]] = row[0]
            else:
                cat_id = uuid.uuid4()
                await session.execute(
                    text("""
                        INSERT INTO book_categories (id, category_name, description, status, created_at, updated_at)
                        VALUES (:id, :name, :desc, true, now(), now())
                    """),
                    {"id": cat_id, "name": cat["name"], "desc": cat["desc"]}
                )
                category_map[cat["name"]] = cat_id
                print(f"Created category: {cat['name']}")

        await session.commit()

        # 2. Insert books
        added_count = 0
        for book in BOOKS:
            cat_id = category_map.get(book["category"])
            if not cat_id:
                print(f"Skipping {book['title']} - category not found")
                continue

            # Check if ISBN already exists
            res = await session.execute(
                text("SELECT id FROM books WHERE isbn = :isbn"),
                {"isbn": book["isbn"]}
            )
            if res.fetchone():
                print(f"Book with ISBN {book['isbn']} already exists: {book['title']}")
                continue

            book_id = uuid.uuid4()
            await session.execute(
                text("""
                    INSERT INTO books (
                        id, isbn, title, subtitle, author, publisher, category_id,
                        edition, language, rack_number, shelf_number,
                        total_copies, available_copies, description, status, is_deleted,
                        created_at, updated_at
                    ) VALUES (
                        :id, :isbn, :title, :subtitle, :author, :publisher, :cat_id,
                        :edition, :language, :rack_number, :shelf_number,
                        :total_copies, :available_copies, :description, true, false,
                        now(), now()
                    )
                """),
                {
                    "id": book_id,
                    "isbn": book["isbn"],
                    "title": book["title"],
                    "subtitle": book.get("subtitle"),
                    "author": book["author"],
                    "publisher": book.get("publisher"),
                    "cat_id": cat_id,
                    "edition": book.get("edition"),
                    "language": book.get("language"),
                    "rack_number": book.get("rack_number"),
                    "shelf_number": book.get("shelf_number"),
                    "total_copies": book["total_copies"],
                    "available_copies": book["available_copies"],
                    "description": book.get("description"),
                }
            )
            added_count += 1
            print(f"Added book: {book['title']} ({book['category']})")

        await session.commit()
        print(f"\nSuccessfully seeded {added_count} Class 10 curriculum books into Nomera Library!")

if __name__ == "__main__":
    asyncio.run(seed_library())
