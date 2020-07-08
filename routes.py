"""
All dynamic routing belongs here 
"""
import os, json, ast, random, datetime
import sqlite3
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_mysqldb import MySQL
from flask import render_template, redirect, flash, url_for, request, jsonify, Request, send_file, make_response,session, abort, send_file,render_template_string
from controllers import app, mail
from controllers.forms import RegistrationForm, LoginForm, Billing, PaymentInfo, ContactUs, PasswordForm, Disable, Activate
from controllers.forms import RegistrationForm, LoginForm, AdminAddProductForm, AdminUpdateProductForm, UpdateAccountForm, UpdateBilling, RequestResetForm, ResetPasswordForm, UpdateCard, ResetPassForm, ChangePasswordForm
from controllers.email import sendEmail
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_mail import Message
from flask import Flask
from controllers import key
import base64, platform
from datetime import datetime, timedelta
from flask_csv import send_csv
import markdown.extensions.fenced_code
from jinja2 import Environment
import urllib

Jinija2 = Environment()

@app.route('/new')
def new():
    injected = request.args.get('i')
    if injected == None:
        injected = ""
    print(render_template_string(injected))
    return render_template_string(f'''
    <h1>Test it on this page first!</h1>
    <h1>{injected}</h1>''')

@app.errorhandler(404)
def page_not_found(error):
    template = '''
    <h1>Oops! This page doesn't exist!</h1>
    <h3>%s does not work!</h3>
    ''' % (urllib.parse.unquote(request.url))
    return render_template_string(template)


DATABASE = 'controllers/site.db'
returnedMessage = None

def query_db(query):
    db = sqlite3.connect(DATABASE)
    cur = db.cursor()
    cur.execute(query)
    rv = cur.fetchall()
    cur.close()
    return (rv if rv else None)

def insert_db(query):
    print(query)
    db = sqlite3.connect(DATABASE)
    cur = db.cursor()
    cur.execute(query)
    print('success')
    db.commit()

def get_reset_token(user, expires_sec=300):
    s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
    return s.dumps({'user_id': user[0]}).decode('utf-8')


def verify_reset_token(token):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token)['user_id']
    except:
        return None
    return user_id



# """
# Functions 
# """
# Refreshes the json file if admin adds a new product in##
def refresh():
    with open('json_files/product.json', 'r+') as f:
        data = json.load(f)
    return data 

def refreshEvents():
    with open('json_files/events.json', 'r+') as f:
        data = json.load(f)
    return data

def refreshAnalytics():
    with open('json_files/analytics.json', 'r+') as f:
        data = json.load(f)
    return data 

# ##Ensures that allowed images are accepted##
def allowed_image(filename):
    if not "." in filename:
        return False
    ext = filename.rsplit(".", 1)[1]
    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return True


# """
# Home, contact-us, about pages 
# """

@app.route('/files', defaults={'req_path': ''})
@app.route('/files<path:req_path>')
def dir_listing(req_path):
    BASE_DIR = 'files'

    # Joining the base and the requested path
    abs_path = os.path.join(BASE_DIR, req_path)

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        return send_file(abs_path)

    # Show directory contents
    files = os.listdir(abs_path)
    return render_template('files.html', files=files)

@app.route('/files/<path>')
def fi(path):
    try:
        readme_file = open(f"files/{path}", "r")
        md_template_string = markdown.markdown(
            readme_file.read(), extensions=["fenced_code"]
        )
    except:
        return send_file(f"files/{path}")
    return md_template_string
@app.route('/')
def home():
    if "user_id" in session:
        orginalCartItems = query_db(f"SELECT * FROM product WHERE user_id = {session['user_id']}")
        if orginalCartItems == None:
            orginalCartItems = []
    else:
        orginalCartItems = []
    return render_template('homepage.html', cartItems=orginalCartItems)

@app.route('/about')
def about():
    if "user_id" in session:
        orginalCartItems = query_db(f"SELECT * FROM product WHERE user_id = {session['user_id']}")
        if orginalCartItems == None:
            orginalCartItems = []
    else:
        orginalCartItems = []
    return render_template('aboutus.html', cartItems=orginalCartItems)

@app.route('/contactUs', methods=['GET', 'POST'])
def contactUs():
    if "user_id" in session:
        orginalCartItems = query_db(f"SELECT * FROM product WHERE user_id = {session['user_id']}")
        if orginalCartItems == None:
            orginalCartItems = []
    else:
        orginalCartItems = []
    form = ContactUs()
    if request.method == 'POST':
        sendEmail(form.email.data, form.fullname.data, form.feedback.data, request.form['optradio'])
        flash(f'Message has been send! Thank you for leaving a message :) ', 'success')
        return redirect(url_for('home'))
    else:
        pass
    return render_template("contactUs.html", form=form, cartItems=orginalCartItems)

# """
# ERROR ROUTE
# """
# """
# Account Related Routes 
# """
@app.route('/register', methods=['GET', 'POST'])
def register():
    # if current_user.is_authenticated:
    #     return redirect(url_for('registerStep2'))
    form = RegistrationForm()
    if request.method == 'POST' and form.validate_on_submit():
        # hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        query = f"""INSERT INTO user(user_id, fullname, email, password, security_question, security_answer) VALUES(NULL, \'{form.fullname.data}\', \'{form.email.data}\' , \'{form.password.data}\', \'{form.security_question.data}\', \'{form.security_answer.data}\');"""
        insert_db(query)
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/registerStep2', methods=['GET', 'POST'])
def registerStep2():
    form = Billing()
    if form.validate_on_submit():
        # exisr = AddressInfo.query.filter_by(address=form.address.data, user_id=current_user.id).first()
        # print(exisr)
        exisr = query_db(f"SELECT * FROM address_info WHERE address= \'{form.address.data}\' AND user_id={session['user_id']}")
        print(exisr)
        if exisr == None:
            address = form.address.data
            address = address.strip()
            country = form.country.data
            state = form.state.data
            postal = form.postal.data
            insert_db(f"Update address_info set default_add = 0 WHERE user_id={session['user_id']}")
            insert_db(f"INSERT INTO address_info(addressID, address, country, state, postal, default_add, user_id) VALUES(NULL, \'{address}\', \'{country}\', \'{state}\', \'{postal}\', 1, {session['user_id']})")
            return redirect(url_for('myAccount'))
        # elif str(exisr).find('SELECT') != None and exisr == None:
        #     address = form.address.data
        #     country = form.country.data
        #     state = form.state.data
        #     postal = form.postal.data
        #     address = AddressInfo(address=address, country=country, state=state, postal=postal, user_id = current_user.id, default='True')
        #     db.session.add(address)
        #     db.session.commit()
        #     return redirect(url_for('myAccount'))
        else:
            flash('Address already added! Please add a different address', 'danger')
    return render_template('registerStep2.html', form = form, data=[])

