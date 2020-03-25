import json
import re
import requests
import time

from bson import json_util
from flask import Flask, request, jsonify, render_template, abort
from flask_pymongo import PyMongo 
from flask_cors import CORS, cross_origin

mongo = PyMongo()

app = Flask(__name__)

app.config["MONGO_URI"] = 'mongodb+srv://<username>:<password>@<server-name>/<database-name>?retryWrites=true&w=majority'

CORS(app)

app.config['CORS_HEADERS'] = 'Content-Type'

mongo.init_app(app)

@app.route('/')
@cross_origin()
def home():
    return render_template('index.html')

@app.route('/all/<limit>', methods=['GET'])
@cross_origin()
def all(limit):
    try:
        record_lim = int(limit)
    except:
        record_lim = 0
    try:
        r = requests.get('https://covidlk-autorun.herokuapp.com/ping')
    except:
        print('External API failed..')
    query_collection = mongo.db.daily #select collection
    result = json.dumps(list(query_collection.find({}).sort([("update_date_time", -1)]).limit(record_lim)), default=json_util.default)
    if result == "[]":
        return jsonify({'message': 'No data yet!'}), 400
    return result, 200

@app.route('/ping')
@cross_origin()
def ping():
    r = requests.get('https://hpb.health.gov.lk/api/get-current-statistical')
    responce = r.json()
    new_date = responce['data']['update_date_time']
    print(responce['data']['update_date_time'])

    last_update_collection = mongo.db.last_update #select collection
    result = json.dumps(list(last_update_collection.find({'qid' : 1}, {"_id": 0, "update_date_time": 1})), default=json_util.default)
    if result == "[]":
        queryToInsert = {
            'qid': 1,
            'update_date_time': new_date,
        }
        last_update_collection.insert(queryToInsert) #insert
    if new_date not in result:
        print('new date')
        dataToInsert = {
            'update_date_time': responce['data']['update_date_time'],
            'local_new_cases': responce['data']['local_new_cases'],
            'local_total_cases': responce['data']['local_total_cases'],
            'local_total_number_of_individuals_in_hospitals': responce['data']['local_total_number_of_individuals_in_hospitals'],
            'local_deaths': responce['data']['local_deaths'],
            'local_new_deaths': responce['data']['local_new_deaths'],
            'local_recovered': responce['data']['local_recovered'],
            'global_new_cases': responce['data']['global_new_cases'],
            'global_total_cases': responce['data']['global_total_cases'],
            'global_deaths': responce['data']['global_deaths'],
            'global_new_deaths': responce['data']['global_new_deaths'],
            'global_recovered': responce['data']['global_recovered'],
            'hospital_data': responce['data']['hospital_data']
        }
        query_collection = mongo.db.daily #select queries collection
        query_collection.insert(dataToInsert) #insert
        last_update_collection.update({"qid": 1}, {'$set': {"update_date_time": responce['data']['update_date_time']}})
    else:
        print('not updated')
    return 'running....'

if __name__ == "__main__":
    app.run(debug=True)