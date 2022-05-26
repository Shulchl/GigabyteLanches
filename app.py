from flask import *
import sqlite3, hashlib, os
from werkzeug.utils import secure_filename
from secrets import compare_digest
import os

app = Flask(__name__)
app.secret_key = 'MEU AMIGÃOZÃO, MEU AMIGÃOZÃÃÃO'
DATA_FOLDER = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(DATA_FOLDER, 'static/')
UPLOAD_FOLDER = os.path.join(DATA_FOLDER, 'static/uploads')
ALLOWED_EXTENSIONS = set([ 'jpeg', 'jpg', 'png', 'gif' ])
app.config[ 'UPLOAD_FOLDER' ] = UPLOAD_FOLDER


# favicon
@app.route('/favicon.ico')
def favicon():
    return url_for(STATIC_FOLDER, filename='images/icons/favicon.ico')


def getLoginDetails():
    with sqlite3.connect(dataFile) as conn:
        cur = conn.cursor()
        if 'email' not in session:
            loggedIn = False
            firstName = ''
            noOfItems = 0
        else:
            loggedIn = True
            cur.execute("SELECT userId, firstName FROM users WHERE email = ?", (session[ 'email' ],))
            userId, firstName = cur.fetchone()
            cur.execute("SELECT count(productId) FROM kart WHERE userId = ?", (userId,))
            noOfItems = cur.fetchone()[ 0 ]
    conn.close()
    return (loggedIn, firstName, noOfItems)


@app.route("/")
def root():
    loggedIn, firstName, noOfItems = getLoginDetails()
    with sqlite3.connect(dataFile) as conn:
        cur = conn.cursor()
        cur.execute('SELECT productId, name, price, description, image, stock, categoryId FROM products ORDER BY productId ASC')
        itemData = cur.fetchall()
        cur.execute('SELECT categoryId, name, color FROM categories ORDER BY categoryId ASC')
        categoryData = cur.fetchall()
        itemData = parse(itemData)
    return render_template('home.html', itemData=itemData, loggedIn=loggedIn, firstName=firstName,
                           noOfItems=noOfItems, categoryData=categoryData)

@app.route("/add")
def add():
    with sqlite3.connect(dataFile) as conn:
        cur = conn.cursor()
        cur.execute('SELECT productId, name, price, description, image, stock FROM products')
        data = cur.fetchall()
        cur.execute('SELECT categoryId, name, color FROM categories ORDER BY categoryId ASC')
        categories = cur.fetchall()
    conn.close()
    return render_template('product/add.html', data=data, categories=categories)

@app.route("/addItem", methods=["GET", "POST"])
def addItem():
    if request.method == "POST":
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        stock = int(request.form['stock'])
        try:
            addcat = request.form['Addcategory']
        except:
            addcat = None
        if addcat is not None:
            addcat = request.form['Addcategory']
            if isinstance(addcat, str):
                with sqlite3.connect(dataFile) as conn:
                    try:
                        cur = conn.cursor()
                        cur.execute('''INSERT INTO categories (name) VALUES (?)''', (str(addcat), ))
                        categoryId = int(cur.lastrowid)
                        conn.commit()
                        msg="item adicionado às categorias"
                    except Exception as e:
                        msg=f"error occured 1 {e}"
                        conn.rollback()
                print(msg)
                conn.close()
        else:
            categoryId = int(request.form['category'])         
        #Uploading image procedure
        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            imagename = filename
            with sqlite3.connect(dataFile) as conn:
                try:
                    cur = conn.cursor()
                    cur.execute('''INSERT INTO products (name, price, description, image, stock, categoryId) VALUES 
                                (?, ?, ?, ?, ?, ?)''', (name, price, description, imagename, stock, categoryId, ))
                    conn.commit()
                    msg="added successfully"
                except Exception as e:
                    msg=f"error occured {e}"
                    conn.rollback()
            conn.close()
            print(msg)
            return redirect(url_for('root'))

@app.route("/updateProduct" )
def updateProduct():
    loggedIn, firstName, noOfItems = getLoginDetails()
    productId = request.args.get('productId')
    with sqlite3.connect(dataFile) as conn:
        cur = conn.cursor()
        cur.execute('SELECT productId, name, price, description, image, stock, categoryId FROM products WHERE productId = ?',
                    (productId,))
        productData = cur.fetchone()
        cur.execute('SELECT categoryId, name FROM categories')
        categoryData = cur.fetchall()
    conn.close()
    return render_template('product/updateProduct.html', productData=productData, categoryData=categoryData, loggedIn=loggedIn,
                        firstName=firstName, noOfItems=noOfItems, productId=productId)

