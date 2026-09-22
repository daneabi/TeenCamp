import json
import os
import random
from flask import Flask, render_template, request, redirect, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))

FILE_NAME = 'people.json'

CHORES = [
    {"navn": "Morgenmad Køkken", "ledere": 1, "teens": 3, "køn_krav": None},
    {"navn": "Morgenmad Opvask + Spisestuen", "ledere": 1, "teens": 3, "køn_krav": None},
    {"navn": "Frokost Køkken", "ledere": 2, "teens": 3, "køn_krav": None},
    {"navn": "Frokost Opvask + Spisestuen", "ledere": 1, "teens": 3, "køn_krav": None},
    {"navn": "Aftensmad Køkkenet", "ledere": 2, "teens": 3, "køn_krav": None},
    {"navn": "Aftensmad Opvask + Spisestuen", "ledere": 1, "teens": 3, "køn_krav": None},
    {"navn": "Toilet: Piger", "ledere": 1, "teens": 2, "køn_krav": "F"},
    {"navn": "Toilet: Drenge", "ledere": 1, "teens": 2, "køn_krav": "M"},
]

def load_data():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {"teenagers": [], "leaders": []}

def save_data(data):
    with open(FILE_NAME, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def get_next_person(available_pool, full_list, arbejder_i_dag, køn=None):
    if not full_list:
        return {"navn": "[INGEN]", "køn": "?"}

    if not available_pool:
        available_pool.extend(random.sample(full_list, len(full_list)))

    gyldige_i_pulje = [p for p in available_pool if (køn is None or p['køn'] == køn) and p['navn'] not in arbejder_i_dag]
    if gyldige_i_pulje:
        valgt = gyldige_i_pulje[0]
        available_pool.remove(valgt)
        arbejder_i_dag.add(valgt['navn'])
        return valgt

    ekstra_kandidater = [p for p in full_list if (køn is None or p['køn'] == køn) and p['navn'] not in arbejder_i_dag]
    if ekstra_kandidater:
        valgt = random.choice(ekstra_kandidater)
        if valgt in available_pool:
            available_pool.remove(valgt)
        arbejder_i_dag.add(valgt['navn'])
        return valgt

    fallback_pulje = [p for p in available_pool if (køn is None or p['køn'] == køn)]
    if fallback_pulje:
        valgt = fallback_pulje[0]
        available_pool.remove(valgt)
    else:
        alle_af_køn = [p for p in full_list if (køn is None or p['køn'] == køn)]
        valgt = random.choice(alle_af_køn) if alle_af_køn else {"navn": f"[MANGLER {køn}]", "køn": køn}

    arbejder_i_dag.add(valgt.get('navn', ''))
    return valgt

@app.route('/')
def index():
    data = load_data()
    return render_template('index.html', data=data, schedule=None)

@app.route('/add', methods=['POST'])
def add():
    data = load_data()
    navn = request.form.get('navn', '').strip()
    køn = request.form.get('køn', '').upper()
    rolle = request.form.get('rolle', '')
    
    if navn and køn in ['M', 'F'] and rolle in ['teenagers', 'leaders']:
        data[rolle].append({"navn": navn, "køn": køn})
        save_data(data)
        
    return redirect(url_for('index'))

@app.route('/generate', methods=['POST'])
def generate():
    data = load_data()
    try:
        dage = int(request.form.get('dage', 1))
    except ValueError:
        dage = 1

    available_teens = random.sample(data['teenagers'], len(data['teenagers'])) if data['teenagers'] else []
    available_leaders = random.sample(data['leaders'], len(data['leaders'])) if data['leaders'] else []
    
    schedule = []
    for dag in range(1, dage + 1):
        dag_plan = {"dag": dag, "chores": []}
        arbejder_i_dag_ledere = set()
        arbejder_i_dag_teens = set()
        
        for chore in CHORES:
            tildelte_ledere = []
            tildelte_teens = []
            
            for _ in range(chore['ledere']):
                person = get_next_person(available_leaders, data['leaders'], arbejder_i_dag_ledere, chore['køn_krav'])
                tildelte_ledere.append(person['navn'])
                
            for _ in range(chore['teens']):
                person = get_next_person(available_teens, data['teenagers'], arbejder_i_dag_teens, chore['køn_krav'])
                tildelte_teens.append(person['navn'])
                
            dag_plan["chores"].append({
                "navn": chore['navn'],
                "ledere": tildelte_ledere,
                "teens": tildelte_teens
            })
        schedule.append(dag_plan)
        
    return render_template('index.html', data=data, schedule=schedule)

@app.route('/clear', methods=['POST'])
def clear():
    save_data({"teenagers": [], "leaders": []})
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)