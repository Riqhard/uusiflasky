from flask import render_template, request, flash, redirect, url_for, jsonify, current_app, send_from_directory
from flask_login import login_required,current_user
from ..decorators import admin_required,debuggeri
from ..models import User,  Ingredient, Instruction, Recipe
from .forms import ProfileForm,ProfileFormAdmin,RecipeForm
from app import db
from . import main
from sqlalchemy import text
import os
from werkzeug.utils import secure_filename

@debuggeri
def shorten(filename):
    name, extension = os.path.splitext(filename)
    # print("SHORTEN:"+name+" "+extension)
    length = 64 - len(extension)
    return name[:length] + extension

'''def allowed_file(filename):
    app = current_app._get_current_object()
    ALLOWED_EXTENSIONS = app.config['ALLOWED_EXTENSIONS']
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
'''

def tee_kuvanimi(id,kuva):
    return str(id) + '_' + kuva

def poista_vanha_kuva(id,kuva):
    kuvanimi = tee_kuvanimi(id,kuva)
    app = current_app._get_current_object()
    KUVAPOLKU = app.config['KUVAPOLKU']
    filename = os.path.join(KUVAPOLKU, kuvanimi)
    print("POISTETAAN:"+filename)
    try:
        os.remove(filename)
    except Exception as e:
        app.logger.info(e)
        return False
    else:   
        return True

@main.route('/')
def index():
    latest_recipes = Recipe.query.order_by(Recipe.created_at.desc()).limit(5).all()
    for recipe in latest_recipes:
        recipe.user = User.query.get(recipe.user_id)
    return render_template('index.html', latest_recipes=latest_recipes)

@main.route('/img/')
@main.route('/img/<path:filename>')
def img(filename = None):
    app = current_app._get_current_object()
    KUVAPOLKU = app.config['KUVAPOLKU']
    if filename is None:
        return send_from_directory('static','default_profile.png')
    return send_from_directory(KUVAPOLKU, filename)

@main.route('/edit_profile', methods=['GET', 'POST'])  
@login_required
def edit_profile():
    user = User.query.get_or_404(current_user.id)
    form = ProfileForm(obj=user, max_file_size=current_app.config.get('MAX_FILE_SIZE', 1 * 1024 * 1024))
    app = current_app._get_current_object()
    KUVAPOLKU = app.config['KUVAPOLKU']
    kuvanimi = ''
    # Huom. omat validointifunktiot ProfileForm-luokassa
    # Huom. kuvan nimen tallennus tietokantaan perustuu img-kenttään,
    # kuvatiedoston tallennus palvelimelle files-kenttään. Img-kenttä
    # tarvitaan, 1) jotta muuttamaton kuva säilyy, sillä sitä ei
    # tule valituksi files-kenttään lomakkeelta ja 2) kuvan poistaminen
    # ilmenee tyhjästä img-kentästä.
    if form.validate_on_submit():
        # check if the post request has the file part
        print("FILES:"+str(request.files))
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            kuvanimi = file.filename
            print("file.filename:"+kuvanimi)
            if current_user.img and kuvanimi != current_user.img:
                poista_vanha_kuva(current_user.id,current_user.img)
            # if kuvanimi and allowed_file(kuvanimi):
            if kuvanimi:    
                # Lomakkeelta lähetettynä paikallinen tallennus,
                # S3- ja Azure-tallennus tehty erikseen Javascriptillä
                kuvanimi = shorten(secure_filename(kuvanimi))
                filename = tee_kuvanimi(current_user.id,kuvanimi)
                file.save(os.path.join(KUVAPOLKU, filename))
        form.populate_obj(user)
        print("KUVANIMI:"+kuvanimi)
        # Huom. Alkuperäinen kuvan nimi on lyhentämätön ja se tallenetaan
        # lyhennettynä tietokantaan ilman id-tunnistetta, kuvatiedosto
        # tallennetaan id-tunnisteella, jotta se on yksilöllinen.
        print("IMG:"+user.img)
        user.img = kuvanimi if kuvanimi else user.img
        # db.session.add(current_user._get_current_object())
        try:
            db.session.commit()
            flash('Your profile has been updated.', 'success')
            return redirect(url_for('.user', username=user.username))
        except Exception as e:
            db.session.rollback()
            flash('Virhe tallennuksessa.', 'danger')
            app.logger.info(e)
            kuva = tee_kuvanimi(user.id, kuvanimi) if kuvanimi else ''
            return render_template('edit_profile.html', form=form,kuva=kuva)
    kuva = tee_kuvanimi(user.id,user.img) if user.img else ''  
    print("kuva:"+kuva) 
    return render_template('edit_profile.html', form=form,kuva=kuva,API_KEY=app.config.get('GOOGLE_API_KEY'))


