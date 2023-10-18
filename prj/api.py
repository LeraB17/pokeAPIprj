from flask import request, make_response, jsonify
import requests
from flask import Blueprint
import random

api_app = Blueprint('route', __name__)

default_limit = 10

# получение инфы по 1 покемону
@api_app.route('/api/pokemon/<string:id>', methods=["GET"])
def api_get_pokemon_info(id):
    url = f"https://pokeapi.co/api/v2/pokemon/{id}/"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        stats = data["stats"]
        
        hp = next((x for x in stats if x["stat"]["name"] == "hp"), None)
        attack = next((x for x in stats if x["stat"]["name"] == "attack"), None)
        defense = next((x for x in stats if x["stat"]["name"] == "defense"), None)
        speed = next((x for x in stats if x["stat"]["name"] == "speed"), None)
        
        res = make_response({
            "id": data["id"],
            "name": data["name"],
            "image": data["sprites"]["front_default"],
            "hp": hp["base_stat"] if hp else None,
            "attack": attack["base_stat"] if attack else None,
            "defense": defense["base_stat"] if defense else None,
            "speed": speed["base_stat"] if speed else None,
        }, 200)

    else:
        res = make_response("Not found pokemon", response.status_code)
    return res


# получение списка покемонов со всей инфой для 1 страницы с учётом поиска
@api_app.route('/api/pokemon/list', methods=["GET"])
def api_get_pokemon_list():
    # получить параметры для фильтрации списка (номер страницы, кол-во на 1 странице и строку поиска)
    page = request.args.get('page')
    page = int(page) if page and page.isdigit() else 1
    limit = request.args.get('limit')
    limit = int(limit) if limit and limit.isdigit() else default_limit
    q = request.args.get('q', '')

    # запрос для получения общего количества покемонов
    url = f"https://pokeapi.co/api/v2/pokemon"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        all_poke_count = data['count']
        
        # запрос для получения списка всех покемонов 
        url = f"https://pokeapi.co/api/v2/pokemon/?offset=0&limit={all_poke_count}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()  
            pokemon_list = data.get("results", [])
            all_poke_count = data["count"]

            # фильтрация списка по содержанию строки поиска
            if q.strip() != "":
                pokemon_list = [pokemon for pokemon in pokemon_list if q.strip() in pokemon['name']]
                all_poke_count = len(pokemon_list)

            # получение списка покемонов для 1 страницы (пагинация)
            offset = (page - 1) * limit
            pokemon_list = pokemon_list[offset : offset+limit]
            
            # формирование ответа
            res = {
                "pokemons": [api_get_pokemon_info(pokemon['name']).json for pokemon in pokemon_list],
                "count": all_poke_count,
                "pages": int(all_poke_count / limit) + int(all_poke_count % limit > 0)
            }
            return make_response(res, 200)  
    return make_response("Error", response.status_code)
    
    
# получение рандомного покемона
@api_app.route('/api/pokemon/random', methods=["GET"])
def api_get_random_pokemon():
    # получить id выбранного покемона, чтобы он сам с собой не дрался
    id_current = request.args.get('id')
    id_current = int(id_current) if id_current and id_current.isdigit() else None
    
    # запрос для получения общего количества покемонов
    url = f"https://pokeapi.co/api/v2/pokemon"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        all_poke_count = data['count']
        
        # выбор рандомного id (с/без учёта совпадения с выбранным покемоном)
        ids = [i for i in range(1, all_poke_count) if i != id_current] if id_current else [i for i in range(1, all_poke_count)] 
        res = {
            "id": random.choice(ids)
        }
        return make_response(res, 200)
    return make_response("Error", response.status_code)


# получение инфы о противниках
@api_app.route('/api/fight', methods=["GET"])
def api_fight():
    # получение id выбранного покемона и противника + проверка на корректность
    try:
        id_select = int(request.args.get('id_select'))
        id_vs = int(request.args.get('id_vs'))
    except (ValueError, TypeError):
        return make_response("Uncorrect ids", 400)

    # получение инфы по 2 покемонам 
    select_pokemon = api_get_pokemon_info(id_select)
    vs_pokemon = api_get_pokemon_info(id_vs)
    
    if select_pokemon.status_code == 200 and vs_pokemon.status_code == 200:
        res = {
            "select_pokemon": select_pokemon.json,
            "vs_pokemon": vs_pokemon.json,
        }
        return make_response(res, 200)
    return make_response("Error: not found pokemons", 404)


