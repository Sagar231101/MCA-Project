from flask import Flask, render_template, request, flash, redirect, url_for, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from datetime import datetime, date
import sys # Add this import at the top of your app.py file if it's not there


app = Flask(__name__)

# --- Configuration ---
app.secret_key = '67da3f9ca45501e4ec09eb49f3fbabf85850cf09b374992e9652cb8182f13c74' # Keep this secret!

# IMPORTANT: Replace with your actual MySQL database credentials and host!
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Sagar@2311', # Replace with your MySQL root password
    'database': 'ai_tour_db'
}

# Placeholder for social links (ensure this matches your template's requirements)
social_links = {
    'twitter': '#', # Replace with actual Twitter URL
    'facebook': '#', # Replace with actual Facebook URL
    'instagram': '#', # Replace with actual Instagram URL
    'linkedin': '#', # Replace with actual LinkedIn URL
    'youtube': '#' # Added YouTube as seen in team member data
}


# --- Database Connection Management ---
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            return conn
        else:
            print("Error: MySQL connection could not be established.")
            return None
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        # Consider specific error handling for Access Denied (password/user issue) or Unknown Database
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            print("Error: Access denied for user. Check your MySQL username and password in DB_CONFIG.")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            print(f"Error: Database '{DB_CONFIG['database']}' does not exist. Please create it.")
        return None

def close_db_connection(conn):
    if conn and conn.is_connected():
        conn.close()