@app.route('/editAddress', methods=['GET', 'POST'])
def editBilling():
    address = request.args.get('address')
    addressinfo = query_db(f"SELECT * FROM address_info WHERE address= \'{address}\'")[0]
    print(addressinfo[1])
    # addressinfo = AddressInfo.query.filter_by(address=address, user_id=current_user.id).first()
    form = UpdateBilling()
    if form.validate_on_submit() and request.method=='POST':
        exisr = query_db(f"SELECT address FROM address_info WHERE address= \'{form.address.data}\' AND user_id = {session['user_id']}")
        if exisr == None:
            print('new address')
            insert_db(f"UPDATE address_info set country = \'{form.country.data}\' WHERE address=\'{address}\' AND user_id = {session['user_id']}")
            insert_db(f"UPDATE address_info set postal = \'{form.postal.data}\' WHERE address=\'{address}\' AND user_id = {session['user_id']}")
            insert_db(f"UPDATE address_info set state = \'{form.state.data}\' WHERE address=\'{address}\' AND user_id = {session['user_id']}")
            insert_db(f"UPDATE address_info set address = \'{form.address.data}\' WHERE address=\'{address}\' AND user_id = {session['user_id']}")
            # addressinfo.address = form.address.data
            # addressinfo.country = form.country.data
            # addressinfo.state = form.state.data
            # addressinfo.postal = form.postal.data
            # db.session.commit()
            return redirect(url_for('myAccount'))
        elif addressinfo[1] == form.address.data:
            print("same address")
            insert_db(f"UPDATE address_info set address = \'{form.address.data}\' WHERE address=\'{address}\' AND user_id = {session['user_id']}")
            insert_db(f"UPDATE address_info set country = \'{form.country.data}\' WHERE address=\'{address}\' AND user_id = {session['user_id']}")
            insert_db(f"UPDATE address_info set postal = \'{form.postal.data}\' WHERE address=\'{address}\' AND user_id = {session['user_id']}")
            insert_db(f"UPDATE address_info set state = \'{form.state.data}\' WHERE address=\'{address}\' AND user_id = {session['user_id']}")
            return redirect(url_for('myAccount'))
        else:
            flash('Address already added! Please add a different address', 'danger')
            return render_template('editAddress.html', form=form, data = addressinfo)
    return render_template('editAddress.html', form=form, data = addressinfo)
    
@app.route('/editCardInfo', methods=['GET', 'POST'])
def editCardInfo():
    cardno = request.args.get('card')
    cardinfo = query_db(f"SELECT * FROM card_info WHERE cardno= \'{cardno}\'")[0]
    print(cardinfo[1])
    # addressinfo = AddressInfo.query.filter_by(address=address, user_id=current_user.id).first()
    form = UpdateCard()
    if form.validate_on_submit() and request.method=='POST':
        exisr = query_db(f"SELECT cardno FROM card_info WHERE cardno= \'{form.cardno.data}\' AND user_id = {session['user_id']}")
        if exisr == None:
            insert_db(f"UPDATE card_info set month = \'{form.exp.data}\' WHERE cardno= \'{cardno}\' AND user_id = {session['user_id']}")
            insert_db(f"UPDATE card_info set year = \'{form.year.data}\' WHERE cardno= \'{cardno}\' AND user_id = {session['user_id']}")
            insert_db(f"UPDATE card_info set card_name = \'{form.name.data}\' WHERE cardno= \'{cardno}\' AND user_id = {session['user_id']}")
            insert_db(f"UPDATE card_info set cardno = \'{form.cardno.data}\' WHERE cardno= \'{cardno}\' AND user_id = {session['user_id']}")
            # addressinfo.address = form.address.data
            # addressinfo.country = form.country.data
            # addressinfo.state = form.state.data
            # addressinfo.postal = form.postal.data
            # db.session.commit()
            return redirect(url_for('myAccount'))
        elif cardinfo[2] == form.cardno.data:
            insert_db(f"UPDATE card_info set month = \'{form.exp.data}\' WHERE cardno= \'{cardno}\' AND user_id = {session['user_id']}")
            insert_db(f"UPDATE card_info set year = \'{form.year.data}\' WHERE cardno= \'{cardno}\' AND user_id = {session['user_id']}")
            insert_db(f"UPDATE card_info set card_name = \'{form.name.data}\' WHERE cardno= \'{cardno}\' AND user_id = {session['user_id']}")
            insert_db(f"UPDATE card_info set cardno = \'{form.cardno.data}\' WHERE cardno= \'{cardno}\' AND user_id = {session['user_id']}")
            return redirect(url_for('myAccount'))
        else:
            flash('Card already added! Please add a different card', 'danger')
            return render_template('editCard.html', form=form, data = cardinfo)       
    return render_template('editCard.html', form=form, data = cardinfo)

@app.route('/registerStep3', methods=['GET', 'POST'])
def registerStep3():
    form = PaymentInfo()
    if form.validate_on_submit():
        # exisr = AddressInfo.query.filter_by(address=form.address.data, user_id=current_user.id).first()
        # print(exisr)
        exisr = query_db(f"SELECT * FROM card_info WHERE cardno = \'{form.cardno.data}\' AND user_id={session['user_id']}")
        print(exisr)
        if exisr == None:
            cardno = form.cardno.data
            cardno = cardno.strip()
            if cardno[0] == '5':
                card_type = "master"
            else:
                card_type = "visa"
            cardname = form.name.data
            exp = form.exp.data
            year = form.year.data
            insert_db(f"Update card_info set default_CARD = 0 WHERE user_id={session['user_id']}")
            insert_db(f"INSERT INTO card_info(cardID, card_name, cardno, month, year, default_CARD, card_type,user_id) VALUES(NULL, \'{cardname}\', \'{cardno}\', \'{exp}\', \'{year}\', 1, \'{card_type}\',{session['user_id']})")
            return redirect(url_for('myAccount'))
        else:
            flash('Card already added! Please add a different card', 'danger')
    return render_template('registerStep3.html', form = form, data=None)

    