# отправка хода и обновление инфы о состояниии покемонов
@api_app.route('/api/fight/<int:number>', methods=["POST"])
def api_attack(number):
    select_pokemon = request.json['select_pokemon']
    vs_pokemon = request.json['vs_pokemon']
    
    # если данные корректны
    if select_pokemon and vs_pokemon and number in list(range(1, 11)):
        if 'id' in select_pokemon and 'hp' in select_pokemon and 'attack' in select_pokemon:
            if 'id' in vs_pokemon and 'hp' in vs_pokemon and 'attack' in vs_pokemon:
                hp_select = select_pokemon['hp']
                hp_vs = vs_pokemon['hp']
                round_winner = None
                
                # генерация числа противника
                vs_number = random.randint(1, 10)
                
                # проверка кто атакует и пересчёт hp
                if hp_vs > 0 and hp_select > 0:
                    if number % 2 == vs_number % 2:
                        hp_vs -= select_pokemon['attack']
                        round_winner = select_pokemon['id']
                    else:
                        hp_select -= vs_pokemon['attack']
                        round_winner = vs_pokemon['id']
                    
                # проверка победителя
                winner = None
                if hp_select <= 0:
                    winner = vs_pokemon['id']
                elif hp_vs <= 0:
                    winner = select_pokemon['id']
                    
                # формирование ответа
                res = {
                    "select_pokemon": {
                        "id": select_pokemon['id'],
                        "hp": hp_select,
                        "attack": select_pokemon['attack'],
                    },
                    "vs_pokemon": {
                        "id": vs_pokemon['id'],
                        "hp": hp_vs,
                        "attack": vs_pokemon['attack'],
                    },
                    "round": [{
                            "number": number,
                            "hp": hp_select,
                        }, 
                        {
                            "number": vs_number,
                            "hp": hp_vs,
                        }, 
                        round_winner],
                    "winner": winner,
                }
                return make_response(res, 200)         
    return make_response("Uncorrect data", 400)

# быстрый бой
@api_app.route('/api/fight/fast', methods=["GET"])
def api_fast_fight():
    # получение id покемонов
    try:
        id_select = int(request.args.get('id_select'))
        id_vs = int(request.args.get('id_vs'))
    except (ValueError, TypeError):
        return make_response("Uncorrect ids", 400)
    
    # получение инфы по 2 покемонам 
    select_pokemon = api_get_pokemon_info(id_select)
    vs_pokemon = api_get_pokemon_info(id_vs)
    
    if select_pokemon.status_code != 200 or vs_pokemon.status_code != 200:
        return make_response("Not found pokemos", 404)
    
    select_pokemon = select_pokemon.json
    vs_pokemon = vs_pokemon.json
    
    hp_select = select_pokemon['hp']
    hp_vs = vs_pokemon['hp']
                
    rounds = [] # история раундов
    
    # раунды, пока у кого-нибудь не закончится hp
    while hp_select >= 0 and hp_vs >= 0:
        number = random.randint(1, 10)
        vs_number = random.randint(1, 10)
        
        round_winner = None
        # проверка кто атакует и пересчёт hp
        if number % 2 == vs_number % 2:
            hp_vs -= select_pokemon['attack']
            round_winner = select_pokemon['id']
        else:
            hp_select -= vs_pokemon['attack']
            round_winner = vs_pokemon['id']
        # запись в историю раундов
        rounds.append([{
            "number": number,
            "hp": hp_select,
        }, 
        {
            "number": vs_number,
            "hp": hp_vs,
        }, round_winner])
            
    # проверка победителя
    winner = None
    if hp_select <= 0:
        winner = vs_pokemon['id']
    elif hp_vs <= 0:
        winner = select_pokemon['id']
                        
    # формирование ответа
    res = {
        "select_pokemon": {
            "id": select_pokemon['id'],
            "name": select_pokemon['name'],
            "hp": hp_select,
            "attack": select_pokemon['attack'],
        },
        "vs_pokemon": {
            "id": vs_pokemon['id'],
            "name": vs_pokemon['name'],
            "hp": hp_vs,
            "attack": vs_pokemon['attack'],
        },
        "rounds": rounds,
        "winner": winner,
    }
    return make_response(res, 200) 
                
