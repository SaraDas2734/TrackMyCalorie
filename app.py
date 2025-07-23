import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from utils.calculations import calculate_bmr, calculate_tdee, calculate_macros, suggest_goal
from utils.food_data import get_food_info, get_supplement_info, calculate_portion_nutrients
from dotenv import load_dotenv
import requests
import json
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
EDAMAM_APP_ID = os.getenv('EDAMAM_APP_ID', 'your_edamam_app_id_here')
EDAMAM_APP_KEY = os.getenv('EDAMAM_APP_KEY', 'your_edamam_app_key_here')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyAoGaoj9pNleyef7038RrofFJ344NDpyyA')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Simplified database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trackmycalorie.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    height = db.Column(db.Float, nullable=True)  # in cm
    weight = db.Column(db.Float, nullable=True)  # in kg
    activity_level = db.Column(db.String(20), nullable=True)
    goal = db.Column(db.String(20), nullable=True)
    meals = db.relationship('Meal', backref='user', lazy=True)
    supplements = db.relationship('Supplement', backref='user', lazy=True)
    weight_logs = db.relationship('WeightLog', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_name = db.Column(db.String(100), nullable=False)
    portion_size = db.Column(db.Float, nullable=False)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fats = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Supplement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    serving_size = db.Column(db.Float, nullable=False)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class WeightLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def is_profile_complete(user):
    return all([
        user.gender,
        user.age,
        user.height,
        user.weight,
        user.activity_level,
        user.goal
    ])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists.', 'danger')
            return render_template('register.html')
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    user = current_user
    if not is_profile_complete(user):
        flash('Please complete your profile to continue.', 'warning')
        return redirect(url_for('profile', edit=1))
    today_meals = Meal.query.filter_by(user_id=user.id).filter(
        db.func.date(Meal.date) == datetime.utcnow().date()
    ).all()
    today_supplements = Supplement.query.filter_by(user_id=user.id).filter(
        db.func.date(Supplement.date) == datetime.utcnow().date()
    ).all()
    
    # Calculate totals
    total_calories = sum(meal.calories for meal in today_meals) + sum(supp.calories for supp in today_supplements)
    total_protein = sum(meal.protein for meal in today_meals) + sum(supp.protein for supp in today_supplements)
    total_carbs = sum(meal.carbs for meal in today_meals)
    total_fats = sum(meal.fats for meal in today_meals)
    
    # Get targets
    bmr = calculate_bmr(user.weight, user.height, user.age, user.gender)
    tdee = calculate_tdee(bmr, user.activity_level)
    targets = calculate_macros(tdee, user.goal, user.weight)
    
    return render_template('home.html', 
                         user=user,
                         meals=today_meals,
                         supplements=today_supplements,
                         totals={'calories': total_calories, 
                                'protein': total_protein,
                                'carbs': total_carbs,
                                'fats': total_fats},
                         targets=targets)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user
    edit_mode = request.args.get('edit') == '1'
    suggestion = None
    explanation = None
    if request.method == 'POST':
        if user:
            user.name = request.form['name']
            user.age = int(request.form['age'])
            user.gender = request.form['gender']
            user.height = float(request.form['height'])
            user.weight = float(request.form['weight'])
            user.activity_level = request.form['activity_level']
            user.goal = request.form['goal']
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        else:
            user = User(
                name=request.form['name'],
                age=int(request.form['age']),
                gender=request.form['gender'],
                height=float(request.form['height']),
                weight=float(request.form['weight']),
                activity_level=request.form['activity_level'],
                goal=request.form['goal']
            )
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            flash('Profile created successfully!', 'success')
            return redirect(url_for('home'))
    # Suggestion logic for GET (edit mode)
    if edit_mode:
        # Try to get values from user or default to empty
        gender = user.gender if user and user.gender else None
        height = user.height if user and user.height else None
        age = user.age if user and user.age else None
        weight = user.weight if user and user.weight else None
        if gender and height and age and weight:
            suggestion, explanation = suggest_goal(gender, height, age, weight)
    return render_template('profile.html', user=user, edit_mode=edit_mode, suggestion=suggestion, explanation=explanation)

@app.route('/add_meal', methods=['GET', 'POST'])
@login_required
def add_meal():
    user = current_user
    if request.method == 'POST':
        food_name = request.form['food_name']
        calories = request.form['calories']
        protein = request.form['protein']
        carbs = request.form['carbs']
        fats = request.form['fats']
        # Backend validation
        if not all([calories, protein, carbs, fats]):
            flash('Please use "Calculate Calories" and ensure all fields are filled before adding the meal.', 'danger')
            return render_template('add_meal.html')
        calories = float(calories)
        protein = float(protein)
        carbs = float(carbs)
        fats = float(fats)
        meal = Meal(
            user_id=user.id,
            food_name=food_name,
            portion_size=1,  # Default to 1 for AI-powered entry
            calories=calories,
            protein=protein,
            carbs=carbs,
            fats=fats
        )
        db.session.add(meal)
        db.session.commit()
        flash('Meal added successfully!', 'success')
        return redirect(url_for('home'))
    return render_template('add_meal.html')

@app.route('/supplements', methods=['GET', 'POST'])
@login_required
def supplements():
    user = current_user
    
    if request.method == 'POST':
        supp_name = request.form['supplement_name']
        serving_size = float(request.form['serving_size'])
        
        supp_info = get_supplement_info(supp_name)
        if supp_info:
            nutrients = calculate_portion_nutrients(supp_info, serving_size)
            supplement = Supplement(
                user_id=user.id,
                name=supp_name,
                serving_size=serving_size,
                calories=nutrients['calories'],
                protein=nutrients['protein']
            )
            db.session.add(supplement)
            db.session.commit()
            flash('Supplement added successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Supplement not found in database!', 'error')
    
    return render_template('supplements.html')

@app.route('/weight_tracker', methods=['GET', 'POST'])
@login_required
def weight_tracker():
    user = current_user
    
    if request.method == 'POST':
        weight = float(request.form['weight'])
        log = WeightLog(user_id=user.id, weight=weight)
        db.session.add(log)
        db.session.commit()
        flash('Weight logged successfully!', 'success')
    
    weight_logs = WeightLog.query.filter_by(user_id=user.id).order_by(WeightLog.date.desc()).all()
    # Format dates for template
    weight_logs_with_strdate = [
        {'date': log.date.strftime('%Y-%m-%d'), 'weight': log.weight}
        for log in weight_logs
    ]
    return render_template('weight_tracker.html', weight_logs=weight_logs_with_strdate)

@app.route('/summary')
@login_required
def summary():
    user = current_user
    
    # Get today's totals
    today_meals = Meal.query.filter_by(user_id=user.id).filter(
        db.func.date(Meal.date) == datetime.utcnow().date()
    ).all()
    today_supplements = Supplement.query.filter_by(user_id=user.id).filter(
        db.func.date(Supplement.date) == datetime.utcnow().date()
    ).all()
    
    total_calories = sum(meal.calories for meal in today_meals) + sum(supp.calories for supp in today_supplements)
    total_protein = sum(meal.protein for meal in today_meals) + sum(supp.protein for supp in today_supplements)
    
    # Get targets
    bmr = calculate_bmr(user.weight, user.height, user.age, user.gender)
    tdee = calculate_tdee(bmr, user.activity_level)
    targets = calculate_macros(tdee, user.goal, user.weight)
    
    # Calculate remaining
    remaining_calories = targets['calories'] - total_calories
    remaining_protein = targets['protein'] - total_protein
    
    return render_template('summary.html',
                         user=user,
                         total_calories=total_calories,
                         total_protein=total_protein,
                         remaining_calories=remaining_calories,
                         remaining_protein=remaining_protein,
                         targets=targets)

@app.route('/api/edamam_search')
def edamam_search():
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    url = 'https://api.edamam.com/api/food-database/v2/parser'
    params = {
        'app_id': EDAMAM_APP_ID,
        'app_key': EDAMAM_APP_KEY,
        'ingr': query
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return jsonify({'error': 'API error', 'details': response.text}), 500
    data = response.json()
    # Return only relevant info for frontend
    foods = []
    for hint in data.get('hints', []):
        food = hint['food']
        foods.append({
            'label': food['label'],
            'calories': food['nutrients'].get('ENERC_KCAL', 0),
            'protein': food['nutrients'].get('PROCNT', 0),
            'carbs': food['nutrients'].get('CHOCDF', 0),
            'fats': food['nutrients'].get('FAT', 0),
            'serving': food.get('servingSizes', [{}])[0].get('quantity', 1)
        })
    return jsonify({'foods': foods})

@app.route('/api/gemini_calories', methods=['POST'])
def gemini_calories():
    data = request.get_json()
    food_query = data.get('query')
    if not food_query:
        return jsonify({'error': 'No food query provided'}), 400
    url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=' + GEMINI_API_KEY
    headers = {'Content-Type': 'application/json'}
    prompt = f"You are a nutritionist. Estimate the calories, protein, carbs, and fats for: {food_query}. Respond in the format: Calories: X kcal, Protein: Y g, Carbs: Z g, Fats: W g."
    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code != 200:
        return jsonify({'error': 'Gemini API error', 'details': response.text}), 500
    result = response.json()
    try:
        ai_text = result['candidates'][0]['content']['parts'][0]['text']
    except Exception:
        return jsonify({'error': 'Invalid response from Gemini', 'details': result}), 500
    return jsonify({'result': ai_text})

if __name__ == '__main__':
    app.run(debug=True)