@app.route('/login', methods=['GET', 'POST'])
def login(): 
    form = LoginForm()
    if form.validate_on_submit():
        # emailExist = (f"SELECT email FROM user WHERE email = '{form.email.data}' and password = '{form.password.data}';")
        user = f"SELECT * FROM user WHERE email =  '{form.email.data}' AND password = \'{form.password.data}\';"
        email = query_db(f"SELECT * FROM user WHERE email = '{form.email.data}'")[0]
        if email == None:
            flash('Invalid email. Please input a valid email', 'danger')
        else:
            if query_db(user) != None:
                # print(user)
                # passwordExist = query_db(f"SELECT password FROM user WHERE email = \'{form.email.data}\';")
                # if passwordExist[0][0] == form.password.data:
                activeCheck = query_db(f"SELECT status FROM user WHERE email = \'{form.email.data}\'")[0][0]
                adminMail = email[3]
                session['user_id'] = query_db(user)[0][0]
                # id = query_db(user)[0][0]
                if activeCheck == "Inactive":
                    return redirect(url_for('activateask'))
                elif "@prestigium.com" in adminMail:
                    return redirect(url_for('admin'))
                print(query_db(user))
                return redirect(url_for('home'))
            else:
                flash('Wrong password. Please check your password', 'danger')
    return render_template('login.html', title='Login', form=form)
  

@app.route('/myAccount', methods=['GET', 'POST'])
def myAccount():
    orginalCartItems = query_db(f"SELECT * FROM product WHERE user_id = {session['user_id']}")
    if orginalCartItems == None:
        orginalCartItems = []
    removeConfirmation = request.args.get('delete')
    removeAddress = request.args.get('address')
    removeCard = request.args.get('card')
    removeReview = request.args.get('name')
    if removeAddress != None and removeConfirmation == 'true':
        # address = AddressInfo.query.filter_by(address=removeAddress, user_id = current_user.id).first()
        insert_db(f"DELETE FROM address_info WHERE address= \'{removeAddress}\' AND user_id= {session['user_id']}")
        addresses = query_db(f"SELECT * FROM address_info WHERE user_id = {session['user_id']}")[-1][1]
        insert_db(f"UPDATE address_info set default_add = {1} WHERE address=\'{addresses}\' AND user_id= {session['user_id']}")
        return redirect(url_for('myAccount'))
    elif removeReview != None and removeConfirmation == 'true': 
        # review = Review.query.filter_by(prod_name=removeReview, user_id=current_user.id).first()
        insert_db(f"DELETE FROM review WHERE prod_name= \'{removeReview}\' AND user_id= {session['user_id']}")
    elif removeCard != None and removeConfirmation == 'true':
        # cards = CardInfo.query.filter_by(user_id=current_user.id)
        insert_db(f"DELETE FROM card_info WHERE cardno = \'{removeCard}\' AND user_id = {session['user_id']} ")
        cards = query_db(F"SELECT * FROM card_info WHERE user_id= {session['user_id']}")
        insert_db(f"UPDATE card_info set default_CARD = {1} WHERE cardno = \'{cards[-1][2]}\' AND user_id = {session['user_id']}")
        return redirect(url_for('myAccount'))
    old = request.args.get('old')
    new = request.args.get('new')
    if old != None:
        old_password = query_db(f"SELECT password FROM user WHERE user_id= {session['user_id']}")[0][0]
        if old_password != old:
            return "wrong"
    if new != None:
        insert_db(f"UPDATE user set password = \'{new}\'  WHERE user_id = {session['user_id']}")
        return redirect(url_for('myAccount'))
    form = UpdateAccountForm()
    if form.submit.data and form.validate_on_submit():
        print('no')
        image = request.files['image']
        filename = request.files['image'].filename  
        print(filename)  
        if filename:
            image.save(os.path.join(app.config["PROFILE_UPLOADS"], filename))
            insert_db(f"UPDATE user set image_file = \'../static/img/profile_pic/{filename}\'  WHERE user_id = {session['user_id']}")
        insert_db(f"UPDATE user set fullname = \'{form.fullname.data}\'  WHERE user_id = {session['user_id']}")
        insert_db(f"UPDATE user set email = \'{form.email.data}\'  WHERE user_id = {session['user_id']}")
        # flash('Your account has been updated!', 'success')
        return redirect(url_for('myAccount'))
    elif request.method == 'GET':
        tran_list = []
        card_list = []
        form.fullname.data = query_db(f"SELECT * FROM user WHERE user_id={session['user_id']}")[0][2]
        form.email.data = query_db(f"SELECT * FROM user WHERE user_id={session['user_id']}")[0][3]
        image_file = query_db(f"SELECT * FROM user WHERE user_id={session['user_id']}")[0][4][0]
        address = query_db(f"SELECT * FROM address_info WHERE user_id = {session['user_id']}")
        cards = query_db(f"SELECT * FROM card_info WHERE user_id = {session['user_id']}")
        if cards == None:
            cards = []
        else:
            for i in cards:
                card_list.append({'id':i[0],'card_name':i[1], 'cardno':i[2], 'exp':i[3], 'year':i[4], "card_type":i[5], "default":i[6]})
        previous_transactions = query_db(f"SELECT * FROM previous_transactions WHERE user_id={session['user_id']}")
        reviews = query_db(f"SELECT * FROM review WHERE user_id={session['user_id']}")
        if previous_transactions == None:
            pass
        else:
            for i in previous_transactions:
                total = 0
                date = i[2]
                items = ast.literal_eval(i[1])
                for j in items:
                    total += j['prod_price']*j['prod_quantity']
                tran_list.append({'id':i[0], 'total':total ,'date': str(date), 'status': i[3],'items':ast.literal_eval(i[1])})
    tran_list = []
    card_list = []
    image_file = query_db(f"SELECT image_file from user WHERE user_id={session['user_id']}")
    address = query_db(f"SELECT * FROM address_info WHERE user_id={session['user_id']}")
    cards = query_db(f"SELECT * FROM card_info WHERE user_id={session['user_id']}")
    print(cards)
    if cards == None:
        cards = []
    else:
        for i in cards:
            print(i[0])
            card_list.append({'id':i[0],'card_name':i[1], 'cardno':i[2], 'exp':i[3], 'year':i[4], "card_type":i[6], "default":i[5]})
    previous_transactions = query_db(f"SELECT * FROM previous_transactions WHERE user_id={session['user_id']}") 
    reviews = query_db(f"SELECT * FROM review WHERE user_id={session['user_id']}")
    if previous_transactions == None:
        pass
    else:
        for i in previous_transactions:
            total = 0
            date = i[2]
            items = ast.literal_eval(i[1])
            for j in items:
                total += j['prod_price']*j['prod_quantity']
            tran_list.append({'id':i[0], 'total':total ,'date': str(date), 'status': i[3],'items':ast.literal_eval(i[1])})
    user = query_db(f"SELECT * FROM user WHERE user_id = {session['user_id']}")[0]  
    if address == None:
        address = []  
    if reviews == None:
        reviews = [] 
    return render_template('myAccount.html', title='Account', image_file=image_file, form=form,accountInfo = address, previous_transactions = tran_list, review=reviews, card=card_list, user=user, cartItems=orginalCartItems)


