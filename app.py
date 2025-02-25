from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import pickle
import numpy as np
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import Schema, fields, ValidationError, validate
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
cors = CORS(app)

# Set up SQLAlchemy Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql+psycopg2://user:password@localhost/dbname')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print(app.config['SQLALCHEMY_DATABASE_URI'])

# Initialize Database & Marshmallow
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Load Model
MODEL_PATH = 'model/best_xgb_acc.pkl'
with open(MODEL_PATH, 'rb') as file:
    model = pickle.load(file)

margins = {
    "6": 0.07,
    "12": 0.08,
    "24": 0.09,
    "36": 0.10
}

tenors = [
    6,
    12,
    24,
    36
]

class CreditApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    credit_amount = db.Column(db.BigInteger, nullable=False)
    present_employment = db.Column(db.Integer, nullable=False)
    property = db.Column(db.Integer, nullable=False)
    purpose = db.Column(db.Integer, nullable=False)
    saving_accounts = db.Column(db.Integer, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    dependants = db.Column(db.Integer, nullable=False)
    credit_history = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    existing_acc = db.Column(db.Integer, nullable=False)
    result = db.Column(db.Boolean, nullable=True)

with app.app_context():
    db.create_all()

# ---------------- Validation Schema ----------------
class CreditApplicationSchema(ma.Schema):
    credit_amount = fields.Integer(required=True, validate=lambda x: 1 <= x <= 100_000_000_000)
    present_employment = fields.Integer(strict=True, required=True, validate=validate.Range(0, 4, error="Value must be between 0 and 4"))
    property = fields.Integer(strict=True, required=True, validate=validate.Range(0, 3, error="Value must be between 0 and 3"))
    purpose = fields.Integer(strict=True, required=True, validate=validate.Range(0, 3, error="Value must be between 0 and 3"))
    saving_accounts = fields.Integer(strict=True, required=True, validate=validate.Range(0, 4, error="Value must be between 0 and 4"))
    age = fields.Integer(strict=True, required=True, validate=validate.Range(1, 100, error="Value must be between 1 and 100"))
    dependants = fields.Integer(strict=True, required=True, validate=validate.Range(0, 100, error="Value must be between 0 and 100"))
    credit_history = fields.Integer(strict=True, required=True, validate=validate.Range(0, 4, error="Value must be between 0 and 4"))
    duration = fields.Integer(strict=True, required=True, validate=validate.OneOf([6,12,24,36]))  # Months
    existing_acc = fields.Integer(strict=True, required=True, validate=validate.Range(0, 3, error="Value must be between 0 and 3"))
    result = fields.Boolean(strict=True, required=False)

credit_schema = CreditApplicationSchema()

def calculate(credit_amount, tenor):
    calc_result = (credit_amount + margins[str(tenor)]*credit_amount) / tenor
    return calc_result


@app.route('/api/v1/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        validated_data = credit_schema.load(data)

        # Create new CreditApplication instance
        new_application = CreditApplication(**validated_data)

        credit_amount = new_application.credit_amount
        present_employment = new_application.present_employment
        property = new_application.property
        purpose = new_application.purpose
        saving_accounts = new_application.saving_accounts
        age = new_application.age
        dependants = new_application.dependants
        credit_history = new_application.credit_history
        duration = new_application.duration
        existing_acc = new_application.existing_acc



        # feature_input = request.get_json()

        # credit_amount = int(feature_input.get('credit_amount', 0))
        # present_employment = int(feature_input.get('present_employment', 0))
        # property = int(feature_input.get('property', 0))
        # purpose = int(feature_input.get('purpose', 0))
        # saving_accounts = int(feature_input.get('saving_accounts', 0))
        # age = int(feature_input.get('age', 0))
        # dependants = int(feature_input.get('dependants', 0))
        # credit_history = int(feature_input.get('credit_history', 0))
        # duration = int(feature_input.get('duration', 0))
        # existing_acc = int(feature_input.get('existing_acc', 0))

        # Pastikan input dalam bentuk numpy array
        features = np.array([[credit_amount, present_employment, property, purpose, 
                              saving_accounts, age, dependants, credit_history, 
                              duration, existing_acc]])
        
        # Prediksi model
        prediction = model.predict(features)
        output = "APPROVED" if prediction[0] == 1 else "REJECTED"  # Perbaikan label output

        new_application.result = prediction[0] == 1

        db.session.add(new_application)
        db.session.commit()


        if(prediction[0] == 1):
            result = []
            for tenor in tenors:
                calc_result = calculate(credit_amount, tenor)
                result.append({
                    "tenor": tenor,
                    "margin": margins[str(tenor)],
                    "installment": calc_result
                })
            
            return jsonify({
                "message": "Prediction Success",
                "prediction_text": output,
                "input_data": {
                    "Credit Amount": credit_amount,
                    "Present Employment": present_employment,
                    "Property": property,
                    "Purpose": purpose,
                    "Saving Accounts": saving_accounts,
                    "Age": age,
                    "Dependants": dependants,
                    "Credit History": credit_history,
                    "Duration": duration,
                    "Existing Account": existing_acc,
                },
                "calc_result": result
            })

            

        return jsonify({
            "message": "Prediction Success",
            "prediction_text": output,
            "input_data": {
                "Credit Amount": credit_amount,
                "Present Employment": present_employment,
                "Property": property,
                "Purpose": purpose,
                "Saving Accounts": saving_accounts,
                "Age": age,
                "Dependants": dependants,
                "Credit History": credit_history,
                "Duration": duration,
                "Existing Account": existing_acc,
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/v1/applications', methods=['GET'])
def get_applications():
    try: 
        applications = CreditApplication.query.all()
        result = credit_schema.dump(applications, many=True)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/')
def home():
    return "Flask Home Page"

@app.route('/about')
def about():
    return "About Page"

if __name__ == '__main__':
    app.run(debug=True)