# --- Initial Database Setup and Population ---
# This function is for initial setup (creating tables) and populating dummy data.
# It should typically be run once, e.g., via a separate script or Flask CLI command,
# not on every app startup, especially db.create_tables().
def setup_database():
    conn = get_db_connection()
    if not conn:
        print("Could not establish DB connection for setup. Exiting setup.")
        return

    cursor = conn.cursor()

    # Function to check if a table exists
    def table_exists(table_name_check):
        try:
            cursor.execute(f"SHOW TABLES LIKE '{table_name_check}'")
            return cursor.fetchone() is not None
        except mysql.connector.Error as err:
            print(f"Error checking existence of table '{table_name_check}': {err}")
            return False

    # SQL commands for creating tables if they don't exist
    create_tables_sql = [
        """
        CREATE TABLE IF NOT EXISTS user (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS admin (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password_hash VARCHAR(511) NOT NULL, -- Increased length for modern hashes
            email VARCHAR(120) UNIQUE NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS package (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            location VARCHAR(100) NOT NULL,
            price VARCHAR(50) NOT NULL,
            days VARCHAR(50) NOT NULL,
            -- persons VARCHAR(50) NOT NULL, -- Removed persons column
            img VARCHAR(100) NOT NULL,
            description TEXT,
            discount_percentage INT DEFAULT 0
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS destination (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            description TEXT,
            image VARCHAR(100) NOT NULL,
            discount_percentage INT DEFAULT 0
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS booking (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            package_id INT NOT NULL,
            booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            travel_date DATE NOT NULL,
            num_adults INT NOT NULL,
            num_children INT NOT NULL,
            total_price FLOAT NOT NULL,
            status VARCHAR(50) DEFAULT 'Pending',
            special_request TEXT,
            FOREIGN KEY (user_id) REFERENCES user(id),
            FOREIGN KEY (package_id) REFERENCES package(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS custom_booking (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            destination_id INT,
            destination_name VARCHAR(200),
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            preferences TEXT,
            num_travelers INT DEFAULT 1,
            budget VARCHAR(100),
            status VARCHAR(50) DEFAULT 'Pending',
            FOREIGN KEY (user_id) REFERENCES user(id),
            FOREIGN KEY (destination_id) REFERENCES destination(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            rating INT NOT NULL,
            comment TEXT NOT NULL,
            feedback_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS transport (
            id INT AUTO_INCREMENT PRIMARY KEY,
            type VARCHAR(50) NOT NULL,
            name VARCHAR(100) NOT NULL,
            capacity INT,
            price_per_person FLOAT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS itinerary (
            id INT AUTO_INCREMENT PRIMARY KEY,
            package_id INT NOT NULL,
            day_number INT NOT NULL,
            title VARCHAR(200) NOT NULL,
            description TEXT NOT NULL,
            FOREIGN KEY (package_id) REFERENCES package(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS team_member (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            designation VARCHAR(100) NOT NULL,
            image VARCHAR(100) NOT NULL,
            twitter_url VARCHAR(255),
            facebook_url VARCHAR(255),
            linkedin_url VARCHAR(255),
            instagram_url VARCHAR(255),
            youtube_url VARCHAR(255)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS testimonial (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            location VARCHAR(100) NOT NULL,
            image VARCHAR(100) NOT NULL,
            quote TEXT NOT NULL
        )
        """
    ]

    for sql_command in create_tables_sql:
        try:
            cursor.execute(sql_command)
            conn.commit()
            print(f"Executed table creation: {sql_command.split(' ')[5]} table")
        except mysql.connector.Error as err:
            print(f"Error creating table: {err} - SQL: {sql_command}")

    print("\nChecking tables for initial data population...")

    # Helper to check if a table is empty
    def is_table_empty(table_name_check, cur):
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table_name_check}")
            count = cur.fetchone()[0]
            return count == 0
        except mysql.connector.Error as err:
            print(f"Error checking if table '{table_name_check}' is empty: {err}")
            return False # Assume not empty or cannot determine

    # Users
    if table_exists('user') and is_table_empty('user', cursor):
        print("Populating 'user' table...")
        admin_pass = generate_password_hash('adminpass')
        user_pass = generate_password_hash('testpass')
        cursor.execute("INSERT INTO user (username, email, password_hash, is_admin) VALUES (%s, %s, %s, %s)",
                       ('admin', 'admin@globetour.com', admin_pass, True))
        cursor.execute("INSERT INTO user (username, email, password_hash, is_admin) VALUES (%s, %s, %s, %s)",
                       ('testuser', 'test@example.com', user_pass, False))
        conn.commit()
        print("Added default admin and test user.")
    elif not table_exists('user'):
        print("Table 'user' was not created. Skipping population.")
    else:
        print("Table 'user' already contains data. Skipping population.")


    # Admin (if separate Admin table is desired)
    if table_exists('admin') and is_table_empty('admin', cursor):
        print("Populating 'admin' table...")
        superadmin_pass = generate_password_hash('superadminpass')
        cursor.execute("INSERT INTO admin (username, password_hash, email) VALUES (%s, %s, %s)",
                       ('superadmin', superadmin_pass, 'superadmin@globetour.com'))
        conn.commit()
        print("Added default superadmin.")
    elif not table_exists('admin'):
        print("Table 'admin' was not created. Skipping population.")
    else:
        print("Table 'admin' already contains data. Skipping population.")


    # Packages
    if table_exists('package') and is_table_empty('package', cursor):
        print("Populating 'package' table...")
        packages_to_insert = [
            # Indian Packages
            ('Golden Triangle India', 'North India', '₹21,000', '5 days', 'golden_triangle.jpg', 'Classic tour of Delhi, Agra, and Jaipur – India\'s iconic cultural circuit.', 10),
            ('Rajasthan Royal Odyssey', 'Rajasthan', '₹28,000', '7 days', 'rajasthan_royal.jpg', 'Experience the majestic forts, palaces, and deserts of Rajasthan (Udaipur, Jodhpur, Jaisalmer).', 15),
            ('Himalayan Heights', 'Himachal Pradesh', '₹22,000', '6 days', 'himalayan_heights.jpg', 'Explore the scenic beauty of Shimla and Manali with stunning mountain views.', 12),
            ('Kashmir Valley Paradise', 'Kashmir', '₹25,000', '5 days', 'kashmir_valley.jpg', 'Discover the serene lakes, lush valleys, and snow-capped peaks of Kashmir.', 8),
            ('Leh-Ladakh Adventure', 'Ladakh', '₹32,000', '7 days', 'lehladakh_adventure.jpg', 'A thrilling journey through high-altitude passes, ancient monasteries, and barren landscapes.', 20),
            ('Rishikesh Yoga & Rafting', 'Uttarakhand', '₹14,000', '4 days', 'rishikesh_yoga.jpg', 'Combine spiritual tranquility with exciting river rafting in the Yoga Capital of the World.', 5),
            ('Kerala Backwater & Beach', 'Kerala', '₹19,000', '5 days', 'kerala_backwater.jpg', 'Relax on houseboats, enjoy Ayurvedic treatments, and explore the serene beaches of Kerala.', 10),
            ('Karnataka Heritage Trail', 'Karnataka', '₹17,000', '4 days', 'karnataka_heritage.jpg', 'Visit the historical sites of Mysore and Hampi, showcasing ancient architecture and rich heritage.', 7),
            ('Tamil Nadu Temple Tour', 'Tamil Nadu', '₹16,500', '5 days', 'tamilnadu_temple.jpg', 'A spiritual journey through the magnificent temples of Madurai, Rameshwaram, and Kanyakumari.', 9),
            ('Darjeeling & Sikkim Serenity', 'East India', '₹23,000', '6 days', 'darjeeling_sikkim.jpg', 'Enjoy tea gardens, panoramic Himalayan views, and vibrant Buddhist monasteries.', 11),
            ('Mumbai Metropolitan Marvel', 'Maharashtra', '₹16,000', '3 days', 'mumbai_marvel.jpg', 'Experience the bustling city life, iconic landmarks, and Bollywood glamour of Mumbai.', 6),
            ('Goa Fun & Sun', 'Goa', '₹15,000', '4 days', 'goa_fun.jpg', 'Relax on beautiful beaches, enjoy vibrant nightlife, and indulge in water sports.', 14),
            ('North East Wonders', 'North East India', '₹29,000', '7 days', 'northeast_india.jpg', 'Explore the untouched beauty of Assam and Meghalaya, with waterfalls, living root bridges, and unique cultures.', 18),
            ('Andaman Island Paradise', 'Andaman & Nicobar', '₹38,000', '6 days', 'andaman_island.jpg', 'Dive into crystal-clear waters, explore coral reefs, and relax on pristine beaches.', 17),
            ('Spiritual Varanasi', 'Uttar Pradesh', '₹11,000', '3 days', 'varanasi_spiritual.jpg', 'A soulful journey to the ancient city of Varanasi, witnessing sacred rituals and historical ghats.', 4),
            ('Wildlife Safari Ranthambore', 'Rajasthan', '₹19,000', '3 days', 'ranthambore.jpg', 'An thrilling wildlife safari in Ranthambore National Park, famous for its tigers.', 0),

            # International Packages
            ('Parisian Romance', 'France', '₹75,000', '6 days', 'paris_romance.jpg', 'Experience the magic of Paris with iconic landmarks, exquisite cuisine, and romantic strolls.', 20),
            ('Rome Ancient Empire', 'Italy', '₹70,000', '5 days', 'rome_ancient.jpg', 'Journey back in time amidst ancient ruins, magnificent art, and vibrant Italian culture.', 18),
            ('Swiss Alps Dream', 'Switzerland', '₹85,000', '7 days', 'swiss_alps.jpg', 'Breathtaking mountain landscapes, charming villages, and alpine adventures in Switzerland.', 25),
            ('London City Explorer', 'UK', '₹72,000', '5 days', 'london_explorer.jpg', 'Discover historical landmarks, vibrant neighborhoods, and diverse culture in the heart of London.', 16),
            ('Greek Island Hopping', 'Greece', '₹95,000', '8 days', 'greece_islands.jpg', 'Sail through the Aegean Sea, exploring the stunning islands of Santorini and Mykonos.', 28),
            ('Tokyo Modern & Tradition', 'Japan', '₹90,000', '7 days', 'tokyo_modern.jpg', 'Experience the unique blend of ancient traditions and futuristic technology in Tokyo.', 22),
            ('Bali Serenity Retreat', 'Indonesia', '₹68,000', '6 days', 'bali_retreat.jpg', 'Find peace amidst lush rice paddies, spiritual temples, and beautiful beaches in Bali.', 15),
            ('Thailand Beach & City', 'Thailand', '₹60,000', '7 days', 'thailand_beachcity.jpg', 'Enjoy the bustling city life of Bangkok and the pristine beaches of Phuket.', 12),
            ('Singapore Urban Adventure', 'Singapore', '₹65,000', '5 days', 'singapore_urban.jpg', 'Explore Gardens by the Bay, Sentosa Island, and vibrant culinary scene in Singapore.', 10),
            ('Maldives Luxury Getaway (Intl.)', 'Maldives', '₹120,000', '4 days', 'maldives_luxury.jpg', 'Indulge in unparalleled luxury with overwater bungalows and turquoise lagoons in the Maldives.', 30),
            ('Dubai Desert & Skyline (Intl.)', 'UAE', '₹68,000', '5 days', 'dubai_desert.jpg', 'Experience a thrilling desert safari, magnificent skyscrapers, and luxurious shopping in Dubai.', 19),
            ('Egypt Pyramids & Nile (Intl.)', 'Egypt', '₹80,000', '8 days', 'egypt_pyramids.jpg', 'Explore ancient wonders like the Pyramids of Giza and a relaxing Nile River cruise.', 21),
            ('Canadian Rockies (Intl.)', 'Canada', '₹110,000', '8 days', 'canada_rockies.jpg', 'Discover breathtaking mountains, turquoise lakes, and wildlife in Banff and Jasper National Parks.', 25),
            ('Machu Picchu Trek (Intl.)', 'Peru', '₹130,000', '9 days', 'machu_picchu.jpg', 'Embark on an epic journey to the ancient Inca city of Machu Picchu.', 20),
            ('African Safari (Intl.)', 'Kenya', '₹150,000', '7 days', 'africa_safari.jpg', 'Witness the incredible wildlife of the Maasai Mara on a thrilling safari adventure.', 15),
        ]
        # Updated INSERT statement to remove 'persons' column
        cursor.executemany("INSERT INTO package (name,location,price,days,img,description,discount_percentage)VALUES (%s,%s,%s,%s,%s,%s,%s)",packages_to_insert)
        conn.commit()
        print(f"Added {cursor.rowcount} packages.")

        # --- Dynamic Itinerary Population for ALL Packages ---
        # This section dynamically generates and populates itineraries.
        # If you prefer manual insertion, you will bypass this.
        print("\nAttempting to populate itineraries for all packages dynamically...")
        
        # Crucial: TRUNCATE itinerary table to ensure fresh population with new data
        try:
            cursor.execute("TRUNCATE TABLE itinerary;")
            conn.commit()
            print("Truncated 'itinerary' table for fresh population.")
        except mysql.connector.Error as err:
            print(f"Error truncating 'itinerary' table: {err}. Itineraries might be duplicated or outdated if not empty.")
        
        all_itineraries_to_insert = []
        # Fetch all packages (including newly inserted ones with their IDs)
        all_packages_from_db = fetch_all("SELECT id, name, location, days FROM package")

        for p in all_packages_from_db:
            package_id = p['id']
            package_name = p['name']
            package_location = p['location']
            num_days_str = p['days'].split(' ')[0] 
            try:
                num_days = int(num_days_str)
            except ValueError:
                num_days = 3 # Default to 3 days if format is unexpected

            # Logic to generate itinerary based on number of days and package name/location
            if num_days == 1:
                all_itineraries_to_insert.append((package_id, 1, f'Arrival & {package_name} Highlights', f'Arrive at {package_location}, check-in and explore local highlights.'))
            elif num_days == 2:
                all_itineraries_to_insert.append((package_id, 1, f'Arrival & {package_name} Exploration', f'Arrive at {package_location}, transfer to hotel. Enjoy a half-day city/area tour.'))
                itinerary_title_2 = 'Main Sightseeing & Departure'
                itinerary_desc_2 = f'Full day exploring main attractions of {package_name}. Evening departure from {package_location}.'
                all_itineraries_to_insert.append((package_id, 2, itinerary_title_2, itinerary_desc_2))
            elif num_days == 3:
                all_itineraries_to_insert.append((package_id, 1, f'Day 1: Arrival & Local Charm of {package_location}', f'Arrive at {package_location}, check-in. Explore local markets or nearby sights.'))
                all_itineraries_to_insert.append((package_id, 2, f'Day 2: Full Day {package_name} Immersion', f'Enjoy a full day dedicated to the primary attractions and activities of {package_name}.'))
                all_itineraries_to_insert.append((package_id, 3, f'Day 3: Leisure & Departure from {package_location}', f'Morning at leisure or last-minute souvenir shopping. Transfer to airport/station for departure.'))
            else: # For 4 or more days
                all_itineraries_to_insert.append((package_id, 1, f'Day 1: Arrival in {package_location} & Welcome', f'Arrive at {package_location}, transfer to hotel. Enjoy a relaxed evening.'))
                all_itineraries_to_insert.append((package_id, 2, f'Day 2: Iconic {package_name} Exploration', f'Full day dedicated to exploring the most famous landmarks and sites of {package_name}.'))
                all_itineraries_to_insert.append((package_id, 3, f'Day 3: Cultural & Hidden Gems of {package_location}', f'Discover local culture, traditional cuisine, or visit lesser-known attractions.'))
                for day_num in range(4, num_days):
                    all_itineraries_to_insert.append((package_id, day_num, f'Day {day_num}: Extended Discovery', f'Continue with optional tours, adventure activities, or deeper exploration of {package_location} / {package_name}.'))
                all_itineraries_to_insert.append((package_id, num_days, f'Day {num_days}: Departure from {package_location}', f'Enjoy a final breakfast, check-out, and transfer for your onward journey.'))

        # Insert all generated itineraries
        cursor.executemany("INSERT INTO itinerary (package_id, day_number, title, description) VALUES (%s, %s, %s, %s)", all_itineraries_to_insert)
        conn.commit()
        print(f"Added {cursor.rowcount} itineraries for all packages.")

    elif not table_exists('itinerary'):
        print("Table 'itinerary' was not created. Skipping population (issue with table creation).")
    else:
        print("Table 'itinerary' already contains data. Skipping population (not empty and not truncated by setup).")


    # Destinations
    # Keep this section as it is from the previous full app.py update
    # This populates your destination pages.
    if table_exists('destination') and is_table_empty('destination', cursor):
        print("Populating 'destination' table...")
        destinations_to_insert = [
            ('Thailand', 'Land of smiles, ancient temples, and stunning beaches.', 'destination-1.jpg', 30),
            ('Malaysia', 'A blend of vibrant cities, colonial architecture, and beautiful islands.', 'destination-2.jpg', 25),
            ('Australia', 'Vast wilderness, unique wildlife, and iconic cityscapes.', 'destination-3.jpg', 35),
            ('Indonesia', 'Diverse archipelago with volcanic mountains, tropical beaches, and rich culture.', 'destination-4.jpg', 20),
            # New Indian Destinations
            ('Shimla', 'The Queen of Hills, known for its colonial architecture and scenic beauty in Himachal Pradesh.', 'shimla.jpg', 15),
            ('Udaipur', 'The City of Lakes, famous for its majestic palaces and serene lakes in Rajasthan.', 'udaipur.jpg', 10),
            ('Darjeeling', 'The Queen of the Hills in West Bengal, famous for its tea gardens and Himalayan views.', 'darjeeling.jpg', 12),
            ('Varanasi', 'The spiritual capital of India, known for its ghats and ancient temples along the Ganges.', 'varanasi.jpg', 8), 
            ('Mysore', 'The City of Palaces, rich in history and culture in Karnataka.', 'mysore.jpg', 10),
            ('Amritsar', 'Home to the Golden Temple, a spiritual and cultural hub in Punjab.', 'amritsar.jpg', 7),
            ('Coorg', 'The Scotland of India, known for its coffee plantations and lush landscapes in Karnataka.', 'coorg.jpg', 11),
            ('Ooty', 'A popular hill station in Tamil Nadu, famous for its botanical gardens and Nilgiri Mountain Railway.', 'ooty.jpg', 9),
            ('Hampi', 'A UNESCO World Heritage site, known for its ancient ruins and temples in Karnataka.', 'hampi.jpg', 13),
            ('Kolkata', 'The City of Joy, a cultural and intellectual hub with colonial architecture in West Bengal.', 'kolkata.jpg', 6),
            # New International Destinations
            ('Paris', 'The City of Love, famous for its iconic Eiffel Tower, art, and fashion in France.', 'paris.jpg', 20),
            ('Rome', 'The Eternal City, steeped in ancient history, iconic ruins, and vibrant culture in Italy.', 'rome.jpg', 18),
            ('Tokyo', 'A bustling metropolis blending traditional culture with futuristic technology in Japan.', 'tokyo.jpg', 22),
            ('New York City', 'The city that never sleeps, known for its iconic landmarks, diverse culture, and vibrant arts scene in USA.', 'nyc.jpg', 17),
            ('London', 'A global capital of finance, art, and culture, with historic landmarks and diverse neighborhoods in UK.', 'london.jpg', 19),
            ('Sydney', 'A vibrant coastal city known for its iconic Opera House, Harbour Bridge, and beautiful beaches in Australia.', 'sydney.jpg', 25),
            ('Cairo', 'The ancient capital of Egypt, home to the Pyramids of Giza and Sphinx.', 'cairo.jpg', 16),
            ('Santorini', 'A picturesque Greek island known for its stunning sunsets, white-washed villages, and volcanic landscapes.', 'santorini.jpg', 28),
            ('Bangkok', 'A vibrant city known for its ornate shrines, bustling street life, and rich cultural heritage in Thailand.', 'bangkok.jpg', 14),
            ('Amsterdam', 'Known for its artistic heritage, elaborate canal system, narrow houses, and cycling culture in Netherlands.', 'amsterdam.jpg', 15)
        ]
        cursor.executemany("INSERT INTO destination (name, description, image, discount_percentage) VALUES (%s, %s, %s, %s)", destinations_to_insert)
        conn.commit()
        print(f"Added {cursor.rowcount} destinations.")
    elif not table_exists('destination'):
        print("Table 'destination' was not created. Skipping population.")
    else:
        print("Table 'destination' already contains data. Skipping population.")


    # Team Members
    if table_exists('team_member') and is_table_empty('team_member', cursor):
        print("Populating 'team_member' table...")
        team_members_to_insert = [
            ('Sagar D Patil', 'Co-Founder', 'Sagar2..jpg', 'https://twitter.com/sagardpatil', 'https://facebook.com/sagardpatil', 'https://linkedin.com/in/sagardpatil', 'https://instagram.com/sagardpatil', None),
            ('Piyush Raj', 'Co-Founder', 'piyush blazzer.jpg', 'https://twitter.com/piyushraj', 'https://facebook.com/piyushraj', 'https://linkedin.com/in/piyushraj', 'https://instagram.com/piyushraj', None),
            ('Afsar Ali', 'CEO', 'Afsar Blazzer.jpg', 'https://twitter.com/afsarali', 'https://facebook.com/afsarali', 'https://linkedin.com/in/afsarali', 'https://instagram.com/afsarali', None),
            ('Deepu', 'Relationship Manager', 'team-4.jpg', 'https://twitter.com/deepu', 'https://facebook.com/deepu', 'https://linkedin.com/in/deepu', 'https://instagram.com/deepu', None),
        ]
        cursor.executemany("INSERT INTO team_member (name, designation, image, twitter_url, facebook_url, linkedin_url, instagram_url, youtube_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", team_members_to_insert)
        conn.commit()
        print(f"Added {cursor.rowcount} team members.")
    elif not table_exists('team_member'):
        print("Table 'team_member' was not created. Skipping population.")
    else:
        print("Table 'team_member' already contains data. Skipping population.")


    # Testimonials
    if table_exists('testimonial') and is_table_empty('testimonial', cursor):
        print("Populating 'testimonial' table...")
        testimonials_to_insert = [
            ('Sagar Patil', 'Maharashtra, India', 'testimonial-1.jpg', 'The trip was absolutely incredible! Every detail was perfect, and our guide made the experience truly unforgettable. Highly recommend!'),
            ('Piyush Raj', 'Maharashtra, India', 'testimonial-2.jpg', 'The booking process was so smooth, and the support team was always available to answer our questions. A truly stress-free vacation!'),
            ('Afsar Ali', 'New York, USA', 'testimonial-3.jpg', 'Our travel guide was fantastic, knowledgeable, and made the entire tour enjoyable. We saw so much much more than we ever could have on our own!'),
            ('Deepu', 'London, UK', 'testimonial-4.jpg', 'From start to finish, the service was impeccable. Every detail was handled with care, making our anniversary trip truly special.'),
        ]
        cursor.executemany("INSERT INTO testimonial (name, location, image, quote) VALUES (%s, %s, %s, %s)", testimonials_to_insert)
        conn.commit()
        print(f"Added {cursor.rowcount} testimonials.")
    elif not table_exists('testimonial'):
        print("Table 'testimonial' was not created. Skipping population.")
    else:
        print("Table 'testimonial' already contains data. Skipping population.")
    
    # Transport
    if table_exists('transport') and is_table_empty('transport', cursor):
        print("Populating 'transport' table...")
        transport_options = [
            ('Flight', 'Economy Class', 200, 15000.00),
            ('Flight', 'Business Class', 50, 35000.00),
            ('Bus', 'AC Sleeper', 30, 2500.00),
            ('Car Rental', 'Sedan', 4, 5000.00),
        ]
        cursor.executemany("INSERT INTO transport (type, name, capacity, price_per_person) VALUES (%s, %s, %s, %s)", transport_options)
        conn.commit()
        print(f"Added {cursor.rowcount} transport options.")
    elif not table_exists('transport'):
        print("Table 'transport' was not created. Skipping population.")
    else:
        print("Table 'transport' already contains data. Skipping population.")

    close_db_connection(conn)
    print("\nDatabase setup and population check complete.")