@app.route("/disable", methods=["GET", "POST"])
def disable():
    form = Disable()
    if form.validate_on_submit():
        password = query_db(f"SELECT password FROM user WHERE user_id={session['user_id']}")[0][0]
        if password != None and form.password.data == password:
            inactive_user = (f"UPDATE user SET status = 'Inactive' WHERE user_id='{session['user_id']}'")
            insert_db(inactive_user)
            session.pop('user_id', None)
            return redirect(url_for('home'))
        else:
            flash('Password is inncorrect. Please retype your password.', 'danger')
            return redirect(url_for('disable'))
    return render_template('disable.html', form=form)
    #     if user and bcrypt.check_password_hash(user.password, form.password.data):
    #         current_user.active = "Inactive"
    #         db.session.commit()
    #         logout_user()
    #         return redirect(url_for('home'))
    #     else:
    #         flash('Password is inncorrect. Please retype your password.', 'danger')
    #         return redirect(url_for('disable'))
    # return render_template('disable.html', form=form)

@app.route("/activate", methods=["GET", "POST"])
def activate():
    form = Activate()
    if form.validate_on_submit():
        password = query_db(f"SELECT password FROM user WHERE email = '{form.email.data}'")[0][0]
        if password != None and form.password.data == password:
            #LOGIN
            user = query_db(f"SELECT * FROM user WHERE email = \'{form.email.data}\'")[0]
            session['user_id'] = user[0]
            active_user = (f"UPDATE user SET status = 'active' WHERE user_id='{session['user_id']}'")
            insert_db(active_user)
            return redirect(url_for('home'))
        else:
            flash('Password is inncorrect. Please retype your password.', 'danger')
            return redirect(url_for('activate'))
    return render_template('activate.html', form=form)
    #     user = User.query.filter_by(email=form.email.data).first()
    #     if user and bcrypt.check_password_hash(user.password, form.password.data):
    #         login_user(user)
    #         user.active = "Active"
    #         db.session.commit()
    #         return redirect(url_for('home'))
    #     else:
    #         flash('Password is inncorrect. Please retype your password.', 'danger')
    #         return redirect(url_for('activate'))
    # return render_template('activate.html', form=form)

@app.route("/activateask", methods=["GET", "POST"])
def activateask():
    return render_template('activateask.html')


@app.route("/logout")
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/review', methods=["GET", "POST"])
def review():
    if request.method == 'GET': 
        edit = request.args.get('edit')
        name = request.args.get('name')
        rating = request.args.get('rating')
        message = request.args.get('message')
        transaction_id = request.args.get('id')
        print("trans_id", transaction_id)
        pre_tran = query_db(f"SELECT * FROM previous_transactions WHERE Transaction_Id={transaction_id}")[0]
        cartItems = ast.literal_eval(pre_tran[1])
        for i in cartItems: 
            if i['prod_name'] == name:
                prod_name = i['prod_name']
                prod_quantity = i['prod_quantity']
                prod_price = i['prod_price']
                img = i['img']
        if edit == 'true':
            # review = Review.query.filter_by(prod_name = prod_name, transaction_id = transaction_id, user_id = current_user.id).first()
            # review.rating = rating 
            # review.comment = message 
            insert_db(f"UPDATE review set rating = \'{int(rating)}\' WHERE prod_name= \'{name}\' AND transaction_id = {transaction_id}")
            insert_db(f"UPDATE review set comment = \'{message}\' WHERE prod_name= \'{name}\' AND transaction_id = {transaction_id}")
        else:
            # review = Review(rating=rating, comment=message, prod_name = prod_name, prod_quantity = prod_quantity, prod_price = prod_price, prod_desc = 'null',img = img,
            #                 date_purchase = pre_tran.transaction_date, transaction_id = transaction_id, user_id = current_user.id)
            insert_db(f"INSERT INTO REVIEW(review_id, rating, comment, prod_name, prod_qty, prod_price, prod_desc, date_purchase, img, Transaction_id, user_id) VALUES(NULL, \'{rating}\', \'{message}\',  \'{prod_name}\',  \'{prod_quantity}\',  \'{prod_price}\',  'null',  \'{pre_tran[2]}\' ,\'{img}\',  \'{transaction_id}\',  \'{session['user_id']}\')")
        return redirect(url_for('myAccount'))

@app.route('/defaultAddress', methods=['GET', 'POST'])
def defaultAddress():
    address = request.args.get('address')
    insert_db(f"Update address_info set default_add = 0 WHERE user_id={session['user_id']}")
    insert_db(f"Update address_info set default_add = 1 WHERE address = \'{address}\' AND user_id={session['user_id']}")
   
@app.route('/defaultCard', methods=['GET', 'POST'])
def defaultCard():
    card = request.args.get('card')
    insert_db(f"Update card_info set default_CARD = 0 WHERE user_id={session['user_id']}")
    insert_db(f"Update card_info set default_CARD = 1 WHERE cardno = \'{card}\' AND user_id={session['user_id']}")
   
