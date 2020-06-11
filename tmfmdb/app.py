import os
from os import path
import time
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo, pymongo
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

if path.exists("env.py"):
    import env

# Connection to Database
app = Flask(__name__)
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = 'mongodb+srv://vpb:ztKQZus3.k9hkMY@myfirstcluster-zzbzp.mongodb.net/task_manager?retryWrites=true&w=majority'
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)

# Collections
users_collection = mongo.db.users
recipes_collection = mongo.db.recipes
user_in_db = mongo.db.users.find_one

# Landing page Route
@app.route('/')
@app.route('/recipes')
def recipes():
    rated_text = "Highest Rated"
    # Collecting all the recipes for highest ranking Recipes
    un_rated_recipes = mongo.db.Recipes.find({'totalStarValue': {"$lt": 1}}).sort("name", 1)
    high_rated_recipes = mongo.db.Recipes.find({'totalStarValue': {"$gt": 3, "$lt": 6}}).sort(
        [('totalStarValue', pymongo.DESCENDING),
         ("name", 1)])

    # Finding the last Recipe added and approved for the Recipe highlight on the page
    new_recipe = mongo.db.Recipes.find({'approved': True}) \
        .sort([('_id', pymongo.DESCENDING), (
            'approved', pymongo.ASCENDING)]).limit(1)

    # Same as above, but acquiring to it make sure there is no duplicates
    find_last = mongo.db.Recipes.find({'approved': True}) \
        .sort([('_id', pymongo.DESCENDING), (
            'approved', pymongo.ASCENDING)]).limit(1)

    # Finds the name from last Recipe
    for x in find_last:
        last_recipe = (x['name'])

    return render_template("index.html")

# Medium Ranking Route landing page Route
@app.route('/sort-by-rating')
def sort_by_rating():
    rated_text = "Medium Rank"
    # Collecting all the recipes for Medium ranking Recipes
    un_rated_recipes = mongo.db.Recipes.find({'totalStarValue': {"$lt": 1}}).sort("name", 1).limit(9)
    medium_rated_recipes = mongo.db.Recipes.find({'totalStarValue': {"$lt": 4, "$gt": 0}}).sort(
        [('totalStarValue', pymongo.DESCENDING), ("name", 1)])

    # Finding the last Recipe added and approved for the Recipe highlight on the page
    new_recipe = mongo.db.Recipes.find({'approved': True}) \
        .sort([('_id', pymongo.DESCENDING), (
            'approved', pymongo.ASCENDING)]).limit(1)

    # Same as above, but acquiring to it make sure there is no duplicates
    find_last = mongo.db.Recipes.find({'approved': True}) \
        .sort([('_id', pymongo.DESCENDING), (
            'approved', pymongo.ASCENDING)]).limit(1)

    # Finds the name from last Recipe
    for x in find_last:
        last_recipe = (x['name'])

    return render_template('index.html')


# Administrative Portal Route
@app.route('/admin_portal')
def admin_portal():
    # Check if user in session
    if 'user' in session:
        # Check if the user is administrator
        if session['user'] == "Administrator":
            # Collects all users
            # And recipes waiting for approval
            all_users = mongo.db.users.find()
            all_users_number = all_users.count()
            pending_recipes = mongo.db.Recipes.find({'approved': False})
            pending_recipes_number = pending_recipes.count()

        else:
            return redirect(url_for('profile'))
    else:
        return redirect(url_for('login'))
    
    return render_template('admin_portal.html')


# User Profile Route
@app.route('/profile')
def profile():
    # Check if user is in session
    if 'user' in session:
        # Collect all recipes both approved and pending
        approved_recipes = mongo.db.Recipes.find({'approved': True})
        pending_recipes = mongo.db.Recipes.find({'approved': False})
        # Direct user to profile
        return render_template("profile.html")
    else:
        # Direct user to login
        return redirect(url_for('recipes'))


# Add Recipe Route
@app.route('/add_recipe')
def add_recipe():
    # Check if user is logged in
    if 'user' in session:
        user_in_database = mongo.db.users.find_one({"username": session['user']})
        if user_in_database:
            # If user in DB, redirected to Create Recipe page
            return render_template('add_recipe.html')
    else:
        # Render the page for user to be able to log in
        return render_template("login.html")