@app.route("/updateProd", methods=[ "GET", "POST" ])
def updateProd():
    if request.method == 'POST':
        productId = request.args.get('productId')
        name = request.form[ 'name' ]
        price = float(request.form[ 'price' ].replace(',', '.'))
        description = request.form[ 'description' ]
        stock = int(request.form[ 'stock' ])
        image = request.files['image']
        try:
            addcat = request.form['Addcategory']
            print(addcat)
        except:
            addcat = request.form['category']
            print(addcat)

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            imagename = filename
            
            with sqlite3.connect(dataFile) as conn:
                try:
                    cur = conn.cursor()
                    cur.execute('UPDATE products SET name = ?, price = ?, description = ?, stock = ?, image = ?, categoryId = ? WHERE productId = ?', 
                            (name, price, description, stock, imagename, addcat, productId, ))
                    conn.commit()
                    msg = "Saved Successfully"
                except Exception as e:
                    conn.rollback()
                    msg = f"Error occured 1\n\n{e}"
        else:
            with sqlite3.connect(dataFile) as conn:
                try:
                    cur = conn.cursor()
                    cur.execute('UPDATE products SET name = ?, price = ?, description = ?, stock = ?, categoryId = ? WHERE productId = ?', 
                                (name, price, description, stock, addcat, productId, ))
                    conn.commit()
                    msg = f"Saved Successfully"
                except Exception as e:
                    conn.rollback()
                    msg = f"Error occured 2\n\n{e}"
        
        conn.close()
        Response(msg)
        print(msg)
        return redirect(url_for('root'))

@app.route("/remove")
def remove():
    with sqlite3.connect(dataFile) as conn:
        cur = conn.cursor()
        cur.execute('SELECT productId, name, price, description, image, stock FROM products')
        data = cur.fetchall()
    conn.close()
    return render_template('product/remove.html', data=data)


@app.route("/removeItem")
def removeItem():
    productId = request.args.get('productId')
    with sqlite3.connect(dataFile) as conn:
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM products WHERE productID = ?', (productId, ))
            conn.commit()
            msg = "Deleted successsfully"
        except:
            conn.rollback()
            msg = "Error occured"
    conn.close()
    Response(msg)
    return redirect(url_for('root'))


@app.route("/displayCategory")
def displayCategory():
    loggedIn, firstName, noOfItems = getLoginDetails()
    categoryId = request.args.get("categoryId")
    with sqlite3.connect(dataFile) as conn:
        cur = conn.cursor()
        cur.execute("SELECT products.productId, products.name, "
                    "products.price, products.image, categories.name "
                    "FROM products, categories WHERE products.categoryId = "
                    "categories.categoryId AND categories.categoryId = ?", (categoryId,))
        data = cur.fetchall()
    conn.close()
    if data:
        categoryName = data[ 0 ][ 4 ]
    else:
        categoryName = "Não encontramos nada"
    data = parse(data)
    return render_template('product/displayCategory.html', data=data, loggedIn=loggedIn,
                        firstName=firstName, noOfItems=noOfItems, categoryName=categoryName, categoryId=categoryId)

@app.route("/createCategory" )
def createCategory():
    return render_template('product/createCategory.html')

@app.route("/createCat", methods=[ "GET", "POST" ])
def createCat():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    else:
        if request.method == 'POST':
            name = request.form[ 'name' ]
            color = request.form[ 'color' ]
            image = request.files['imgCat']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            imagename = filename
            with sqlite3.connect(dataFile) as conn:
                cur = conn.cursor()
                try:
                    cur.execute("INSERT INTO categories (name, color, imgCat) VALUES (?, ?, ?)", (name, color, imagename))
                    conn.commit()
                    categoryId = int(cur.lastrowid)
                    msg = "Added successfully"
                except:
                    conn.rollback()
                    msg = "Error occured"
            conn.close()
            Response(msg)
            print(msg)
            return redirect(url_for('root'))

@app.route("/updateCategory" )
def updateCategory():
    categoryId = int(request.args.get('categoryId'))
    with sqlite3.connect(dataFile) as conn:
        cur = conn.cursor()
        cur.execute('SELECT categoryId, name, imgCat, color FROM categories WHERE categoryId = ?', (categoryId, ))
        data = cur.fetchall()
        print(categoryId)
    conn.close()
    return render_template('product/updateCategory.html', data=data, categoryId=categoryId)