# """
# Shop Related Routes 
# """
@app.route('/shop', methods=['GET', 'POST'])
def shop():
    global returnedMessage
    if "user_id" in session:
        orginalCartItems = query_db(f"SELECT * FROM product WHERE user_id = {session['user_id']}")
        if orginalCartItems == None:
            orginalCartItems = []
        id = request.args.get('id')
        itemName = request.args.get('name')
        quantity = request.args.get('quantity')
        delete = request.args.get('delete')
        # product = Product.query.filter_by(prod_name=itemName, user_id = current_user.id)
        if itemName != None:
            product = query_db(f"SELECT * FROM product WHERE prod_name=\'{itemName}\' AND user_id= {session['user_id']}")
        else:
            product = None
        if product != None and quantity != None:
            insert_db(f"UPDATE product set prod_quantity = \'{int(quantity)}\' WHERE prod_name=\'{itemName}\' AND user_id= {session['user_id']}")
            print('changed')
        elif product != None and delete == 'true':
            insert_db(f"DELETE FROM product WHERE prod_name= \'{itemName}\' AND user_id= {session['user_id']}")
        else:
            with open('json_files/product.json', 'r+') as f:
                data = json.load(f)
                for i in data: 
                    if str(i['id']) == id:
                        current = i 
                        # singleProduct = Product(prod_quantity=1, prod_name=current['prod_name'], prod_price=current['prod_price'], prod_desc=current['prod_desc'], img=current['prod_img'], user_id = current_user.id)
                        insert_db(f"INSERT INTO product(productID, prod_quantity, prod_name, prod_price, prod_desc, img, user_id) VALUES(NULL, 1, \'{current['prod_name']}\', \'{current['prod_price']}\' , \'{current['prod_desc']}\',\'{current['prod_img']}\', {session['user_id']});")
        if returnedMessage == None:
            data = refresh()
            for i in data:
                if i['id'] > 12:
                    data.remove(i)
            data.remove(data[-1])
        else: 
            data = returnedMessage["data"]
            returnedMessage = None
        current = session['user_id']
    else:
        if returnedMessage == None:
            data = refresh()
            for i in data: 
                if i['id'] > 12:
                    data.remove(i)
            data.remove(data[-1])
        else: 
            data = returnedMessage["data"]
            returnedMessage = None
        orginalCartItems = []
        current = "None"
    return render_template("shop.html", data = data, cartItems = orginalCartItems, current = current)


@app.route('/searchProduct')
def search():
    name=request.args.get('q')
    global returnedMessage
    returnedMessage = {"status":"success", "data":[]}
    product = query_db(f"SELECT * FROM store_product WHERE prod_name= '{name}' ") 
    if product == None: 
        products = query_db(f"SELECT * FROM store_product")
        filtered_list = []
        for i in products:
            if name.capitalize() in i[2]:
                filtered_list.append(query_db(f"SELECT * FROM store_product WHERE prod_name = \'{i[2]}\'")[0])
        for i in filtered_list:
            returnedMessage["data"].append({"id":i[0], "product_quantity":i[1], "prod_name":i[2], "prod_price":i[3], "prod_desc":i[4], "prod_img":i[6], "status":i[5]})
    else:        
        for i in product: 
            returnedMessage["data"].append({"id":i[0], "product_quantity":i[1], "prod_name":i[2], "prod_price":i[3], "prod_desc":i[4], "prod_img":i[6], "status":i[5]})
    return jsonify(returnedMessage)



@app.route('/single_product/<int:id>')
def single_product(id):
    global returnedMessage
    if "user_id" in session:
        orginalCartItems = query_db(f"SELECT * FROM product WHERE user_id = {session['user_id']}")
        curr = session['user_id']
        if orginalCartItems == None:
            orginalCartItems = []
        product_id = request.args.get('id')
        itemName = request.args.get('name')
        quantity = request.args.get('quantity')
        delete = request.args.get('delete')
        if itemName != None:
            product = query_db(f"SELECT * FROM product WHERE prod_name=\'{itemName}\' AND user_id= {session['user_id']}")
        else:
            product = None
        if product != None and quantity != None:
            insert_db(f"UPDATE product set prod_quantity = \'{int(quantity)}\' WHERE prod_name=\'{itemName}\' AND user_id= {session['user_id']}")
            print('changed')
        elif product != None and delete == 'true':
            insert_db(f"DELETE FROM product WHERE prod_name= \'{itemName}\' AND user_id= {session['user_id']}")
        else:
            with open('json_files/product.json', 'r+') as f:
                data = json.load(f)
                for i in data: 
                    if str(i['id']) == id:
                        current = i 
                        # singleProduct = Product(prod_quantity=1, prod_name=current['prod_name'], prod_price=current['prod_price'], prod_desc=current['prod_desc'], img=current['prod_img'], user_id = current_user.id)
                        insert_db(f"INSERT INTO product(productID, prod_quantity, prod_name, prod_price, prod_desc, img, user_id) VALUES(NULL, 1, \'{current['prod_name']}\', \'{current['prod_price']}\' , \'{current['prod_desc']}\',\'{current['prod_img']}\', {session['user_id']});")
    else:
        orginalCartItems = []
    with open('json_files/product.json', 'r+') as f:
        data = json.load(f)
        for i in data: 
            if i['id'] == id:
                current = i
    reviews = query_db(f'SELECT * FROM product_review WHERE prodID = \'{int(id)}\'')
    if reviews == None:
        reviews = []
    if "user_id" not in session: 
        curr = "None"
    else:
        curr = session['user_id']
    returnedMessage = None
    return render_template("single_product.html", data = current, cartItems = orginalCartItems, current2 = curr, reviews = reviews)

