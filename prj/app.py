from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import requests
import random
from models import connect_string, db, Fight

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = connect_string
app.config['SECRET_KEY'] = 'meow_key_mrrr$' 

db.init_app(app)

limit = 10

def get_pokemon_list(offset=0, limit=10):
    url = f"https://pokeapi.co/api/v2/pokemon/?offset={offset}&limit={limit}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()  
        pokemon_list = data.get("results", [])
        all_poke_count = data['count']
        return pokemon_list, int(all_poke_count / limit + int(all_poke_count % limit > 0))
    else:
        print(f"Error: {response.status_code}")
        return [], 0


def get_page_list(cur_page=1, final_page=1):
    left = cur_page - 3 if cur_page >= 4 else 1
    right = cur_page + 3 if final_page - cur_page >= 3 else final_page
    return list(range(left, right + 1))


def get_pokemon_info(pokemon_name):
    if pokemon_name:
        url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.strip()}/"
        response = requests.get(url)
    
        if response.status_code == 200:
            data = response.json()
            
            stats = data["stats"]
            
            hp = next((x for x in stats if x["stat"]["name"] == "hp"), None)
            attack = next((x for x in stats if x["stat"]["name"] == "attack"), None)
            defense = next((x for x in stats if x["stat"]["name"] == "defense"), None)
            speed = next((x for x in stats if x["stat"]["name"] == "speed"), None)
            poison = next((x for x in stats if x["stat"]["name"] == "poison"), None)
            
            return {
                "id": data["id"],
                "name": data["name"],
                "image": data["sprites"]["front_default"],
                "large_image": data["sprites"]["other"]["dream_world"]["front_default"],
                "hp": hp["base_stat"] if hp else None,
                "attack": attack["base_stat"] if attack else None,
                "defense": defense["base_stat"] if defense else None,
                "speed": speed["base_stat"] if speed else None,
                "poison": poison["base_stat"] if poison else None,
            }

    print("not found pokemon info")
    return {}


@app.route('/')
def pokemons():
    try:
        page = int(request.args.get('page')) if request.args.get('page') else 1
    except ValueError:
        page = 1

    offset = (page - 1) * limit 
 
    pokemon_list, page_count = get_pokemon_list(offset, limit)
    
    search_string = request.args.get('search_string', None)
    
    if search_string and search_string.strip() != "":
        pokemon_list, page_count = get_pokemon_list(offset=0, limit=page_count * limit)
        pokemon_list = [pokemon for pokemon in pokemon_list if search_string.strip() in pokemon['name']]
        page_count = int(len(pokemon_list) / limit) + int(len(pokemon_list) % limit > 0)
        pokemon_list = pokemon_list[offset:offset + limit]
    
    pokemon_list = [get_pokemon_info(pokemon["name"]) for pokemon in pokemon_list]
    
    return render_template("list.html", 
                           pokemons=pokemon_list, 
                           page_list=get_page_list(page, page_count), 
                           current=page, 
                           final_page=page_count,
                           search_string=search_string)


@app.route("/pokemon/<string:pokemon_name>")
def pokemon_page(pokemon_name):
    pokemon = get_pokemon_info(pokemon_name)
    return render_template("pokemon_page.html", pokemon=pokemon)
    
    
def decrease_hp(entered_number: int, vs_pokemon_number: int, run: bool):
    if entered_number % 2 == vs_pokemon_number % 2:
        if run:
            session['vs_pokemon_hp'] -= session['select_pokemon_attack']
        return True
    else:
        if run:
            session['select_pokemon_hp'] -= session['vs_pokemon_attack']
        return False
    

def define_global_win():
    return session['vs_pokemon_hp'] <= 0 or session['select_pokemon_hp'] <= 0


def winner():
    result = None
    if session['vs_pokemon_hp'] <= 0:
        result = session['select_pokemon']
    elif session['select_pokemon_hp'] <= 0:
        result = session['vs_pokemon']
    return result
    
    
