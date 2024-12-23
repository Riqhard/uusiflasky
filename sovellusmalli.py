import os
import click
from flask_migrate import Migrate
from app import create_app, db
from app.models import User, Role

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)
# Tämä, jos tauluja eikä migraatiotiedostoja ole käytettävissä
# db.create_all()
# Tämä, jos Flask-komentorivi ei ole käytössä roolien lisäämiseen
# with app.app_context():
    # query = db.session.query(Role).first()
    # if not query:
        # print("query: "+str(query))
        # Role.insert_roles()

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)


@app.cli.command()
@click.argument('test_names', nargs=-1)
def test(test_names):
    """Run the unit tests."""
    import unittest
    if test_names:
        tests = unittest.TestLoader().loadTestsFromNames(test_names)
    else:
        tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)