@app.route('/productReview', methods=['GET', 'POST'])
def productReview():
    if request.method == 'GET': 
        id = request.args.get('prodID')
        rating = request.args.get('rating')
        comments = request.args.get('comment')
        user = session['user_id']
        comments = comments.replace('',"")
        email = query_db(f"SELECT email FROM user WHERE user_id = \'{session['user_id']}\' ")[0][0]
        insert_db(f"INSERT INTO product_review(review_id, prodID, rating, comment, email, user_id) VALUES(NULL, \'{id}\', \'{rating}\', \"{comments}\", \"{email}\",\'{user}\')")

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'GET':
        card = None
        user = query_db(f"SELECT * FROM user WHERE user_id = {session['user_id']}")[0]
        cartItems = query_db(f"SELECT * FROM product WHERE user_id = {session['user_id']}")
        cardinfo = query_db(f"SELECT * FROM card_info WHERE default_CARD = 1 AND user_id = {session['user_id']}")
        if cardinfo == None:
            cardinfo = []
        else:
            cardinfo = query_db(f"SELECT * FROM card_info WHERE default_CARD = 1 AND user_id = {session['user_id']}")[0]
        print(cardinfo)
        try:
            card = {'card_name':cardinfo[1], 'cardno':cardinfo[2], 'exp':cardinfo[3], 'year':cardinfo[4]}
        except:
            pass
        address_info = query_db(f"SELECT * FROM address_info WHERE default_add = 1 AND user_id = {session['user_id']}")
        if address_info == None:
            address_info =[]
        else:
            address_info = query_db(f"SELECT * FROM address_info WHERE default_add = 1 AND user_id = {session['user_id']}")[0]
        if cartItems == None:
            cartItems = []
    elif request.method == 'POST':
        return redirect(url_for('myAccount'))
    return render_template('checkout.html', cartItems = cartItems, address = address_info, card = card, user=user)

@app.route('/paymentConfirmation', methods=['GET', 'POST'])
def confirm():
    if request.method == 'GET':
        print('Successful Transaction')
        transaction_list = []
        li = []
        bought_products = query_db(f"SELECT * FROM product WHERE user_id = {session['user_id']}")
        data = refreshAnalytics()
        data2 = refresh()
        total = 0
        for index, i in enumerate(bought_products): 
            transaction_list.append({'prod_name':i[2], 'prod_quantity':i[1], 'prod_price':i[3], 'img':i[5]})
            for y in data:
                if y['name'] == i[2]:  
                    y['stock'] -= int(i[1])  
                    y['count'] += int(i[1])
                    y['amount_earned'] += (int(i[1])*int(i[3]))
            for x in data2:
                 if x['prod_name'] == i[2]:   
                    x['stock'] -= int(i[1])
        with open('json_files/analytics.json', 'w') as f:
                json.dump(data, f)
        with open('json_files/product.json', 'w') as f:
                json.dump(data2, f)
        unique = random.randint(100000000000,999999999999)
        insert_db(f"INSERT INTO previous_transactions(Transaction_id, cartItems, transaction_date, user_id) VALUES(\'{str(unique)}\', \"{str(transaction_list)}\", \'{datetime.now()}\', \'{session['user_id']}\' )")
        insert_db(f"DELETE FROM product WHERE user_id = {session['user_id']}")

# """
# Admin Related Routes
# """

# ## Admin Static Routes ##
@app.route('/admin')
def admin():
    # if session['user_id'] == 3:
        # previousTransaction = PreviousTransactions.query.all()
    # user = query_db(f"SELECT * FROM user WHERE user_id = {session['user_id']}")[0]
    previousTransaction = query_db(f"SELECT * FROM previous_transactions")
    if previousTransaction == None:
        previousTransaction= []
    li = []
    for i in previousTransaction: 
        if i[1] == 'Awaiting order':
            li.append(i)
    number = len(li)
    return render_template('admin/admin.html', previousTransaction = previousTransaction, number = number)
    # else:
    #     return redirect(url_for('home'))

@app.route('/adminAnalytics')
def analytics():
    # user = query_db(f"SELECT * FROM user WHERE user_id = {session['user_id']}")[0]
    data = refreshAnalytics()
    return render_template('admin/adminAnalytics.html', data = data)

@app.route('/stats')
def stats():
    data = refreshAnalytics()
    return jsonify(data)

@app.route('/downloadcsvs')
def downloadcsv():
    data = refreshAnalytics()
    return send_csv(data,
                    "data.csv", ["id", "name","stock","count","amount_earned"]) 

@app.route('/trans')
def trans():
    transactions = query_db(f"SELECT * FROM previous_transactions")
    if transactions == None:
        tran_list = []
    else:
        tran_list = [] 
        for i in transactions:
            total = 0
            date = i[2]
            items = ast.literal_eval(i[1])
            for j in items:
                total += int(j['prod_price']*j['prod_quantity'])
            tran_list.append({'user_id':i[4],'id':i[0], 'total':total ,'date': str(date), 'status': i.status,'items':ast.literal_eval(i.cartItems)})
    return render_template('admin/adminTranList.html', trans = tran_list)

# @app.route('/adminIndvTran')
# def indv():
#     id = request.args.get('id')
#     trans = PreviousTransactions.query.filter_by(transactionId=id).first()
#     transactions = []
#     transactions.append(trans)
#     tran_list = []
#     for i in transactions:
#         total = 0
#         date = i.transaction_date
#         items = ast.literal_eval(i.cartItems)
#         for j in items:
#             total += int(j['prod_price']*j['prod_quantity'])
#         tran_list.append({'user_id':i.user_id,'id':i.transactionId, 'total':total ,'date': str(date), 'status': i.status,'items':ast.literal_eval(i.cartItems)})
#     return render_template('admin/adminTransactions.html', trans = tran_list)
@app.route('/Calendar')
def Calander(): 
    if request.method == 'GET':
        name = request.args.get('ename')
        description = request.args.get('edesc')
        date = request.args.get('edate')
        className = request.args.get('ecolor')
        icon = request.args.get('eicon')
        new_dict = {
        "title": name,
        "description": description,
        "start": date,
        "end": date,
        "className": className,
        "icon" : icon
        }
        if name == None:
            pass
        else:
            with open('json_files/events.json', 'r') as f:
                data = json.load(f)
                data.append(new_dict)
            with open('json_files/events.json', 'w') as f:
                json.dump(data, f)
    return render_template('admin/calander.html')


# @app.route('/announcement')
# def announcement():
#     if request.method == 'GET':
#             name = request.args.get('ann_ename')
#             if name == '':
#                 return redirect(url_for('Calander'))
#             description = request.args.get('anouncements')
#             desc = request.args.get('edesc_ann')
#             start_date = request.args.get('edateStart')
#             end_date = request.args.get('edateEnd')
#             className = request.args.get('ecolor_ann')
#             icon = request.args.get('eicon_ann')
#             new_dict = {
#             "title": name,
#             "anouncement": description,
#             "description":desc,
#             "start": start_date,
#             "end": end_date,
#             "className": className,
#             "icon" : icon
#             }
#             if name == None:
#                 pass
#             else:
#                 with open('json_files/events.json', 'r') as f:
#                     data = json.load(f)
#                     data.append(new_dict)
#                 with open('json_files/events.json', 'w') as f:
#                     json.dump(data, f)
#     return redirect(url_for('Calander'))

