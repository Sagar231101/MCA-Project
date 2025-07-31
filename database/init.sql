
CREATE TABLE packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price INTEGER,
    days INTEGER,
    image TEXT
);

CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    package_id INTEGER,
    FOREIGN KEY (package_id) REFERENCES packages (id)
);
