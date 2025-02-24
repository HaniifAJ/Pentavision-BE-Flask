from flask import Flask, request, jsonify
import pickle
import numpy as np

app = Flask(__name__)

# Load Model
MODEL_PATH = 'model/best_xgb_acc.pkl'
with open(MODEL_PATH, 'rb') as file:
    model = pickle.load(file)

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
