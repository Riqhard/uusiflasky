from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager
from datetime import datetime

class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16
    
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                        Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                            Permission.WRITE, Permission.MODERATE,
                            Permission.ADMIN],
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm


    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    # Huom. Oletuarvon migraatiota ei ole vielä testattu
    # lambda: current_app.config['TIMEZONE_FUNCTION']())
    # member_since = db.Column(db.DateTime(), server_default=db.func.now())
    member_since = db.Column(db.DateTime(), default=lambda: current_app.config['GET_TIME']())
    last_seen = db.Column(db.DateTime())
    img = db.Column(db.String(64))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(255))
    active = db.Column(db.Boolean, default=True,server_default='1')
    confirmed = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['SOVELLUSMALLI_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()


    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token,max_age=3600)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'reset': self.id})

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token,max_age=3600)
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token,max_age=3600)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def ping(self):
        # self.last_seen = datetime.now()
        self.last_seen = current_app.config['GET_TIME']()
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f'<User {self.username}, email {self.email}>'

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref='recipes')
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    img = db.Column(db.String(64))  # New column for image filename
    version = db.Column(db.Integer, nullable=False, default=1)  # New column for version
    original_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=True)  # New column for original recipe id
    description = db.Column(db.Text, nullable=False)  # New column for description

    def create_new_version(self, title, ingredients, instructions, img=None):
        new_version = Recipe(
            title=title,
            ingredients=ingredients,
            instructions=instructions,
            user_id=self.user_id,
            img=img,
            version=self.version + 1,
            original_id=self.original_id or self.id,
            description=self.description  # Include description in new version
        )
        db.session.add(new_version)
        db.session.commit()
        return new_version

    def __repr__(self):
        return f'<Recipe {self.title}>'
    
class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    amount = db.Column(db.String(64), nullable=False, index=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'))

    def __repr__(self):
        return f'<Ingredient {self.name}>'
    
class Instruction(db.Model):
    __tablename__ = 'instructions'
    id = db.Column(db.Integer, primary_key=True)
    step = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'))

    def __repr__(self):
        return f'<Ingredient {self.name}>'
