from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
from models import db, Fight
from api import api_app
import re
from send_email import send_email
import pandas as pd
from flask_caching import Cache
from settings import *

app = Flask(__name__)
app.register_blueprint(api_app)

app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONNECTION_STRING
app.config['SECRET_KEY'] = SECRET_KEY
app.config['CACHE_TYPE'] = CACHE_TYPE
app.config['CACHE_REDIS_HOST'] = CACHE_REDIS_HOST
app.config['CACHE_REDIS_PORT'] = CACHE_REDIS_PORT
app.config['CACHE_REDIS_DB'] = CACHE_REDIS_DB

db.init_app(app)

cache = Cache(app)
cache.init_app(app)

def get_page_list(cur_page=1, final_page=1):
    left = cur_page - 3 if cur_page >= 4 else 1
    right = cur_page + 3 if final_page - cur_page >= 3 else final_page
    return list(range(left, right + 1))


@app.route('/')
@cache.cached(timeout=3600, query_string=True)
def pokemons():
    try:
        page = int(request.args.get('page')) if request.args.get('page') else 1
    except ValueError:
        page = 1
    search_string = request.args.get('search_string', '')
    
    url = f"{request.host_url}/api/pokemon/list?page={page}&q={search_string}&limit=10"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()  
        pokemon_list = data.get('pokemons', [])
        pages = data['pages']
    
    return render_template("list.html", 
                            pokemons=pokemon_list, 
                            page_list=get_page_list(page, pages), 
                            current=page, 
                            final_page=pages,
                            search_string=search_string)


@app.route("/pokemon/<string:pokemon_name>")
@cache.cached(timeout=3600, query_string=True)
def pokemon_page(pokemon_name):
    url = f"{request.host_url}/api/pokemon/{pokemon_name}"
    response = requests.get(url)
    if response.status_code == 200:
        pokemon = response.json()
    return render_template("pokemon_page.html", pokemon=pokemon)


@app.route('/fight', methods=['GET', 'POST'])
def fight():
    if request.method == 'POST' and "select_pokemon" in request.form:
        select_pokemon_id = request.form["select_pokemon"]

        # почистить сессию перед новым боем
        session.clear()
        
        # выбор рандомного противника
        url = f"{request.host_url}/api/pokemon/random?id={select_pokemon_id}"
        response = requests.get(url)
        if response.status_code == 200:
            vs_pokemon_id = response.json()['id']
        else:
            print('Error random vs_pokemon_id')
            return redirect(url_for('pokemons'))
        
        # получение инфы о бое
        url = f"{request.host_url}/api/fight?id_select={select_pokemon_id}&id_vs={vs_pokemon_id}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            select_pokemon = data['select_pokemon']
            vs_pokemon = data['vs_pokemon']
            
            # записать в сессию выбранного покемона и противника
            session['select_pokemon'] = select_pokemon['id']
            session['select_pokemon_hp'] = select_pokemon['hp']
            session['select_pokemon_attack'] = select_pokemon['attack']
            session['vs_pokemon'] = vs_pokemon['id']
            session['vs_pokemon_hp'] = vs_pokemon['hp']
            session['vs_pokemon_attack'] = vs_pokemon['attack']
            
            return render_template('fight_page.html',
                                    pokemon=select_pokemon, 
                                    vs_pokemon=vs_pokemon)
        else:
            print('Error get fight info:', response.status_code)
            return redirect(url_for('pokemons'))
    return redirect(url_for('pokemons'))
        

@app.route('/fight/round', methods=["POST"])
def round():
    if request.method == "POST" and "entered_number" in request.form:
        entered_number = request.form["entered_number"]
        
        # если уже победа (при перезагрузке страницы) - на главную
        if session['select_pokemon_hp'] <= 0 or session['vs_pokemon_hp'] <= 0:
            return redirect(url_for('pokemons'))
        
        # получить инфу о бое
        url = f"{request.host_url}/api/fight?id_select={session['select_pokemon']}&id_vs={session['vs_pokemon']}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            select_pokemon = data['select_pokemon']
            vs_pokemon = data['vs_pokemon']
        
        # если число некорректное - перезагрузка страницы
        if not (entered_number.isdigit() and int(entered_number) in list(range(1, 11))):
            return render_template('fight_page.html',
                                    pokemon=select_pokemon, 
                                    vs_pokemon=vs_pokemon)
        
        # запрос для отправки хода и обновления состояния покемонов    
        url = f"{request.host_url}/api/fight/{entered_number}"
        response = requests.post(url, json={
            "select_pokemon": {
                "id": session['select_pokemon'],
                "hp": session['select_pokemon_hp'],
                "attack": session['select_pokemon_attack'],
            },
            "vs_pokemon": {
                "id": session['vs_pokemon'],
                "hp": session['vs_pokemon_hp'],
                "attack": session['vs_pokemon_attack'],
            },
        })
        if response.status_code == 200:
            data = response.json()
            session['select_pokemon_hp'] = data['select_pokemon']['hp']
            session['vs_pokemon_hp'] = data['vs_pokemon']['hp']
            winner = data['winner']
            # добавление в историю раундов инфы о раунде
            if 'history' not in session:
                session['history'] = []
            session['history'].append(data['round'])

            # если есть победитель - бой окончен => запись в бд
            if winner:
                try:
                    fight_row = Fight(select_pokemon=select_pokemon['name'],
                                      vs_pokemon=vs_pokemon['name'],
                                      win=winner == session['select_pokemon'],
                                      rounds=len(session['history']))
                    db.session.add(fight_row)
                    db.session.commit()
                except Exception:
                    print("Failed to add!")
                    db.session.rollback()
            
            return render_template('fight_page.html',
                                    pokemon=select_pokemon, 
                                    vs_pokemon=vs_pokemon,
                                    rounds=session['history'],
                                    winner=winner)
    return redirect(url_for('pokemons'))


