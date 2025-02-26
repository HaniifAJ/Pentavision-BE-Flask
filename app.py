from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import pickle
import numpy as np
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import Schema, fields, ValidationError, validate
import os
from dotenv import load_dotenv
from sklearn.preprocessing import StandardScaler
import pandas as pd
from sklearn.metrics import accuracy_score

load_dotenv()

app = Flask(__name__)
cors = CORS(app)

# Set up SQLAlchemy Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql+psycopg2://user:password@localhost/dbname')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# print(app.config['SQLALCHEMY_DATABASE_URI'])

# Initialize Database & Marshmallow
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Load Model
# MODEL_PATH = 'model/best_xgb_acc.pkl'
MODEL_PATH = 'model/best_rf_model.pkl'
with open(MODEL_PATH, 'rb') as file:
    model = pickle.load(file)

margins = {
    "12": {
        "1": 6.62,
        "2": 5.78,
        "3": 8.75,
    },
    "24": {
        "1": 6.77,
        "2": 5.65,
        "3": 8.75,
    },
    "36": {
        "1": 7.10,
        "2": 5.67,
        "3": 8.75,
    },
    "48": {
        "1": 7.34,
        "2": 5.73,
        "3": 8.75,
    },
    "60": {
        "1": 7.61,
        "2": 5.79,
        "3": 8.75,
    },
}

tenors = [
    12,
    24,
    36,
    48,
    60
]

class CreditApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    credit_amount = db.Column(db.BigInteger, nullable=False)
    present_employment = db.Column(db.Integer, nullable=False)
    property = db.Column(db.Integer, nullable=False)
    purpose = db.Column(db.Integer, nullable=False)
    
    salary = db.Column(db.Integer, nullable=False)
    # saving_accounts = db.Column(db.Integer, nullable=False)
    
    age = db.Column(db.Integer, nullable=False)
    # dependants = db.Column(db.Integer, nullable=False)
    credit_history = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    existing_acc = db.Column(db.Integer, nullable=False)
    result = db.Column(db.Boolean, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

with app.app_context():
    db.create_all()

# ---------------- Validation Schema ----------------
class CreditApplicationSchema(ma.Schema):
    credit_amount = fields.Integer(required=True, validate=lambda x: 1 <= x <= 100_000_000_000)
    present_employment = fields.Integer(strict=True, required=True, validate=validate.Range(0, 4, error="Value must be between 0 and 4"))
    property = fields.Integer(strict=True, required=True, validate=validate.Range(0, 3, error="Value must be between 0 and 3"))
    purpose = fields.Integer(strict=True, required=True, validate=validate.Range(0, 3, error="Value must be between 0 and 3"))

    salary = fields.Integer(required=True, validate=validate.Range(0, 3, error="Value must be between 0 and 3"))
    # saving_accounts = fields.Integer(strict=True, required=True, validate=validate.Range(0, 4, error="Value must be between 0 and 4"))
    
    age = fields.Integer(strict=True, required=True, validate=validate.Range(1, 100, error="Value must be between 1 and 100"))
    # dependants = fields.Integer(strict=True, required=True, validate=validate.Range(0, 100, error="Value must be between 0 and 100"))
    credit_history = fields.Integer(strict=True, required=True, validate=validate.Range(0, 4, error="Value must be between 0 and 4"))
    duration = fields.Integer(strict=True, required=True, validate=validate.OneOf(tenors))  # Months
    existing_acc = fields.Integer(strict=True, required=True, validate=validate.Range(0, 3, error="Value must be between 0 and 3"))
    result = fields.Boolean(strict=True, required=False)

class InputDataSchema(ma.Schema):
    data = fields.Nested(CreditApplicationSchema, required=True)
    save = fields.Integer(required=True, validate=validate.OneOf([0, 1], error="Value must be 0 or 1")) # 0: No, 1: Yes

credit_schema = CreditApplicationSchema()
input_schema = InputDataSchema()

def calculate(credit_amount, tenor, purpose):
    calc_result = (credit_amount + margins[str(tenor)][str(purpose)]*tenor/12.*credit_amount)/(tenor)
    return calc_result

df = pd.read_csv('scaler/train_data.csv')
# label = df['credit'].values
df = df[['credit_hist', 'present_employment', 'property', 'purpose', 'status_existing_account', 'salary', 'age', 'credit_amount', 'duration']]
scaler = StandardScaler()
# print(df.values[0])
scaler.fit(df)
# df = scaler.transform(df)
# print(scaled_values[0])

# result = model.predict(df)
# print(accuracy_score(label, np.int16(result)))
# result_df = pd.DataFrame(result, columns=['result'])
# result_df.to_csv('result.csv', index=False)



@app.route('/api/v1/predict', methods=['POST'])
def predict():
    try:
        data = input_schema.load(request.get_json())
        # print(data)
        validated_data = credit_schema.load(data['data'])

        # Create new CreditApplication instance
        new_application = CreditApplication(**validated_data)

        credit_amount = new_application.credit_amount
        present_employment = new_application.present_employment
        property = new_application.property
        purpose = new_application.purpose

        salary = new_application.salary
        # saving_accounts = new_application.saving_accounts

        age = new_application.age
        # dependants = new_application.dependants
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
        # 'credit_hist', 'present_employment', 'property', 'purpose', 'status_existing_account', 'salary', 'age', 'credit_amount', 'duration'
        features = np.array([[credit_history, present_employment, property, purpose, 
                              existing_acc, salary, age, credit_amount, duration]])
        # features = np.array([[credit_history, present_employment, credit_amount, 
        #                       property, purpose, salary, duration, age, existing_acc]])

        # Scaling features
        scaled_features = scaler.transform(features)
        # print(features)
        # print(scaled_features)

        features_df = pd.DataFrame(scaled_features, columns=['credit_hist', 'present_employment', 'property', 'purpose', 'status_existing_account', 'salary', 'age', 'credit_amount', 'duration'])
        
        # Prediksi model
        prediction = model.predict(features_df)
        prediction[0] = int(prediction[0])
        output = "APPROVED" if prediction[0] == 1 else "REJECTED"  # Perbaikan label output

        new_application.result = prediction[0] == 1
        # print('tes')
        if data['save'] == 1:
            db.session.add(new_application)
            db.session.commit()
            # print("Data saved")


        if(prediction[0] == 1):
            result = []
            for tenor in tenors:
                calc_result = calculate(credit_amount, tenor, purpose)
                result.append({
                    "tenor": tenor,
                    "margin": margins[str(tenor)][str(purpose)],
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
                    "Salary": salary,
                    "Age": age,
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
                "Salary": salary,
                "Age": age,
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