@app.route("/fight", methods=['GET', 'POST'])
def fight():
    if request.method == 'POST':
        # может прийти: 
        # - имя выбранного покемона (для начала боя) 
        # - введённое число (во время боя)
        # - 'ok' - вычесть hp после раунда
        # - 'ok_win' - бой окончен, выйти
        try:
            your_pokemon_name = request.form["select_pokemon"]
        except KeyError:
            print('not your_pokemon_name')
            your_pokemon_name = None
        try:
            entered_number = request.form["entered_number"]
        except KeyError:
            print('not entered_number')
            entered_number = None
        
        ok = 'ok' in request.form # True только если кнопка 'ok' после каждого раунда
        
        if 'ok_win' in request.form:
            try:
                fight_row = Fight(select_pokemon=session['select_pokemon'],
                                  vs_pokemon=session['vs_pokemon'],
                                  win=winner() == session['select_pokemon'])
                db.session.add(fight_row)
                db.session.commit()
                return redirect(url_for('pokemons'))
            except Exception:
                print("Failed to add!")
                db.session.rollback()
            

        # если в форме пришло имя покемона - сохранить его
        if your_pokemon_name:
            # почистить сессию перед новым боем
            session.clear()
            # запомнить выбранного покемона
            session['select_pokemon'] = your_pokemon_name
            your_pokemon = get_pokemon_info(session['select_pokemon'])
            session['select_pokemon_hp'] = your_pokemon['hp']
            session['select_pokemon_attack'] = your_pokemon['attack']
        
        # если покемона уже выбрали
        if 'select_pokemon' in session:
            # если противника ещё не назначили
            if 'vs_pokemon' not in session:
                # выбор рандомного (не такого же) 
                pokemon_list, page_count = get_pokemon_list(offset=0, limit=1)
                pokemon_list, page_count = get_pokemon_list(offset=0, limit=page_count * limit)
                vs_pokemon_name = random.choice([pokemon for pokemon in pokemon_list if pokemon != session['select_pokemon']])['name']

                session['vs_pokemon'] = vs_pokemon_name
                vs_pokemon = get_pokemon_info(session['vs_pokemon'])
                session['vs_pokemon_hp'] = vs_pokemon['hp']
                session['vs_pokemon_attack'] = vs_pokemon['attack']
                
            # кнопка OK и ещё не вычитали hp - attack
            if ok and 'entered_number' in session:
                round_win = decrease_hp(session['entered_number'], session['vs_pokemon_number'], run=True)
                session.pop('entered_number', None)
                session.pop('vs_pokemon_number', None)
                
            # если отправили число
            if entered_number:
                # если отправленное число корректное - страница с числом вместо формы
                if entered_number.isdigit() and int(entered_number) in list(range(1, 11)):
                   
                    session['entered_number'] = int(entered_number)
                    
                    if 'vs_pokemon_number' not in session:
                        vs_pokemon_number = random.randint(1, 10)
                        session['vs_pokemon_number'] = vs_pokemon_number
                    
                    round_win = decrease_hp(session['entered_number'], session['vs_pokemon_number'], run=False)

                    return render_template('fight_page.html',
                                            pokemon=get_pokemon_info(session['select_pokemon']), 
                                            vs_pokemon=get_pokemon_info(session['vs_pokemon']),
                                            round_win=round_win)
            
            # если нет числа или число некорректное - пустая форма
            return render_template('fight_page.html',
                                    pokemon=get_pokemon_info(session['select_pokemon']), 
                                    vs_pokemon=get_pokemon_info(session['vs_pokemon']),
                                    global_win=define_global_win(),
                                    winner=get_pokemon_info(winner()))
                
    # если покемон не выбран | без отправки формы запрос страницы - в список 
    return redirect(url_for('pokemons'))
        
        
@app.route("/fight-archive")
def archive():
    fights = Fight.query.all()
    return render_template('fight_archive.html', 
                           fights=fights,
                           thead=['№', 'select', 'vs', 'win'])


if __name__ == '__main__':
    app.run(port=8000, debug=True)
    