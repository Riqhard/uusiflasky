from flask_wtf import FlaskForm
from wtforms import BooleanField, FileField, StringField, SubmitField, HiddenField, SelectField, DateTimeLocalField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, Regexp, Optional
from wtforms import ValidationError
from flask_wtf.file import FileAllowed
from app.models import User
from flask_login import current_user
from flask import request
from werkzeug.datastructures import FileStorage


def check_image_size(form, field, max_file_size = 1024 * 1024):  # 1 MB oletusarvo
    file: FileStorage = field.data 
    file_size = 0
    if file:
        # Method 1: Using content_length if available
        file_size = file.content_length
        # Method 2: Calculate the size if content_length is None
        if not file_size:
            # Move to end of the stream to get the size
            file.stream.seek(0, 2)  # Seek to end of the file
            file_size = file.stream.tell()
            file.stream.seek(0)  # Reset stream pointer to beginning
    print("filename:" + str(file.filename))
    print("file_size:" + str(file_size) + ", MAX_FILE_SIZE:" + str(max_file_size))
    if file and file_size > max_file_size:
        raise ValidationError(f"Tiedoston koko ei saa ylittää {max_file_size / (1024 * 1024)} MB.")

class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')

class ProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), ])
    email = StringField('Email', validators=[DataRequired(), Length(5, 64), Email()])
    username = StringField('Username', validators=[ 
        DataRequired(), 
        Length(1, 64), 
        Regexp(r"^[a-zåäöA-ZÅÄÖ '_.\-]+$", 0, 'Usernames must have only letters, numbers, dots or underscores')
        ])
    location = StringField('Location', validators=[DataRequired()])
    about_me = StringField('About me', validators=[DataRequired()])
    file = FileField('Profile picture')
    img = HiddenField("Img") 
    submit = SubmitField('Save profile')    

    def __init__(self, *args, max_file_size = None, **kwargs):    
        super().__init__(*args, **kwargs)
        # Lisää tiedostokoon tarkistus, jos max_file_size annetaan
        if max_file_size:
            self.file.validators = [
                FileAllowed(['png', 'jpg', 'jpeg', 'gif'], 'Images only!'),
                lambda form, field: check_image_size(form, field, max_file_size)
                ]

    def validate_email(self,field):
        new = field.data.lower()
        if current_user.email != new and User.query.filter_by(email=new).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        # Huom. MySQL on case-insensitive, joten vertailu on case-insensitive
        new = field.data
        if current_user.username != new and User.query.filter_by(username=new).first():
            raise ValidationError('Username already in use.')

    

class ProfileFormAdmin(FlaskForm):
    id = HiddenField('Id')
    name = StringField('Name', render_kw={'disabled': True})
    username = StringField('Username', render_kw={'disabled': True})
    email = StringField('Email', render_kw={'disabled': True})
    location = StringField('Location', render_kw={'disabled': True})
    about_me = StringField('About me', render_kw={'disabled': True})
    member_since = DateTimeLocalField('Member since', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    last_seen = DateTimeLocalField('Last seen', render_kw={'disabled': True})
    role_id = SelectField('Role', coerce=int, choices=[(1, 'User'), (2, 'Moderator'), (3, 'Administrator')])
    active = BooleanField('Active')
    submit = SubmitField('Save profile')    

class LatestRepicesForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    instructions = TextAreaField('Instructions', validators=[DataRequired()])
    ingredients = TextAreaField('Ingredients', validators=[DataRequired()])
    submit = SubmitField('Add Recipe')
    
