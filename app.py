from flask import Flask, render_template, flash, redirect, request, url_for, session, logging
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
app.debug = True

# MySQL setup
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '92702689'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init MySQL
mysql = MySQL(app)


Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')


# Authentication function
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login first !', 'danger')
            return redirect(url_for('login'))
    return wrap



@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    # Create cursor
    cur = mysql.connection.cursor()
    # Execute
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles = articles)
    else:
        msg = 'No articles found !'
        return render_template('articles.html', mas = msg)


@app.route('/articles/<string:id>/')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()
    # Execute
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()
    if result > 0:
        return render_template('article.html', article = article)
    else:
        msg = 'Not found !'
        return render_template('article.html', mas = msg)


# Register Form
class RegistrationForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=50)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('password', [validators.DataRequired(),validators.EqualTo('confirm', message='Passwords do not match !')])
    confirm = PasswordField('Confirm Password')



@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        mysql.connection.commit()
        cur.close()

        flash('You are now registered !', 'success')
        return redirect(url_for('index'))
    return render_template('register.html', form = form)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username

        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            data = cur.fetchone()
            password = data['password']

        # Compare the passwords
            if sha256_crypt.verify(password_candidate, password):
                # app.logger.info('Password Matched !')
                session['logged_in'] = True
                session['username'] = username
                flash("You are logged in !", 'success')
                return redirect(url_for('dashboard'))

            else:
                error = "Password not found !"
                return render_template('login.html', error=error)


        else:
            error = "Username not found !"
            return render_template('login.html', error=error)

    return render_template('login.html')


# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash("You are Logged out !")
    return redirect(url_for('login'))


# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()
    # Execute
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles = articles)
    else:
        msg = 'No articles found !'
        return render_template('dashboard.html', mas = msg)


# Article form class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max = 200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Article
@app.route('/add_article', methods = ['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES (%s, %s, %s)", (title, body, session['username']))

        mysql.connection.commit()
        cur.close()

        # Flash messsage
        flash("Your article has been published !", 'success')
        return redirect(url_for('articles'))
    return render_template('add_article.html', form=form)


# Edit Article
@app.route('/edit_article/<string:id>/', methods = ['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()
    # Get articles by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()

    form = ArticleForm(request.form)

    form.title.data = article['title']
    form.body.data = article['body']


    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create cursor
        # cur = mysql.connection.cursor()

        # Execute
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id = %s", (title, body, id))

        mysql.connection.commit()

        cur.close()

        # Flash messsage
        flash("Your article has been Updates !", 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)




if __name__ == '__main__':
    app.secret_key ='secret123'
    app.run()