def is_valid_email(email):
    regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    return re.fullmatch(regex, email)


# собрать итоги раунда в html-табличку 
def get_results_string(data):
    
    res = [['Your num', 'Your hp', 'Vs num', 'Vs hp', 'Win']]
    for round in data:
        res.append([round[0]['number'], round[0]['hp'], round[1]['number'], round[1]['hp'], round[2] == session['select_pokemon']])
    df = pd.DataFrame(res)
    df.columns = df.iloc[0]
    df = df[1:]
    res = df.to_html()
    return res
        

@app.route('/fight/fast', methods=['POST'])
def fast_fight():
    if 'select_pokemon' in session and 'vs_pokemon' in session:
        # если почта отправлена
        if request.method == "POST":
            email = request.form['email']
                    
            # если уже победа (при перезагрузке страницы) - на главную
            if session['select_pokemon_hp'] <= 0 or session['vs_pokemon_hp'] <= 0:
                return redirect(url_for('pokemons'))
        
            # получить инфу о бое
            url = f"{request.host_url}/api/fight?id_select={session['select_pokemon']}&id_vs={session['vs_pokemon']}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                select_pokemon = data['select_pokemon']
                vs_pokemon = data['vs_pokemon']
                
            # если почта некорректная - быстрого боя не будет
            if not email or not is_valid_email(email):
                return render_template('fight_page.html',
                                        pokemon=select_pokemon, 
                                        vs_pokemon=vs_pokemon,
                                        not_valid_email=True)
        
            # запрос для получения результатов быстрого боя    
            url = f"{request.host_url}/api/fight/fast?id_select={session['select_pokemon']}&id_vs={session['vs_pokemon']}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                session['select_pokemon_hp'] = data['select_pokemon']['hp']
                session['vs_pokemon_hp'] = data['vs_pokemon']['hp']
                rounds = data['rounds']
                winner = data['winner']
            
                # если есть победитель - бой окончен => запись в бд
                if winner:
                    try:
                        fight_row = Fight(select_pokemon=select_pokemon['name'],
                                        vs_pokemon=vs_pokemon['name'],
                                        win=winner == session['select_pokemon'],
                                        rounds=len(rounds))
                        db.session.add(fight_row)
                        db.session.commit()
                    except Exception:
                        print("Failed to add!")
                        db.session.rollback()
                 
                # отправка результатов на почту   
                result = {
                    "select_pokemon_name": select_pokemon['name'],
                    "select_pokemon_hp": select_pokemon['hp'],
                    "select_pokemon_attack": select_pokemon['attack'],
                    "vs_pokemon_name": vs_pokemon['name'],
                    "vs_pokemon_hp": vs_pokemon['hp'],
                    "vs_pokemon_attack": vs_pokemon['attack'],
                    "rounds": get_results_string(data=rounds),
                    "winner_name": select_pokemon['name'] if winner == select_pokemon['id'] else vs_pokemon['name'],
                }
                send_email(to_email=email, result=result)
                
                return render_template('fight_page.html',
                                        pokemon=select_pokemon, 
                                        vs_pokemon=vs_pokemon,
                                        rounds=rounds,
                                        winner=winner)
    return redirect(url_for('pokemons'))
            

@app.route("/fight-archive")
def archive():
    fights = Fight.query.order_by(Fight.date_time.desc()).all()
    return render_template('fight_archive.html', 
                           fights=fights,
                           thead=['№', 'select', 'vs', 'win', 'rounds', 'date'])


@app.route('/save_info', methods=['POST'])
def save_info():
    if request.method == 'POST' and 'pokemon_id' in request.form:
        pokemon_id = request.form['pokemon_id']
        
        # сохранить инфу о покемоне в файл
        url = f"{request.host_url}/api/save-info/{pokemon_id}"
        response = requests.post(url)
        if response.status_code == 201 or response.status_code == 503:
            data = response.json()
            pokemon_name = data['pokemon_name']
            
            if response.status_code == 201:
                flash('Info saved', 'info')
            else:
                flash('Info not saved', 'error')
            
            return redirect(url_for('pokemon_page', 
                                    pokemon_name=pokemon_name))   
    return redirect(url_for('pokemons'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host=APP_IP, port=APP_PORT, debug=APP_DEBUG)
    