# --- Authentication Helper ---
def login_required(f):
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to be logged in to access this page.', 'warning')
            return redirect(url_for('user_login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__ # Preserve original function name for Flask
    return wrap

def admin_login_required(f):
    def wrap(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# --- Utility Functions to fetch data from DB and convert to dicts ---
def fetch_all(query, params=None):
    conn = get_db_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True) # Fetch rows as dictionaries
    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Database error in fetch_all: {err}")
        return []
    finally:
        close_db_connection(conn)

def fetch_one(query, params=None):
    conn = get_db_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        return cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Database error in fetch_one: {err}")
        return None
    finally:
        close_db_connection(conn)

def execute_query(query, params=None, fetch=False):
    conn = get_db_connection()
    if not conn: return None
    
    cursor = None # Initialize cursor to None
    try:
        cursor = conn.cursor(dictionary=True) # Always use dictionary=True for consistency in result access
        cursor.execute(query, params)
        
        if query.strip().upper().startswith("SELECT"):
            result = cursor.fetchall() # Fetch all results
            # Return the first row (as dict) or None if no rows
            # This handles cases like SELECT LAST_INSERT_ID()
            return result[0] if result and len(result) > 0 else None 
        else: # For INSERT, UPDATE, DELETE, etc.
            conn.commit() # Commit changes only for DML operations
            return True # Indicate successful execution for DML
    except mysql.connector.Error as err:
        print(f"Database error in execute_query: {err}")
        conn.rollback() # Rollback on error for DML
        return False # Indicate failure
    finally:
        if cursor: # Ensure cursor is closed if it was created
            cursor.close()
        close_db_connection(conn) # Close the connection


# --- Website Routes ---

@app.route('/')
def home():
    packages = fetch_all("SELECT * FROM package ORDER BY id LIMIT 3")
    team_members = fetch_all("SELECT * FROM team_member ORDER BY id LIMIT 4")
    testimonials = fetch_all("SELECT * FROM testimonial ORDER BY id")
    destinations = fetch_all("SELECT * FROM destination ORDER BY id LIMIT 4") # Still limited to 4 for homepage display
    return render_template('index.html', social=social_links, packages=packages,
                           team_members=team_members, testimonials=testimonials, destinations=destinations)

@app.route('/about')
def about():
    return render_template('about.html', social=social_links)

@app.route('/service')
def services():
    return render_template('service.html')

@app.route('/package')
def packages_page():
    # Get the 'country' query parameter from the URL (e.g., /package?country=Thailand)
    search_country = request.args.get('country', '').strip()
    
    query = "SELECT * FROM package"
    params = []

    if search_country:
        # Filter packages by matching search_term in either 'name' or 'location'
        query += " WHERE LOWER(location) LIKE %s OR LOWER(name) LIKE %s"
        params.append(f'%{search_country.lower()}%')
        params.append(f'%{search_country.lower()}%')
    
    query += " ORDER BY id" # Always order the packages

    packages = fetch_all(query, tuple(params) if params else None)
    
    # You might want to flash a message if no packages are found for the search
    if search_country and not packages:
        flash(f"No packages found for '{search_country}'.", 'info')
    
    return render_template('package.html', packages=packages, search_country=search_country)


@app.route('/booking', methods=['GET', 'POST'])
@login_required
def booking():
    print("\n--- STEP 1: AT BOOKING PAGE ---")
    print(f"Session before processing: {session}")

    packages = fetch_all("SELECT id, name, location, price FROM package ORDER BY name")
    preselect_package_id = request.args.get('preselect_id', type=int)
    preselected_package = None
    if preselect_package_id:
        preselected_package = fetch_one("SELECT * FROM package WHERE id = %s", (preselect_package_id,))

    if request.method == 'POST':
        user_id = session.get('user_id')
        package_id = request.form.get('package_id', type=int)
        travel_date_str = request.form.get('travel_date')
        num_adults = request.form.get('num_adults', type=int, default=1)
        num_children = request.form.get('num_children', type=int, default=0)
        special_request = request.form.get('special_request')

        if not package_id or not travel_date_str or num_adults <= 0:
            flash('Please select a package, travel date, and at least one adult.', 'danger')
            return redirect(url_for('booking', preselect_id=package_id))

        package_details = fetch_one("SELECT id, name, price FROM package WHERE id = %s", (package_id,))
        base_price_raw = package_details['price'].replace('₹', '').replace(',', '')
        base_price = float(base_price_raw)
        total_price = (base_price * num_adults) + (base_price * 0.5 * num_children)

        session['temp_booking'] = {
            'package_id': package_id,
            'package_name': package_details['name'],
            'travel_date': travel_date_str,
            'num_adults': num_adults,
            'num_children': num_children,
            'total_price': total_price,
            'special_request': special_request,
            'user_id': user_id
        }
        session.modified = True
        print(f"Session after adding booking details: {session}")
        return redirect(url_for('add_passengers'))

    return render_template('booking.html', packages=packages, preselected_package=preselected_package)

@app.route('/add-passengers', methods=['GET', 'POST'])
@login_required
def add_passengers():
    print("\n--- STEP 2: AT ADD PASSENGERS PAGE ---")
    print(f"Session on arrival: {session}")

    temp_booking = session.get('temp_booking')
    if not temp_booking:
        flash('Your booking session has expired. Please start again.', 'warning')
        return redirect(url_for('booking'))

    total_passengers = temp_booking['num_adults'] + temp_booking['num_children']

    if request.method == 'POST':
        passengers = []
        try:
            for i in range(1, total_passengers + 1):
                passenger = {
                    'name': request.form[f'name_{i}'],
                    'age': int(request.form[f'age_{i}']),
                    'gender': request.form[f'gender_{i}'],
                    'id_proof_type': request.form[f'id_proof_type_{i}'],
                    'id_proof_number': request.form[f'id_proof_number_{i}']
                }
                passengers.append(passenger)
        except (KeyError, ValueError):
            flash('Please fill out all details for every passenger.', 'danger')
            return render_template('add_passengers.html', booking=temp_booking, total_passengers=total_passengers)

        session['temp_passengers'] = passengers
        session.modified = True
        print(f"Session after adding passenger details: {session}")
        # Let's also check the size of the session cookie
        session_cookie = str(session)
        print(f"Estimated session size: {sys.getsizeof(session_cookie)} bytes")
        
        return redirect(url_for('mock_payment_page'))

    return render_template('add_passengers.html', booking=temp_booking, total_passengers=total_passengers)

@app.route('/destination')
def destination():
    destinations = fetch_all("SELECT * FROM destination ORDER BY name")
    return render_template('destination.html', destinations=destinations)

@app.route('/team')
def team():
    team_members = fetch_all("SELECT * FROM team_member ORDER BY id")
    return render_template('team.html', social=social_links, team_members=team_members)

@app.route('/testimonial')
def testimonial():
    testimonials = fetch_all("SELECT * FROM testimonial ORDER BY id")
    return render_template('testimonial.html', testimonials=testimonials)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        if not name or not email or not subject or not message:
            flash('All fields are required!', 'error')
        else:
            # In a real app, save to a 'contact_messages' table or send email
            print(f"--- NEW CONTACT MESSAGE ---")
            print(f"From: {name} <{email}>")
            print(f"Subject: {subject}")
            print(f"Message: {message}\n")
            flash('Your message has been sent successfully!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/cookies')
def cookies():
    return render_template('cookies.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/help')
def help_page():
    return render_template('help.html')

# --- User Authentication Routes ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not email or not password or not confirm_password:
            flash('All fields are required!', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')
        
        if fetch_one("SELECT id FROM user WHERE username = %s", (username,)):
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('register.html')
        
        if fetch_one("SELECT id FROM user WHERE email = %s", (email,)):
            flash('Email already registered. Please use a different email or login.', 'danger')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        sql = "INSERT INTO user (username, email, password_hash, is_admin) VALUES (%s, %s, %s, %s)"
        if execute_query(sql, (username, email, hashed_password, False)):
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('user_login'))
        else:
            flash('Registration failed. Please try again.', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = fetch_one("SELECT id, username, password_hash, is_admin FROM user WHERE username = %s", (username,))

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/my_bookings')
@login_required
def my_bookings():
    user_id = session.get('user_id')
    
    # Fetch package bookings, joining with package table to get package name/location
    user_bookings = fetch_all("""
        SELECT b.*, p.name AS package_name, p.location AS package_location
        FROM booking b
        JOIN package p ON b.package_id = p.id
        WHERE b.user_id = %s
        ORDER BY b.booking_date DESC
    """, (user_id,))
    
    # Fetch custom bookings
    user_custom_bookings = fetch_all("SELECT * FROM custom_booking WHERE user_id = %s ORDER BY start_date DESC", (user_id,))

    return render_template('my_bookings.html', 
                           user_bookings=user_bookings, 
                           user_custom_bookings=user_custom_bookings)

@app.route('/cancel-booking', methods=['POST'])
@login_required # Make sure user is logged in
def cancel_booking():
    booking_id = request.form.get('booking_id')
    user_id = session.get('user_id')

    if not booking_id:
        flash("Invalid request.", "danger")
        return redirect(url_for('my_bookings'))

    # 1. Fetch the booking to ensure it belongs to the logged-in user and to get its status and price
    # CORRECTED table name from 'bookings' to 'booking'
    booking = fetch_one("""
        SELECT id, status, total_price 
        FROM booking 
        WHERE id = %s AND user_id = %s
    """, (booking_id, user_id))

    if not booking:
        flash("Booking not found or you do not have permission to cancel it.", "danger")
        return redirect(url_for('my_bookings'))

    # 2. Check if the booking can be cancelled
    if booking['status'] != 'Confirmed':
        flash(f"This booking cannot be cancelled as its status is '{booking['status']}'.", "warning")
        return redirect(url_for('my_bookings'))

    # 3. Proceed with cancellation and refund calculation
    # CORRECTED column name from 'amount' to 'total_price'
    original_amount = booking['total_price']
    refund_amount = round(original_amount * 0.9, 2)  # Calculate 90% refund (10% deduction)

    # 4. Update the booking status to 'Cancelled' using your execute_query helper
    # CORRECTED table name from 'bookings' to 'booking'
    sql_update = "UPDATE booking SET status = %s WHERE id = %s"
    if execute_query(sql_update, ('Cancelled', booking_id)):
        # 5. Flash a success message SHOWING the refund amount
        flash(f"Booking cancelled successfully. An amount of ₹{refund_amount:,.2f} will be refunded.", "success")
    else:
        flash("There was an error cancelling the booking. Please try again.", "danger")
    
    return redirect(url_for('my_bookings'))

# --- Admin Routes (Basic Example) ---
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin_user = fetch_one("SELECT id, username, password_hash FROM admin WHERE username = %s", (username,))

        if admin_user and check_password_hash(admin_user['password_hash'], password):
            # Set session variables for both admin-specific and general user display
            session['admin_logged_in'] = True
            session['admin_username'] = admin_user['username']
            
            # IMPORTANT: Set these for navbar dynamic display
            session['user_id'] = admin_user['id'] # Using admin's ID as user_id for session context
            session['username'] = admin_user['username'] # Use admin's username as general username
            session['is_admin'] = True # Flag this session as an admin
            
            flash('Admin logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials.', 'danger')
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
@admin_login_required
def admin_dashboard():
    total_users_data = fetch_one("SELECT COUNT(*) AS count FROM user")
    total_users = total_users_data['count'] if total_users_data else 0

    total_packages_data = fetch_one("SELECT COUNT(*) AS count FROM package")
    total_packages = total_packages_data['count'] if total_packages_data else 0

    pending_bookings_data = fetch_one("SELECT COUNT(*) AS count FROM booking WHERE status = 'Pending'")
    pending_bookings = pending_bookings_data['count'] if pending_bookings_data else 0
    
    # Fetch latest feedbacks, joining with user table to get username
    latest_feedbacks = fetch_all("""
        SELECT f.*, u.username 
        FROM feedback f
        LEFT JOIN user u ON f.user_id = u.id
        ORDER BY f.feedback_date DESC LIMIT 5
    """)

    return render_template('admin_dashboard.html',
                           total_users=total_users,
                           total_packages=total_packages,
                           pending_bookings=pending_bookings,
                           latest_feedbacks=latest_feedbacks)
# --- Admin Routes (Basic Example) ---

# ... (other admin routes) ...

@app.route('/admin/bookings')
@admin_login_required # Admin access required
def admin_bookings():
    conn = get_db_connection() # <--- ADD THIS LINE to get the connection
    if not conn:
        flash('Could not connect to database for bookings data.', 'danger')
        return redirect(url_for('admin_dashboard')) # Redirect if no connection

    cursor = conn.cursor(dictionary=True) # Now 'conn' is defined
    
    # Fetch all package bookings, joining with user and package tables
    all_package_bookings = [] # Initialize empty list
    try:
        cursor.execute("""
            SELECT b.id, b.travel_date, b.num_adults, b.num_children, b.total_price, b.status, b.special_request, b.booking_date,
                   u.username AS user_username,
                   p.name AS package_name, p.location AS package_location
            FROM booking b
            JOIN user u ON b.user_id = u.id
            JOIN package p ON b.package_id = p.id
            ORDER BY b.booking_date DESC
        """)
        all_package_bookings = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error fetching package bookings: {err}")
        flash('Error loading package bookings.', 'danger')

    # Fetch all custom bookings, joining with user and destination tables (if destination_id is present)
    all_custom_bookings = [] # Initialize empty list
    try:
        cursor.execute("""
            SELECT cb.id, cb.start_date, cb.end_date, cb.num_travelers, cb.budget, cb.preferences, cb.status,
                   u.username AS user_username,
                   d.name AS destination_name_from_db
            FROM custom_booking cb
            JOIN user u ON cb.user_id = u.id
            LEFT JOIN destination d ON cb.destination_id = d.id -- Use LEFT JOIN as destination_id can be NULL
            ORDER BY cb.start_date DESC
        """)
        all_custom_bookings = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error fetching custom bookings: {err}")
        flash('Error loading custom bookings.', 'danger')
    finally:
        if cursor: # Ensure cursor is closed
            cursor.close()
        close_db_connection(conn) # Ensure connection is closed


    return render_template('admin/bookings.html', 
                           package_bookings=all_package_bookings, 
                           custom_bookings=all_custom_bookings)
@app.route('/admin/bookings/update/<int:booking_id>', methods=['POST'])
def update_booking_status(booking_id):
    new_status = request.form.get('status')  # e.g., "confirmed", "cancelled", etc.
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Sagar@2311",
        database="ai_tour_db"
    )
    cursor = db.cursor()
    cursor.execute("UPDATE bookings SET status = %s WHERE id = %s", (new_status, booking_id))
    db.commit()
    return redirect(url_for('admin_bookings'))

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    # IMPORTANT: Also clear these for navbar dynamic display
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_admin', None) 
    flash('Admin logged out.', 'info')
    return redirect(url_for('admin_login'))

# --- CRUD for Packages (Admin Only) ---
@app.route('/admin/packages')
@admin_login_required
def admin_packages():
    packages = fetch_all("SELECT * FROM package ORDER BY id")
    return render_template('admin/packages.html', packages=packages)

@app.route('/admin/package/add', methods=['GET', 'POST'])
@admin_login_required
def add_package():
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        price = request.form.get('price')
        days = request.form.get('days')
        # persons = request.form.get('persons') # Removed 'persons' from form data
        img = request.form.get('img') # Handle file uploads in a real app
        description = request.form.get('description')
        discount_percentage = request.form.get('discount_percentage', type=int)

        sql = """
        INSERT INTO package (name, location, price, days, img, description, discount_percentage)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        # Removed 'persons' from values tuple
        if execute_query(sql, (name, location, price, days, img, description, discount_percentage)):
            flash('Package added successfully!', 'success')
            return redirect(url_for('admin_packages'))
        else:
            flash('Failed to add package. Please check inputs and try again.', 'danger')
    return render_template('admin/add_package.html')

@app.route('/admin/package/edit/<int:package_id>', methods=['GET', 'POST'])
@admin_login_required
def edit_package(package_id):
    package = fetch_one("SELECT * FROM package WHERE id = %s", (package_id,))
    if not package:
        flash('Package not found!', 'danger')
        return redirect(url_for('admin_packages'))

    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        price = request.form.get('price')
        days = request.form.get('days')
        # persons = request.form.get('persons') # Removed 'persons' from form data
        img = request.form.get('img')
        description = request.form.get('description')
        discount_percentage = request.form.get('discount_percentage', type=int) # Corrected form field name.
        
        sql = """
        UPDATE package SET name=%s, location=%s, price=%s, days=%s, 
        img=%s, description=%s, discount_percentage=%s WHERE id=%s
        """
        if execute_query(sql, (name, location, price, days, img, description, discount_percentage, package_id)):
            flash('Package updated successfully!', 'success')
            return redirect(url_for('admin_packages'))
        else:
            flash('Failed to update package. Please try again.', 'danger')
    return render_template('admin/edit_package.html', package=package) # Create this template

@app.route('/admin/package/delete/<int:package_id>', methods=['POST'])
@admin_login_required
def delete_package(package_id):
    # Ensure foreign key constraints are handled (e.g., delete related bookings/itineraries first or set ON DELETE CASCADE)
    # If using ON DELETE CASCADE in SQL, just deleting the package will cascade.
    if execute_query("DELETE FROM package WHERE id = %s", (package_id,)):
        flash('Package deleted successfully!', 'success')
    else:
        flash('Failed to delete package. Check for associated data.', 'danger')
    return redirect(url_for('admin_packages'))

# --- Attraction Search Route ---
@app.route('/search_attractions', methods=['GET'])
def search_attractions():
    query = request.args.get('query', '').strip()
    attractions = []

    if query:
        # 1. Find packages matching the search query in their location or name
        # We use LIKE for partial matches and case-insensitivity (using LOWER for both sides)
        packages = fetch_all("""
            SELECT id, name, location FROM package
            WHERE LOWER(location) LIKE %s OR LOWER(name) LIKE %s
        """, (f'%{query.lower()}%', f'%{query.lower()}%'))

        # 2. Collect itinerary details for these packages
        if packages:
            package_ids = [p['id'] for p in packages]
            
            if package_ids:
                # Prepare placeholders for the IN clause dynamically
                placeholders = ', '.join(['%s'] * len(package_ids))
                
                # Fetch itineraries and include package name/location for context
                attractions = fetch_all(f"""
                    SELECT i.*, p.name AS package_name, p.location AS package_location
                    FROM itinerary i
                    JOIN package p ON i.package_id = p.id
                    WHERE i.package_id IN ({placeholders})
                    ORDER BY p.name, i.day_number
                """, tuple(package_ids))

                if not attractions:
                    # If packages are found but no itineraries exist for them
                    flash(f"No detailed itineraries (attractions) found for packages matching '{query}'.", 'info')
            else: # This 'else' covers cases where 'packages' list is not empty but 'package_ids' became empty (shouldn't happen with correct fetch_all)
                flash(f"No packages found matching '{query}'.", 'info')
        else:
            flash(f"No packages found matching '{query}'.", 'info')
    else:
        flash("Please enter a place name to search for attractions.", 'warning')

    return render_template('attraction_results.html', query=query, attractions=attractions)


# --- Dynamic Content Routes (Examples) ---

@app.route('/package/<int:package_id>/read-more')
def read_more(package_id):
    package = fetch_one("SELECT * FROM package WHERE id = %s", (package_id,))
    if not package:
        abort(404)
    
    # ✅ MODIFIED QUERY: This now joins itinerary with hotels to get hotel details for each day.
    itineraries_query = """
        SELECT i.*, h.name as hotel_name, h.rating as hotel_rating, h.image_url as hotel_image
        FROM itinerary i
        LEFT JOIN hotels h ON i.hotel_id = h.id
        WHERE i.package_id = %s
        ORDER BY i.day_number
    """
    itineraries = fetch_all(itineraries_query, (package_id,))
    
    # This query fetches all possible hotel choices for the package (optional to display)
    hotels_query = """
        SELECT h.* FROM hotels h
        JOIN package_hotels ph ON h.id = ph.hotel_id
        WHERE ph.package_id = %s
    """
    available_hotels = fetch_all(hotels_query, (package_id,))

    return render_template('package_detail.html',
                           package=package,
                           itineraries=itineraries, # This now includes hotel info
                           available_hotels=available_hotels,
                           social=social_links)

@app.route('/package/<int:package_id>/book-now')
@login_required
def book_now(package_id):
    package = fetch_one("SELECT id, name FROM package WHERE id = %s", (package_id,))
    if package:
        flash(f"You're initiating booking for: {package['name']}. Please fill out the form.", 'info')
        # Pass preselect_package_id to the booking page to pre-fill the package selection
        return redirect(url_for('booking', preselect_id=package['id'])) 
    flash("Selected package not found for booking.", 'warning')
    return redirect(url_for('packages_page'))

@app.route('/submit_feedback', methods=['GET', 'POST'])
@login_required
def submit_feedback():
    user_id = session.get('user_id')
    if request.method == 'POST':
        rating = request.form.get('rating', type=int)
        comment = request.form.get('comment')

        if not (1 <= rating <= 5) or not comment:
            flash('Invalid feedback. Please provide a rating (1-5) and comment.', 'danger')
            return redirect(url_for('submit_feedback'))
        
        sql = "INSERT INTO feedback (user_id, rating, comment) VALUES (%s, %s, %s)"
        if execute_query(sql, (user_id, rating, comment)):
            flash('Thank you for your feedback!', 'success')
            return redirect(url_for('testimonial'))
        else:
            flash('Failed to submit feedback. Please try again.', 'danger')
    return render_template('submit_feedback.html')


# --- Payment Simulation Routes ---

@app.route('/payment')
@login_required
def mock_payment_page():
    print("\n--- STEP 3: AT PAYMENT PAGE ---")
    print(f"Session on arrival at payment page: {session}")

    temp_booking = session.get('temp_booking')
    if not temp_booking:
        flash('No pending booking details found. Please try booking again.', 'danger')
        return redirect(url_for('booking'))
    
    booking_details = {
        'package_name': temp_booking['package_name'],
        'travel_date': datetime.strptime(temp_booking['travel_date'], '%Y-%m-%d').date(),
        'num_adults': temp_booking['num_adults'],
        'num_children': temp_booking['num_children'],
        'total_price': temp_booking['total_price'],
        'special_request': temp_booking['special_request']
    }
    return render_template('mock_payment.html', booking=booking_details)

@app.route('/confirm_payment', methods=['POST'])
@login_required
def confirm_payment():
    temp_booking = session.get('temp_booking')
    temp_passengers = session.get('temp_passengers')

    if not temp_booking or not temp_passengers:
        flash('Your booking session has expired. Please start again.', 'danger')
        return redirect(url_for('booking'))

    conn = get_db_connection()
    if not conn:
        flash('Could not connect to the database.', 'danger')
        return redirect(url_for('booking'))
    
    cursor = conn.cursor()
    try:
        # 1. Insert into booking table
        booking_sql = """
        INSERT INTO booking (user_id, package_id, travel_date, num_adults, num_children, total_price, special_request, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'Confirmed')
        """
        booking_values = (
            temp_booking['user_id'], temp_booking['package_id'], temp_booking['travel_date'],
            temp_booking['num_adults'], temp_booking['num_children'], temp_booking['total_price'],
            temp_booking['special_request']
        )
        cursor.execute(booking_sql, booking_values)
        new_booking_id = cursor.lastrowid

        # 2. Insert into passengers table
        passenger_sql = """
        INSERT INTO passengers (booking_id, name, age, gender, id_proof_type, id_proof_number)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        for passenger in temp_passengers:
            passenger_values = (
                new_booking_id, passenger['name'], passenger['age'], passenger['gender'],
                passenger['id_proof_type'], passenger['id_proof_number']
            )
            cursor.execute(passenger_sql, passenger_values)

        conn.commit()
        
        # Clear session data
        session.pop('temp_booking', None)
        session.pop('temp_passengers', None)
        
        flash('Payment successful! Your booking is confirmed.', 'success')
        return redirect(url_for('booking_confirmation', booking_id=new_booking_id))
    
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database Error: {err}")
        flash('A database error occurred. Could not confirm booking.', 'danger')
        return redirect(url_for('booking'))
    finally:
        cursor.close()
        close_db_connection(conn)

@app.route('/booking-confirmation/<int:booking_id>')
@login_required
def booking_confirmation(booking_id):
    # Fetch booking details
    booking_details = fetch_one("""
        SELECT b.*, p.name as package_name, p.location, p.days, p.img
        FROM booking b JOIN package p ON b.package_id = p.id
        WHERE b.id = %s AND b.user_id = %s
    """, (booking_id, session['user_id']))

    if not booking_details:
        flash('Booking not found or you do not have permission to view it.', 'danger')
        return redirect(url_for('my_bookings'))

    # Fetch passenger details
    passengers = fetch_all("SELECT * FROM passengers WHERE booking_id = %s", (booking_id,))

    # Fetch itinerary details
    itinerary = fetch_all("""
        SELECT i.*, h.name as hotel_name, h.rating as hotel_rating
        FROM itinerary i LEFT JOIN hotels h ON i.hotel_id = h.id
        WHERE i.package_id = %s ORDER BY i.day_number
    """, (booking_details['package_id'],))

    return render_template('booking_confirmation.html',
                           booking=booking_details,
                           passengers=passengers,
                           itinerary=itinerary)

# --- Error Handlers ---

@app.route('/404_page') # This is the URL path for your 404 page
def page_not_found_route(): # This is the endpoint name that url_for('page_not_found_route') links to
    return render_template('404.html'), 404

@app.errorhandler(404)
def error_404(e):
    return render_template('404.html'), 404

# --- Main Application Run Block ---

if __name__ == '__main__':
    # Initial setup: Create tables and populate with dummy data if they're empty.
    # This block should be carefully managed in production environments.
    print("Running database setup and population check...")
    setup_database()
    print("Starting Flask application...")
    app.run(debug=True)