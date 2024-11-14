import random
from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from flask import current_app as app
from . import db
from .models import User


def users(count=100):
    fake_users = []
    fake = Faker(['fi_FI'])
    fake.unique.clear()
    i = 0
    while i < count:
        u = User(email=fake.unique.email(),
                 name=fake.name(),
                 username=fake.unique.user_name(),
                 # Testaa IntegrityError-tilanne:
                 # username = 'tupla',
                 password='password',
                 confirmed=random.choice([True, False]),
                 # name=fake.name(),
                 # location=fake.city(),
                 # about_me=fake.text(),
                 # member_since=fake.past_date()
                 )
        # if u.username in [user.username for user in fake_users]:
        #    continue     
        # with db.session.no_autoflush:, ei toimi, 
        # joten se on korvattu alustuksella db = SQLAlchemy(session_options={"autoflush": False})    
        
        db.session.add(u)
        fake_users.append(u)
        # print("fake_user: "+str(u))
        app.logger.info(f"fake_user: {u}")  
        i += 1

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        fake_users = []
        # print("virhe: useita samoja käyttäjätunnuksia")
        app.logger.error("virhe: useita samoja käyttäjätunnuksia")
    except Exception as e:
        db.session.rollback()
        fake_users = []
        # print(f"An error occurred: {e}")
        app.logger.error(f"An error occurred: {e}")
    # print("fake_users: "+str(fake_users))
    return fake_users