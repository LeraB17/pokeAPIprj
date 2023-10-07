from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

limit = 10

def get_pokemon_list(offset=0, limit=10):
    url = f"https://pokeapi.co/api/v2/pokemon/?offset={offset}&limit={limit}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()  
        pokemon_list = data.get("results", [])
        all_poke_count = data['count']
        return pokemon_list, int(all_poke_count / limit + 1)
    else:
        print(f"Error: {response.status_code}")
        return [], 0


def get_page_list(cur_page=1, final_page=1):
    left = cur_page - 3 if cur_page >= 4 else 1
    right = cur_page + 3 if final_page - cur_page >= 3 else final_page
    return list(range(left, right + 1))


def get_pokemon_info(pokemon_name):
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
    else:
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
    
    pokemon_list = [get_pokemon_info(pokemon["name"]) for pokemon in pokemon_list]
    
    return render_template("list.html", 
                           pokemons=pokemon_list, 
                           page_list=get_page_list(page, page_count), 
                           current=page, 
                           final_page=page_count)


@app.route("/pokemon/<string:pokemon_name>")
def pokemon_page(pokemon_name):
    pokemon = get_pokemon_info(pokemon_name)
    return render_template("pokemon_page.html", pokemon=pokemon)
    
    
@app.route("/fight")
def fight():
    your_pokemon_name = request.args.get('select_pokemon')
    your_pokemon = get_pokemon_info(your_pokemon_name)
    
    rnd_pokemon = get_pokemon_info('poliwhirl')
    
    return render_template('fight_page.html', 
                           pokemon=your_pokemon, 
                           rnd_pokemon=rnd_pokemon)
    

@app.route("/search")
def search():
    pokemon_name = request.args.get('search_string')
    if pokemon_name.strip() == "":
        return redirect(url_for("pokemons"))
    else:
        pokemon = get_pokemon_info(pokemon_name)
        return render_template("list.html", 
                               pokemons=[pokemon], 
                               search_string=pokemon_name)


if __name__ == '__main__':
    app.run(port=8000, debug=True)
    