# Insert Recipe Route
@app.route('/insert_recipe', methods=['POST'])
def insert_recipe():
    creation_date = time.strftime("%Y-%m-%d", time.localtime())
    mongo.db.Recipes.insert(
        {
            'name': request.form.get('recipe_name'),
            'description': request.form.get('recipe_description'),
            'imageUrl': request.form.get('imageUrl'),
            'ingredients': request.form.get('recipe_ingredients'),
            'recipe': request.form.get('recipe'),
            'portions': request.form.get('recipe_portions'),
            'author': session['user'],
            'approved': False,
            'createDate': creation_date,
            'lastUpdateDate': 0,
            'starRating-1': 0,
            'starRating-2': 0,
            'starRating-3': 0,
            'starRating-4': 0,
            'starRating-5': 0,
            'totalVotes': 0,
            'totalStarValue': 0
        })
    return redirect(url_for('recipes'))


# Insert/Calculate Rating Route
@app.route('/insert_rating/<recipe_id>', methods=['POST', 'GET'])
def insert_rating(recipe_id):
    if 'user' in session:
        starRating = request.form['submit_rating']
        mongo.db.Recipes.update({'_id': ObjectId(recipe_id)},
                                {
                                    '$inc': {
                                        starRating: 1,
                                        'totalVotes': 1
                                    }
                                },
                                upsert=False
                                )
        # Preforms the calculation for the 5 star rating
        star_array = mongo.db.Recipes.find_one({'_id': ObjectId(recipe_id)})
        star_calculator = ((5 * star_array["starRating-5"]
                            + 4 * star_array["starRating-4"]
                            + 3 * star_array["starRating-3"]
                            + 2 * star_array["starRating-2"]
                            + 1 * star_array["starRating-1"])
                           / (star_array["starRating-5"]
                              + star_array["starRating-4"]
                              + star_array["starRating-3"]
                              + star_array["starRating-2"]
                              + star_array["starRating-1"]))

        total_votes = (star_array["starRating-5"]
                       + star_array["starRating-4"]
                       + star_array["starRating-3"]
                       + star_array["starRating-2"]
                       + star_array["starRating-1"])

        star_calculator = (int(star_calculator))
        print(star_calculator)
        # Preform a set update to only updated the values inserted
        mongo.db.Recipes.update({'_id': ObjectId(recipe_id)},
                                {
                                    '$set': {
                                        'totalStarValue': star_calculator,
                                        'totalVotes': total_votes
                                    }
                                },
                                upsert=True

                                )
        return redirect(request.referrer)

    else:
        flash('To rate a recipe you must be logged in')
        return redirect(url_for('login'))


# Recipe Route
@app.route('/recipe/<recipe_id>/')
def recipe(recipe_id):
    # Get all data related to the corresponding recipe_id
    recipe_data = mongo.db.Recipes.find_one({"_id": ObjectId(recipe_id)})
    # Get the star rating information
    data = {'total': recipe_data["totalStarValue"]}
    return render_template('recipe.html')


# Edit Recipe Route
@app.route('/edit_recipe/<recipe_id>')
def edit_recipe(recipe_id):
    # Check if the user is in session
    if 'user' in session:
        # Collects all the recipe data for handling
        recipe_data = mongo.db.Recipes.find_one({"_id": ObjectId(recipe_id)})
        # Stores author for use later
        author = recipe_data["author"]
        # Make sure only administrator or author can edit the recipe
        if session['user'] == author or session['user'] == "Administrator":
            return render_template('recipeUpdate.html')
        else:
            flash('Only Admins can access this page!')
            return redirect(url_for('recipes'))
    else:
        return redirect(url_for('login'))


# Update Recipe Route
@app.route('/update_recipe/<recipe_id>', methods=["POST"])
def update_recipe(recipe_id):
    # Get the date for update
    last_updated_date = time.strftime("%Y-%m-%d", time.localtime())
    recipe_data = mongo.db.Recipes.find_one({'_id': ObjectId(recipe_id)})
    # Get author
    author = recipe_data["author"]
    # Get created Date
    if 'user' in session:
        # Check if user is either author, administrator
        if session['user'] == author or session['user'] == "Administrator":
            mongo.db.Recipes.update({'_id': ObjectId(recipe_id)}, {
                '$set': {
                    'name': request.form.get('recipe_name'),
                    'description': request.form.get('recipe_description'),
                    'imageUrl': request.form.get('imageUrl'),
                    'ingredients': request.form.get('recipe_ingredients'),
                    'recipe': request.form.get('recipe'),
                    'portions': request.form.get('recipe_portions'),
                    'lastUpdateDate': last_updated_date,
                        }
                    },
                            upsert=True
                )

            return redirect(url_for('recipes'))
        else:
            return redirect(url_for('recipes'))
    else:
        return redirect(url_for('login'))