@app.route("/updateCat", methods=[ "GET", "POST" ])
def updateCat():
    categoryId = int(request.args.get('categoryId'))
    if request.method == 'POST':
        name = request.form[ 'name' ]
        print(name)
        color = request.form[ 'color' ]
        print(color)
        image = request.files['imgCat']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            imagename = filename
            with sqlite3.connect(dataFile) as conn:
                try:
                    cur = conn.cursor()
                    cur.execute('UPDATE categories SET name = ?, color = ?, '
                                'imgCat = ? WHERE categoryId = ?',
                                (name, color, imagename, categoryId))
                    conn.commit()
                    msg = "Saved Successfully"
                except Exception as e:
                    conn.rollback()
                    msg = f"Error occured\n\n{e}"
        else:
            with sqlite3.connect(dataFile) as conn:
                try:
                    cur = conn.cursor()
                    cur.execute('UPDATE categories SET name = ?, color = ? '
                                'WHERE categoryId = ?',
                                (name, color, categoryId))
                    conn.commit()
                    msg = "Saved Successfully"
                except Exception as e:
                    conn.rollback()
                    msg = f"Error occured\n\n{e}"

        conn.close()
        Response(msg)
        return redirect(url_for('root'))
    categoryName = data[ 0 ][ 4 ]
    data = parse(data)
    return render_template('displayCategory.html', data=data, loggedIn=loggedIn,
                           firstName=firstName, noOfItems=noOfItems, categoryName=categoryName)


@app.route("/account/profile")
def profileHome():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    return render_template("user/profileHome.html", loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/account/profile/view")
def viewProfile():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    with sqlite3.connect(dataFile) as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId, email, firstName, lastName, "
                    "address1, address2, zipcode, city, state, country, phone "
                    "FROM users WHERE email = ?", (session[ 'email' ],))
        profileData = cur.fetchone()
    conn.close()
    return render_template("user/profileView.html", profileData=profileData,
                           loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/account/profile/edit")
def editProfile():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    with sqlite3.connect(dataFile) as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId, email, firstName, lastName, "
                    "address1, address2, zipcode, city, state, country, phone "
                    "FROM users WHERE email = ?", (session[ 'email' ],))
        profileData = cur.fetchone()
    conn.close()
    return render_template("user/editProfile.html", profileData=profileData,
                           loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)


@app.route("/account/profile/changePassword", methods=[ "GET", "POST" ])
def changePassword():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    if request.method == "POST":
        oldPassword = request.form[ 'oldpassword' ]
        oldPassword = hashlib.md5(oldPassword.encode()).hexdigest()
        newPassword = request.form[ 'newpassword' ]
        newPassword = hashlib.md5(newPassword.encode()).hexdigest()
        with sqlite3.connect(dataFile) as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId, password FROM users WHERE email = ?", (session[ 'email' ],))
            userId, password = cur.fetchone()
            if compare_digest(password, oldPassword):
                try:
                    cur.execute("UPDATE users SET password = ? WHERE userId = ?", (newPassword, userId))
                    conn.commit()
                    msg = "Changed successfully"
                except:
                    conn.rollback()
                    msg = "Failed"
                Response(msg)
                return render_template("user/changePassword.html", msg=msg)
            else:
                msg = "Wrong password"
        Response(msg)
        conn.close()
        return render_template("user/changePassword.html", msg=msg)
    else:
        return render_template("user/changePassword.html")


@app.route("/updateProfile", methods=[ "GET", "POST" ])
def updateProfile():
    if request.method == 'POST':
        email = request.form[ 'email' ]
        firstName = request.form[ 'firstName' ]
        lastName = request.form[ 'lastName' ]
        address1 = request.form[ 'address1' ]
        address2 = request.form[ 'address2' ]
        zipcode = request.form[ 'zipcode' ]
        city = request.form[ 'city' ]
        state = request.form[ 'state' ]
        country = request.form[ 'country' ]
        phone = request.form[ 'phone' ]
        with sqlite3.connect(dataFile) as conn:
            try:
                cur = conn.cursor()
                cur.execute('UPDATE users SET firstName = ?, lastName = ?, '
                            'address1 = ?, address2 = ?, zipcode = ?, city = ?, '
                            'state = ?, country = ?, phone = ? WHERE email = ?',
                            (firstName, lastName, address1, address2, zipcode,
                             city, state, country, phone, email))
                conn.commit()
                msg = "Saved Successfully"
            except:
                conn.rollback()
                msg = "Error occured"
        conn.close()
        Response(msg)
        return redirect(url_for('editProfile'))


@app.route("/loginForm")
def loginForm():
    if 'email' in session:
        return redirect(url_for('root'))
    else:
        return render_template('user/login.html', error='')


@app.route("/login", methods=[ 'POST', 'GET' ])
def login():
    if request.method == 'POST':
        email = request.form[ 'email' ]
        password = request.form[ 'password' ]
        if is_valid(email, password):
            session[ 'email' ] = email
            return redirect(url_for('root'))
        else:
            error = 'Invalid UserId / Password'
            return render_template('user/login.html', error=error)