@main.route('/edit_profile_admin', methods=['GET', 'POST']) 
@login_required
@admin_required
def edit_profile_admin():
    app = current_app._get_current_object()
    user = User.query.get_or_404(request.args.get('id'))
    # Tulosta MySQL-kyselyn arvot
    for key, value in vars(user).items():
        print(f'{key}: {value}')   
    kuva = tee_kuvanimi(user.id,user.img) if user.img else ''
    form = ProfileFormAdmin(obj=user)
    print("FORM:"+str(form))
    if form.validate_on_submit():
        form.populate_obj(user)
        try: 
            db.session.commit()
            flash('Käyttäjän tiedot on päivitetty.', 'success')
            return redirect(url_for('.users'))
        except Exception as e:
            db.session.rollback()
            flash('Virhe tallennuksessa.', 'danger')
            current_app.logger.info(e)
            return render_template('edit_profile_admin.html', form=form,user=user,kuva=kuva,API_KEY=app.config.get('GOOGLE_API_KEY'))
    return render_template('edit_profile_admin.html', form=form,user=user,kuva=kuva,API_KEY=app.config.get('GOOGLE_API_KEY'))
    
@main.route('/user', methods=['GET'])
@login_required
def user(): 
    kuva = tee_kuvanimi(current_user.id,current_user.img) if current_user.img else ''
    return render_template('user.html',user=current_user,kuva=kuva,API_KEY=current_app.config.get('GOOGLE_API_KEY'))   

@main.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users():
    if request.form.get('painike'):
        users = request.form.getlist('users')
        if len(users) > 0:
            query_start = "INSERT INTO users (id,active) VALUES "
            query_end = " ON DUPLICATE KEY UPDATE active = VALUES(active)"
            query_values = ""
            active = request.form.getlist('active')
            for v in users:
                if v in active:
                    query_values += "("+v+",1),"
                else:
                    query_values += "("+v+",0),"
                # query_values += "("+v+"," + ("1" if v in active else "0") + "),"        
                # query_values += f"({v}, {'1' if v in active else '0'}),"
            query_values = query_values[:-1]
            query = query_start + query_values + query_end
            # print("\n"+query+"\n")
            # result = db.session.execute('SELECT * FROM my_table WHERE my_column = :val', {'val': 5})
            db.session.execute(text(query))
            db.session.commit()
            # return query
            #return str(request.form.getlist('users')) + \
            #       "<br>" + \
            #        str(request.form.getlist('active'))
        else:
            flash("Käyttäjälista puuttuu.")
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.name).paginate(
        page=page, per_page=current_app.config.get('FS_POSTS_PER_PAGE', 25),
        error_out=False)
    lista = pagination.items
    return render_template('users.html',users=lista,pagination=pagination,page=page)

@main.route('/poista', methods=['GET', 'POST'])
@login_required
@admin_required
def poista():
    # print("POISTA:"+request.form.get('id'))
    user = User.query.get(request.form.get('id'))
    if user is not None:
        db.session.delete(user)
        db.session.commit()
        flash(f"Käyttäjä {user.name} on poistettu")
        return jsonify(OK="käyttäjä on poistettu.")
    else:
        return jsonify(virhe="käyttäjää ei löydy.")




@main.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        img_filename = None
        if form.img.data:
            img_filename = secure_filename(form.img.data.filename)
            img_filename = shorten(img_filename)
            img_path = os.path.join(current_app.config['KUVAPOLKU'], img_filename)
            form.img.data.save(img_path)
        ingredients = []
        for i in range(50):
            ingredient_field = getattr(form, f'ingredient_{i}')
            if ingredient_field.data:
                ingredients.append(ingredient_field.data)
        ingredients_str = '; '.join(ingredients)
        
        instructions = []
        for i in range(50):
            instruction_field = getattr(form, f'instruction_{i}')
            if instruction_field.data:
                instructions.append(instruction_field.data)
        instructions_str = '; '.join(instructions)
        
        recipe = Recipe(
            title=form.title.data,
            description=form.description.data,
            ingredients=ingredients_str,
            instructions=instructions_str,
            user_id=current_user.id,
            img=img_filename,
            version=1,
            original_id=None
        )
        db.session.add(recipe)
        db.session.commit()
        flash('Uusi resepti lisätty.', 'success')
        return redirect(url_for('main.index'))
    return render_template('add_recipe.html', form=form)

