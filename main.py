from flask import Flask, render_template, redirect, url_for, flash ,request ,session ,abort
from functools import wraps
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy  
from sqlalchemy.orm import relationship 
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm , NewUser, NewComment
from flask_gravatar import Gravatar

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

##CONFIGURE TABLES

class Comments(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer,  primary_key=True)
    comment = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    blog_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    
    comment_author = relationship('Users' , back_populates = 'user_comments')
    comment_blog = relationship('BlogPost' , back_populates='blog_comments')


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    # comment_id = db.Column(db.Integer, db.ForeignKey('Comments.id'))
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    
    blog_author = relationship('Users' , back_populates = 'blog_posts')
    blog_comments = relationship('Comments' , back_populates='comment_blog')

       
class Users(UserMixin , db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250) , unique=True , nullable=False)
    password = db.Column(db.String(250)  , nullable=False)
    name = db.Column(db.String(250) , nullable=False)
    
    blog_posts = relationship('BlogPost' ,back_populates = 'blog_author' )
    user_comments = relationship('Comments' ,back_populates = 'comment_author' )
    

def admin_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.id==1:
            return func(*args, **kwargs)
        return abort(403)
    return wrapper
        

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    
    # print(current_user.id)
    
    if current_user.is_active:
        # return render_template("index.html", all_posts=posts ,logged_in = True , admin= True )
        return render_template("index.html", all_posts=posts ,logged_in = True , user = current_user)
    else:
        # if current_user.is_active:
        #     return render_template("index.html", all_posts=posts ,logged_in = True )
        return render_template("index.html", all_posts=posts , logged_in = False )
           


@app.route('/register' ,methods = ['GET' , 'POST'])
def register():
    form = NewUser()
    if form.validate_on_submit() and request.method == 'POST':   
        name = form.name.data
        email = form.email.data
        password = generate_password_hash(form.password.data)
        # is_admin = 
        
        # Checking if email exist in database or not
        user = Users.query.filter_by(email=email).first()
        print(user)
        if not user:                                    # user does not exist in database
            new_user = Users(email = email , password = password ,name = name)
            db.session.add(new_user)
            db.session.commit()
            # Login
            user_obj = load_user(new_user.id)
            login_user(user_obj)
            return redirect(url_for('get_all_posts'))
        else:
            flash("You've already signed up with that email, login in instead!")
            return redirect(url_for('login'))
    return render_template("register.html", form = form)


@app.route('/login',methods = ['GET' , 'POST'])
def login():
    form = NewUser()
    del form.name                                                   # Deletes the form field NAme
    error = None
    if form.validate_on_submit() and request.method == 'POST':   
        email_ = form.email.data
        password_ = form.password.data
        user = Users.query.filter_by(email = email_).first()
        if user:
            password_ = form.password.data
            if check_password_hash(user.password , password_):
                user_obj = load_user(user.id)
                login_user(user_obj)
                print(current_user.id)
                return redirect(url_for('get_all_posts'))
            else:
                error = 'Invalid Password'  
        else:
            error = 'User does not Exist Please register' 
            # return redirect(url_for('register'))
    return render_template("login.html" , form = form, error = error)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>",methods = ['GET' , 'POST'])
def show_post(post_id):
    form = NewComment() 
    error = ''
    requested_post = BlogPost.query.get(post_id)
    if current_user.is_active and form.validate_on_submit():
        comment = form.comment.data
        new_comment = Comments(comment = comment , comment_author = current_user, comment_blog = requested_post)
        db.session.add(new_comment)
        db.session.commit()
        return render_template("post.html", post=requested_post , comments = Comments.query.all()  ,logged_in = True , user = current_user , form = form , error = error)
    elif form.validate_on_submit():
        error = 'Please Login'    
        return render_template("post.html", post=requested_post , comments = Comments.query.all(), form = form, error = error)
    elif current_user.is_active:
        return render_template("post.html", post=requested_post , comments = Comments.query.all()  ,logged_in = True , user = current_user , form = form , error = error)
    return render_template("post.html", post=requested_post , comments = Comments.query.all(), form = form, error = error)


@app.route("/about")
def about():
    if current_user.is_active:
        return render_template("about.html", logged_in = True)
    else:
        return render_template("about.html")


@app.route("/contact")
def contact():
    if current_user.is_active:
        return render_template("contact.html", logged_in = True)
    else:
        return render_template("contact.html")
        


@app.route("/new-post", methods = ["GET" ,"POST"])
@login_required
@admin_only
def add_new_post():
    # if current_user.id == 1:
        form = CreatePostForm()
        user = Users.query.get(current_user.id)
        
        print(user.id)
        if form.validate_on_submit() and request.method=='POST' :
            new_post = BlogPost(
                title=form.title.data,
                subtitle=form.subtitle.data,
                date=date.today().strftime("%B %d, %Y"),
                body=form.body.data,
                img_url=form.img_url.data,
                blog_author=current_user           # adding relation between author and Blog
            )
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for("get_all_posts"))
        return render_template("make-post.html", form=form)
    # else:
    #     return  abort(403)    #"<p>You are not authorised to Create the post, login as admin</p>"

@app.route("/edit-post/<int:post_id>")
@login_required
@admin_only
def edit_post(post_id):
    # if current_user.id == 1:
        post = BlogPost.query.get(post_id)
        edit_form = CreatePostForm(
            title=post.title,
            subtitle=post.subtitle,
            img_url=post.img_url,
            author=post.author,
            body=post.body
        )
        if edit_form.validate_on_submit():
            post.title = edit_form.title.data
            post.subtitle = edit_form.subtitle.data
            post.img_url = edit_form.img_url.data
            post.author = edit_form.author.data
            post.body = edit_form.body.data
            db.session.commit()
            return redirect(url_for("show_post", post_id=post.id))

        return render_template("make-post.html", form=edit_form)
    # else:
    #     return abort(403)    #"<p>You are not authorised to edit this post, login as admin</p>"

@app.route("/delete/<int:post_id>")
@login_required
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug= True)
    


    # flash('You are not authorised to delete the post, login as admin')
    # return redirect(url_for('get_all_posts'))
        
# @app.route('/a')
# def create():
#     blog = BlogPost(1, 1,'ankit', 'The Life of Cactus' , 'Who knew that cacti lived such interesting lives.' , 'October 20, 2020', """<p>Nori grape silver beet broccoli kombu beet greens fava bean potato quandong celery.</p>

# <p>Bunya nuts black-eyed pea prairie turnip leek lentil turnip greens parsnip.</p>

# <p>Sea lettuce lettuce water chestnut eggplant winter purslane fennel azuki bean earthnut pea sierra leone bologi leek soko chicory celtuce parsley j&iacute;cama salsify.</p>
# """ , 'https://images.unsplash.com/photo-1530482054429-cc491f61333b?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1651&q=80' )
#     db.session.add(blog)
#     db.session.commit()


# @app.route('/b')
# def create():
#     user = Users(1,'ankit@gmail.com' , generate_password_hash('12345678') , 'ankit')
#     db.session.add(user)
#     db.session.commit()


