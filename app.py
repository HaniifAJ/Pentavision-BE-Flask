from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import pickle
import numpy as np

app = Flask(__name__)
cors = CORS(app)

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

def calculate(credit_amount, tenor):
    calc_result = (credit_amount + margins[str(tenor)]*credit_amount) / tenor
    return calc_result


@app.route('/api/v1/predict', methods=['POST'])
def predict():
    try:
        feature_input = request.get_json()

        credit_amount = int(feature_input.get('credit_amount', 0))
        present_employment = int(feature_input.get('present_employment', 0))
        property = int(feature_input.get('property', 0))
        purpose = int(feature_input.get('purpose', 0))
        saving_accounts = int(feature_input.get('saving_accounts', 0))
        age = int(feature_input.get('age', 0))
        dependants = int(feature_input.get('dependants', 0))
        credit_history = int(feature_input.get('credit_history', 0))
        duration = int(feature_input.get('duration', 0))
        existing_acc = int(feature_input.get('existing_acc', 0))

        # Pastikan input dalam bentuk numpy array
        features = np.array([[credit_amount, present_employment, property, purpose, 
                              saving_accounts, age, dependants, credit_history, 
                              duration, existing_acc]])
        
        # Prediksi model
        prediction = model.predict(features)
        output = "APPROVED" if prediction[0] == 1 else "REJECTED"  # Perbaikan label output

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

@app.route('/')
def home():
    return "Flask Home Page"

@app.route('/about')
def about():
    return "About Page"

if __name__ == '__main__':
    app.run(debug=True)