@app.route('/events')
def events():
    data = refreshEvents()
    return jsonify(data)

# ## Admin User Section Routes##
# @app.route('/viewUser')
# def viewUser():
#     if current_user.email == 'admin@gmail.com':
#         return render_template('admin/viewUser.html')
#     else:
#         return redirect(url_for('home'))

@app.route('/viewIndividualUser', methods=['GET', 'POST'])
def viewIndividualUser():
    id = request.args.get('id')
    user = query_db(f"SELECT * FROM user WHERE user_id = {id}")[0]
    address = query_db(f"SELECT * FROM address_info WHERE user_id = {id}")
    reviews = query_db(f"SELECT * FROM review WHERE user_id = {id}")
    previous_transactions = query_db(f"SELECT * FROM previous_transactions WHERE user_id = {id}")
    tran_list = []
    if previous_transactions == None:
        previous_transactions = []
    for i in previous_transactions:
        total = 0
        date = i[2]
        items = ast.literal_eval(i[1])
        for j in items:
            total += int(j['prod_price']*j['prod_quantity'])
        tran_list.append({'id':i[0], 'total':total ,'date': str(date), 'status': i[3],'items':ast.literal_eval(i[1])})
    if reviews == None:
        reviews = []
    if address == None: 
        address = []
    return render_template('admin/viewIndividualUser.html', user=user, address=address, reviews=reviews, previous_transactions = tran_list)
    
@app.route('/orderStatus', methods=['GET', 'POST'])
def orderStatus():
    if request.method == 'GET':
        id = request.args.get('id')
        transaction = query_db(f"SELECT * FROM previous_transactions WHERE Transaction_id=\'{id}\'")[0]
        return render_template('admin/orderStatus.html', transaction=transaction)
    else:
        option = request.form['options']
        id = request.form['id']
        insert_db(f"UPDATE previous_transactions set status = \'{option}\' WHERE Transaction_id=\'{id}\'")
        return redirect(url_for('admin'))

@app.route('/listUser')
def listUser():
    users = query_db(f"SELECT * FROM user")
    for i in users:
        if i[3] == 'admin@gmail.com':
            users.remove(i)
    return render_template('admin/usersList.html', users = users)


# @app.route('/deleteUser')
# def deleteUser():
#     if current_user.email == 'admin@gmail.com':
#         id = request.args.get('userId')
#         delete = request.args.get('delete')
#         if id != None and delete == 'true':
#             user = User.query.filter_by(id=int(id)).first()
#             db.session.delete(user)
#             db.session.commit()
#             return redirect(url_for('listUser'))
#     else:
#         return redirect(url_for('home'))

# ## Admin E-commerce Section Routes ##
@app.route('/productList')
def productList():
    data = refresh()
    return render_template('admin/productList.html', data = data)


@app.route('/adminViewproduct', methods=['GET', 'POST'])
def viewProduct():
    id = request.args.get('id')
    with open('json_files/product.json', 'r') as f:
        data = json.load(f)
        for i in data: 
            if i['id'] ==  int(id):
                product = i 
                break 
    review = query_db(f'SELECT * FROM review WHERE prod_name = \'{product["prod_name"]}\'')
    num = 0 if review == None else len(review) 
    with open('json_files/analytics.json', 'r') as f:
        data = json.load(f)
        for i in data: 
            if i['id'] ==  int(id):
                analytics = i 
                break 
    return render_template('admin/productDetail.html', product= product, review = review, analytics = analytics, num=num)

@app.route('/adminAddproduct', methods=['GET', 'POST'])
def adminAdd():
    form = AdminAddProductForm()
    if request.method == "POST":
        image = request.files['image']
        filename = request.files['image'].filename
        print(filename)
        image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
        new_product_name = form.name.data
        new_product_price = form.price.data
        new_product_description = form.description.data
        new_product_id = form.id.data
        new_product_img = f"../static/product_img/{filename}"
        with open('json_files/product.json', 'r') as f:
            data = json.load(f)
            data.append({"id": int(new_product_id), "prod_name": new_product_name, "prod_price": new_product_price, "prod_desc": new_product_description, "prod_img": new_product_img})
        with open('json_files/product.json', 'w') as f:
            json.dump(data, f)
        return redirect(url_for('admin'))
    else:
        with open('json_files/product.json', 'r') as f: 
            data = json.load(f)
            latest_id = len(data)
    return render_template('admin/adminAddProduct.html', latest_id = latest_id+1, form=form)
 
@app.route('/adminUpdateproduct', methods=['POST', 'GET'])
def update():
    form = AdminUpdateProductForm()
    productId = request.args.get('id')
    if request.method == 'POST':
        item_id = form.id.data
        item_name = form.name.data 
        item_desc = form.description.data
        item_price = form.price.data
        image = request.files['image']
        filename = request.files['image'].filename   
        print(filename) 
        if filename:
            image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
        imagesrc = f'../static/product_img/{filename}'
        with open('json_files/product.json', 'r') as f:
            data = json.load(f)
            for i in data:
                if i["id"] == int(item_id):
                    i['prod_img'] = imagesrc
                    i['prod_name'] = item_name
                    i['prod_price'] = int(item_price)
                    i['prod_desc'] = item_desc
                    break
        with open('json_files/product.json', 'w') as f:
            json.dump(data, f)
        return redirect(url_for('admin'))
    elif productId != None:
        with open('json_files/product.json') as f:
            data = json.load(f)
            for i in data: 
                if i["id"] == int(productId):
                    product = i
                    break
            f.close()
        return render_template('admin/adminUpdateProduct.html', product = product, form=form)
    else:
        with open('json_files/product.json') as f:
            data = json.load(f)
            for i in data: 
                if i["id"] == 1:
                    product = i
                    break
        return render_template('admin/adminUpdateProduct.html', product = product, form=form)