@app.route("/productDescription")
def productDescription():
    loggedIn, firstName, noOfItems = getLoginDetails()
    productId = request.args.get('productId')
    with sqlite3.connect(dataFile) as conn:
        cur = conn.cursor()
        cur.execute('SELECT productId, name, price, description, image, stock, categoryId FROM products WHERE productId = ?',
                    (productId,))
        productData = cur.fetchone()
        cur.execute('SELECT categoryId, name, color FROM categories WHERE categoryId = ?', (productData[6], ))
        categoryData = cur.fetchall()
    conn.close()
    return render_template("product/productDescription.html", data=productData, loggedIn=loggedIn, firstName=firstName,
                           noOfItems=noOfItems, categoryData = categoryData)


@app.route("/addToCart")
def addToCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    else:
        productId = int(request.args.get('productId'))
        with sqlite3.connect(dataFile) as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId FROM users WHERE email = ?", (session[ 'email' ],))
            userId = cur.fetchone()[ 0 ]
            try:
                cur.execute("INSERT INTO kart (userId, productId) VALUES (?, ?)", (userId, productId))
                conn.commit()
                msg = "Added successfully"
            except:
                conn.rollback()
                msg = "Error occured"
        conn.close()
        Response(msg)
        return redirect(url_for('root'))


@app.route("/cart")
def cart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session[ 'email' ]
    with sqlite3.connect(dataFile) as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = ?", (email,))
        userId = cur.fetchone()[ 0 ]
        cur.execute(
            "SELECT products.productId, products.name, products.price, products.image FROM "
            "products, kart WHERE products.productId = kart.productId AND kart.userId = ?",
            (userId,))
        products = cur.fetchall()
    totalPrice = 0
    for row in products:
        totalPrice += row[ 2 ]
    return render_template("product/cart.html", products=products, totalPrice=totalPrice, loggedIn=loggedIn,
                           firstName=firstName, noOfItems=noOfItems)


@app.route("/removeFromCart")
def removeFromCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    email = session[ 'email' ]
    productId = int(request.args.get('productId'))
    with sqlite3.connect(dataFile) as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = ?", (email,))
        userId = cur.fetchone()[ 0 ]
        try:
            cur.execute("DELETE FROM kart WHERE userId = ? AND productId = ?", (userId, productId))
            conn.commit()
            msg = "removed successfully"
        except:
            conn.rollback()
            msg = "error occured"
    conn.close()
    Response(msg)
    return redirect(url_for('root'))


@app.route("/logout")
def logout():
    session.pop('email', None)
    return redirect(url_for('root'))


def is_valid(email, password):
    conn = sqlite3.connect(dataFile)
    cur = conn.cursor()
    cur.execute('SELECT email, password FROM users')
    data = cur.fetchall()
    for row in data:
        if row[ 0 ] == email and row[ 1 ] == hashlib.md5(password.encode()).hexdigest():
            return True
    return False


@app.route("/register", methods=[ 'GET', 'POST' ])
def register():
    if request.method == 'POST':
        # Parse form data
        password = request.form[ 'password' ]
        email = request.form[ 'email' ]
        firstName = request.form[ 'firstName' ]
        lastName = request.form[ 'lastName' ]
        address1 = request.form[ 'address1' ]
        address2 = request.form[ 'address2' ]
        zipcode = request.form[ 'zipcode' ]
        city = request.form[ 'city' ]
        state = request.form[ 'state' ]
        country = request.form[ 'country' ]
        phone = request.form[ 'phone' ]
        with sqlite3.connect(dataFile) as conn:
            try:
                cur = conn.cursor()
                cur.execute('INSERT INTO users (password, email, firstName, lastName, '
                            'address1, address2, zipcode, city, state, country, phone) '
                            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                            (hashlib.md5(password.encode()).hexdigest(), email, firstName,
                             lastName, address1, address2, zipcode, city, state, country, phone))
                conn.commit()
                msg = "Registered Successfully"
            except:
                conn.rollback()
                msg = "Error occured"
        conn.close()
        return render_template("user/login.html", error=msg)

@app.route("/registerationForm")
def registrationForm():
    return render_template("user/register.html")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[ 1 ] in ALLOWED_EXTENSIONS


def parse(data):
    ans = [ ]
    i = 0
    while i < len(data):
        curr = [ ]
        for j in range(7):
            if i >= len(data):
                break
            curr.append(data[ i ])
            i += 1
        ans.append(curr)
    return ans


if __name__ == '__main__':
    app.run(debug=False)
