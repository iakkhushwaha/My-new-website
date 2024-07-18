from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField , EmailField
from wtforms.validators import DataRequired, URL , Length
from flask_ckeditor import CKEditorField

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class NewUser(FlaskForm):
    name = StringField(label='Name' , validators=[DataRequired()])
    email = EmailField(label='Email' , validators=[DataRequired()])
    password = PasswordField(label='Password' , validators=[DataRequired(), Length(min=8 ,max=16)])
    submit = SubmitField("Submit Post")
    
class NewComment(FlaskForm):
    comment = CKEditorField('Comment')
    sumbit = SubmitField('Submit')