@main.route('/add_recipe_version/<int:id>', methods=['GET', 'POST'])
@login_required
def add_recipe_version(id):
    original_recipe = Recipe.query.get_or_404(id)
    form = RecipeForm(obj=original_recipe)
    if form.validate_on_submit():
        img_filename = None
        if form.img.data:
            img_filename = secure_filename(form.img.data.filename)
            img_filename = shorten(img_filename)
            img_path = os.path.join(current_app.config['KUVAPOLKU'], img_filename)
            form.img.data.save(img_path)
        
        ingredients = []
        for i in range(50):
            ingredient_field = getattr(form, f'ingredient_{i}')
            if ingredient_field.data:
                ingredients.append(ingredient_field.data)
        ingredients_str = '; '.join(ingredients)
        
        instructions = []
        for i in range(50):
            instruction_field = getattr(form, f'instruction_{i}')
            if instruction_field.data:
                instructions.append(instruction_field.data)
        instructions_str = '; '.join(instructions)
        
        new_version = original_recipe.create_new_version(
            title=form.title.data,
            ingredients=ingredients_str,
            instructions=instructions_str,
            img=img_filename,
            description=form.description.data  # Include description in new version
        )
        flash('Uusi versio luotu.', 'success')
        return redirect(url_for('main.recipe', id=new_version.id))
    return render_template('add_recipe_version.html', form=form, original_recipe=original_recipe)

@main.route('/recipe/<int:id>', methods=['GET'])
def recipe(id):
    recipe = Recipe.query.get_or_404(id)
    recipe.user = User.query.get(recipe.user_id)
    recipe.all_versions = Recipe.query.filter_by(original_id=recipe.original_id or recipe.id).all()
    if recipe.original_id:
        recipe.original = Recipe.query.get(recipe.original_id)
    return render_template('recipe.html', recipe=recipe)


@main.route('/poista_recipe', methods=['GET', 'POST'])
@login_required
@admin_required
def poista_recipe():
    recipe = Recipe.query.get(request.form.get('id'))
    if recipe is not None:
        db.session.delete(recipe)
        db.session.commit()
        flash(f"Resepti {recipe.title} on poistettu")
        return jsonify(OK="Resepti on poistettu.")
    else:
        return jsonify(virhe="Resepti' ei löydy.")

@main.route('/delete_recipe/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_recipe(id):
    recipe = Recipe.query.get_or_404(id)
    if recipe.user_id != current_user.id and not current_user.is_administrator():
        flash('Sinulla ei ole oikeutta poistaa tätä reseptiä.', 'danger')
        return redirect(url_for('main.index'))
    
    # Check if the recipe is an original or a version
    if recipe.original_id is not None:
        # It's a version, just delete it
        db.session.delete(recipe)
        db.session.commit()
        flash('Reseptiversio poistettu.', 'success')
    else:
        # It's an original, delete all versions first
        versions = Recipe.query.filter_by(original_id=recipe.id).all()
        for version in versions:
            db.session.delete(version)
        db.session.delete(recipe)
        db.session.commit()
        flash('Resepti ja kaikki sen versiot poistettu.', 'success')
    
    return redirect(url_for('main.index'))

@main.route('/load_more_recipes', methods=['GET'])
def load_more_recipes():
    offset = request.args.get('offset', 0, type=int)
    limit = 5
    more_recipes = Recipe.query.order_by(Recipe.created_at.desc()).offset(offset).limit(limit).all()
    for recipe in more_recipes:
        recipe.user = User.query.get(recipe.user_id)
    return jsonify(recipes=[{
        'id': recipe.id,
        'title': recipe.title,
        'user': recipe.user.username,
        'img': recipe.img,
        'ingredients': recipe.ingredients,
        'instructions': recipe.instructions
    } for recipe in more_recipes])

@main.route('/search_recipes', methods=['GET'])
def search_recipes():
    query = request.args.get('query', '')
    if query:
        search = f"%{query}%"
        recipes = Recipe.query.filter(Recipe.title.ilike(search)).all()
    else:
        recipes = []
    return render_template('search_results.html', query=query, recipes=recipes)

