from flask import Flask, request, jsonify
from pickle import load
# from flask_cors import CORS

app = Flask(__name__)

model = load(open('/model/model.pkl', 'rb'))

@app.route('/')
def index():
    return 'API is working'

@app.route('/api/v1/predict', methods=['POST'])
def predict():
    data_key = [
        "credit_amount",
        "present_employment",
        "property",
        "purpose",
        "saving_accounts",
        "age",
        "dependants",
        "credit_history",
        "duration",
        "existring_acc"
    ]
    req_data = request.get_json()
    """ 
    Request Body is a JSON object with the following keys:
    - credit_amount :
    - present_employment :
    - property :
    - purpose
    - saving_accounts
    - age
    - dependants
    - credit_history
    - duration
    - existring_acc
    """
    pred_data = []
    for key in data_key:
        if key in req_data:
            pred_data.append(req_data[key])
        else:
            return jsonify({'result': 'Invalid Input: {}'.format(key)})

    result = model.predict([pred_data])
    if result[0] == 1:
        return jsonify({'result': 'Approved'})
    else:
        return jsonify({'result': 'Not Approved'})

if __name__ == '__main__':
    app.run(debug=True)
