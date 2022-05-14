import sqlite3

conn = sqlite3.connect('db/database.db')

# Create table
conn.execute('''CREATE TABLE users 
                (userId INTEGER PRIMARY KEY, 
                password TEXT,
                email TEXT,
                firstName TEXT,
                lastName TEXT,
                address1 TEXT,
                address2 TEXT,
                zipcode TEXT,
                city TEXT,
                state TEXT,
                country TEXT, 
                phone TEXT
            )''')
conn.execute('''CREATE TABLE products
                (productId INTEGER PRIMARY KEY,
                name TEXT,
                price REAL,
                description TEXT,
                image TEXT,
                stock INTEGER,
                categoryId INTEGER,
                keyNumber TEXT
                FOREIGN KEY(categoryId) REFERENCES categories(categoryId)
                )'''
             )
conn.execute('''CREATE TABLE kart
                (userId INTEGER,
                productId INTEGER,
                FOREIGN KEY(userId) REFERENCES users(userId),
                FOREIGN KEY(productId) REFERENCES products(productId)
            )''')
conn.execute('''CREATE TABLE categories
                (categoryId INTEGER PRIMARY KEY,
                name TEXT
                color TEXT
                imgCat TEXT
            )''')

conn.close()