# Delete Recipe Route
@app.route('/delete_recipe/<recipe_id>')
def delete_recipe(recipe_id):
    # Find Author
    find_author = mongo.db.Recipes.find_one({'_id': ObjectId(recipe_id)})
    author = find_author['author']
    # Check if user is in session
    if 'user' in session:
        # Check if the user is the author
        if session['user'] == author or session['user'] == "Administrator":
            # Deletes the Recipe
            mongo.db.Recipes.remove({'_id': ObjectId(recipe_id)})
            return redirect(url_for('recipes'))
        else:
            return redirect(url_for('recipes'))
    else:
        return redirect(url_for('login'))


# Delete User Route
@app.route('/delete_user/<user_id>')
def delete_user(user_id):
    # Check if user is logged in
    if 'user' in session:
        if session['user'] == "Administrator":
            # Finds the user and removes it
            mongo.db.users.remove({'_id': ObjectId(user_id)})
            return redirect(url_for('admin_portal'))
        else:
            return redirect(url_for('recipes'))
    else:
        return redirect(url_for('login'))


# Approve Recipe
@app.route('/approve_recipe/<recipe_id>')
def approve_recipe(recipe_id):
    # Check if user is in session
    if 'user' in session:
        if session["user"] == "Administrator":
            # Set the approval to True
            mongo.db.Recipes.update({'_id': ObjectId(recipe_id)},
                                    {
                                        '$set': {
                                            'approved': True
                                        }
                                    },
                                    # protection={'seq': True, '_id': False},
                                    upsert=False

                                    )
            return redirect(url_for('admin_portal'))
        else:
            return redirect(url_for('recipes'))
    else:
        return redirect(url_for('login'))


# Login Route
@app.route('/login', methods=['GET'])
def login():
    user_in_db = mongo.db.users
    if 'user' in session:
        user_in_db = users.find_one({'username' : request.form['user']})
        if user_in_db:
            session['username'] = request.form['username']
            return redirect(url_for('profile'))
    return render_template("login.html")

# Log out route
@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    flash('You were logged out!')
    return redirect(url_for('recipes'))

# User authentication route
@app.route('/user_auth', methods=['GET', 'POST'])
def user_auth():
    form = request.form.to_dict()
    user_in_db = mongo.db.users.find_one({"username": form['username']})
    # Check for user in database
    if user_in_db:
        # If passwords match (hashed / real password)
        if check_password_hash(user_in_db['password'], form['user_password']):
            # Log user in (add to session)
            session['user'] = form['username']
            # If the user is admin redirect him to admin area
            if session['user'] == "admin":
                return redirect(url_for('recipes'))
            else:
                flash("You were logged in!")
                return redirect(url_for('recipes'))
        else:
            flash("Wrong password or user name")
            return redirect(url_for('login'))
    else:
        flash("You are not registered")
        return redirect(url_for('login'))

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Check if user is not logged in already
    if 'user' in session:
        return redirect(url_for('recipes'))

    if request.method == 'POST':
        form = request.form.to_dict()
        # Check if the password and password actually match
        if form['user_password'] == form['user_password1']:
            # Check if the user exist in the database
            user = mongo.db.users.find_one({"username": form['username']})
            if user:
                flash(f"{form['username']} already exists!")
                return redirect(url_for('register'))
            # If user does not exist register new user
            else:
                # Hash password
                hash_pass = generate_password_hash(form['user_password'])
                # Create new user with hashed password
                mongo.db.users.insert_one(
                    {
                        'username': form['username'],
                        'email': form['email'],
                        'password': hash_pass

                    }
                )
                # Check if user is actually saved
                user_in_db = mongo.db.users.find_one({"username": form['username']})
                if user_in_db:
                    # Log user in (add to session)
                    session['user'] = user_in_db['username']
                    return redirect(url_for('register'))
                else:
                    flash("There was a problem saving your profile")
                    return redirect(url_for('register'))

        else:
            flash("Passwords dont match!")
            return redirect(url_for('register'))

    return render_template("register.html")



# Error 404 handler route
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Error 500 handler route
@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=os.environ.get('PORT'),
            debug=False)