@app.route('/addStock', methods=['POST', 'GET'])
def stock():
    if request.method == 'GET':
        id = request.args.get('id')
        data = refresh()
        for i in data: 
            if i['id'] == int(id):
                current = i
                break
        return render_template('admin/adminStock.html', data = current)
    else:
        with open('json_files/product.json', 'r') as f:
                data = json.load(f)
                productId = request.args.get('id')
                cun = request.form['quant[1]']
                for i in data: 
                    if i["id"] == int(productId):
                        i['stock'] += int(cun)
                        break
        with open('json_files/product.json', 'w') as f:
            json.dump(data, f)

        with open('json_files/analytics.json', 'r') as f:
                data = json.load(f)
                productId = request.args.get('id')
                cun = request.form['quant[1]']
                for i in data: 
                    if i["id"] == int(productId):
                        i['stock'] += int(cun)
                        break
        with open('json_files/analytics.json', 'w') as f:
            json.dump(data, f)
        return redirect(url_for('admin'))


@app.route('/delete', methods=['POST', 'GET'])
def delete():  
    form = AdminUpdateProductForm()
    productId = request.args.get('id')
    if request.method == 'POST':
        with open('json_files/product.json', 'r') as f:
            data = json.load(f)
            productId = request.args.get('id')
            for i in data: 
                if i["id"] == int(productId):
                    data.remove(i)
                    break
        with open('json_files/product.json', 'w') as f:
            json.dump(data, f)
        return redirect(url_for('admin'))
    else:
        with open('json_files/product.json', 'r+') as f:
            data = json.load(f)
            productId = request.args.get('id')
            for i in data: 
                if i["id"] == int(productId):
                    product = i
                    break
            return render_template('admin/adminDeleteProduct.html', product=product, form=form)


# """Reset Password token routes"""

def send_reset_email(user):
    token = get_reset_token(user)
    print(token)
    msg = Message('Password Reset Request', sender='testemailnyp@gmail.com', recipients=[user[3]])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

# If you did not make this request then simply ignore this email and no changes will be made.
# '''
    mail.send(msg)
   
# @app.route("/reset_password", methods=['GET', 'POST'])
# def reset_request():
#     form = RequestResetForm()
#     if form.validate_on_submit():
#         user = query_db(f"SELECT * FROM user WHERE email = \'{form.email.data}\'")
#         if user == None:
#             return redirect(url_for('home'))
#         else:
#             user = user[0]
#         send_reset_email(user)
#         flash('An email has been sent with instructions to reset your password.', 'info')
#         return redirect(url_for('login'))
#     return render_template('reset_request.html', title='Reset Password', form=form)

# @app.route("/reset_password/<token>", methods=['GET', 'POST'])
# def reset_token(token):
#     user = verify_reset_token(token)
#     print(user)
#     if user is None:
#         flash('That is an invalid or expired token', 'danger')
#         return redirect(url_for('reset_request'))
#     form = ResetPasswordForm()
#     if form.validate_on_submit():
#         insert_db(f"UPDATE user set password = \'{form.password.data}\' WHERE user_id=\'{int(user)}\'")
#         flash('Your password has been updated! You are now able to log in', 'success')
#         return redirect(url_for('login'))
#     return render_template('reset_token.html', title='Reset Password', form=form)




# @app.route('/resetpass', methods=['GET', 'POST'])
# def resetpass():
#     form = PasswordForm()
#     return render_template('resetpass.html', form= form )

#Reset Password Security Form
@app.route('/ResetPassword', methods=['GET', 'POST'])
def resetpassword():
    form = ResetPassForm()
    if request.method == 'POST':
        email = form.email.data
        securityAnswer = form.securityAnswer.data
        new_password = form.password.data
        confirm_password = form.confirm_password
        valid_user = query_db(f"SELECT * FROM user WHERE email= \'{email}\' AND security_answer=\'{securityAnswer}\'")
        if valid_user != None:
            insert_db(f"UPDATE user SET password = \'{new_password}\' WHERE email=\'{email}\' AND security_answer = \'{securityAnswer}\'")
            return redirect(url_for('login'))
        else:
            flash('Wrong security answer', 'danger')
            return redirect(url_for('resetpassword'))
    else:
        email = request.args.get('email')
        if email != None:
            user = query_db(f"SELECT * FROM user WHERE email = \'{email}\'")
            if user == None:
                return "None"
            else:
                return user[0][6]
    return render_template('forgetPassword.html', form= form )    

# """Error Handling Routes"""

# @app.errorhandler(404)
# def page_not_found(e):
#     # note that we set the 404 status explicitly
#     return render_template('pageNotFound.html'), 404

# @app.errorhandler(500)
# def page_not_found500(x):
#     return render_template('feedbackError.html'), 500


# @app.route('/forgetpass', methods=['GET', 'POST'])
# def forgetpass():

#     #if current_user.is_authenticated:
#         #return redirect(url_for('home'))
        
#     form = PasswordForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).first()
#         if user:
#             port = 465  
#             smtp_server = "smtp.gmail.com"
#             sender_email = "testemailnyp@gmail.com"  
#             receiver_email = form.email.data  
#             password = "Valentia01"

#             message = MIMEMultipart("alternative")
#             message["Subject"] = "multipart test"
#             message["From"] = sender_email
#             message["To"] = receiver_email

#             text = """\
#             Hi,
#             How are you?
#             Real Python has many great tutorials:
#             www.realpython.com"""
#             html = """\
#             <html>
#             <body>
#             <h1>Hello!</h1>
#                 <p>You are receiving this email because we received a password reset<br>
#                 request for your account.<br>
#                 <a href="http://www.realpython.com">Reset Password</a>
#                 </p>
#             </body>
#             </html>
#             """

#             part1 = MIMEText(text, "plain")
#             part2 = MIMEText(html, "html")

#             message.attach(part1)
#             message.attach(part2)
           
#             # message = """\
#             # Subject: Change your password

#             # Please click on this link to change your password."""

#             context = ssl.create_default_context()
#             with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
#                 server.login(sender_email, password)
#                 server.sendmail(sender_email, receiver_email, message.as_string())
#     return render_template('forgetpass.html', title='Login', form=form)

# @app.route('/resetpass', methods=['GET', 'POST'])
# def resetpass():
#     form = ResetForm()
#     if form.validate_on_submit():
#         hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
#         current_user.password = hashed_password
#         db.session.commit()

#     return render_template('resetpass.html', form=form)


path = os.getcwd()+"/controllers"
list_of_files = {}

@app.route('/list')
def tree():
    for filename in os.listdir(path):
        list_of_files[filename] = "http://127.0.0.1:5000/"+filename
    return list_of_files




