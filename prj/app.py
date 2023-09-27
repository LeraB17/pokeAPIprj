from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

@app.route('/')
def pokemons():
    
    url = "https://pokeapi.co/api/v2/pokemon/"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        poke_count = data['count']
        
        new_url = f"https://pokeapi.co/api/v2/pokemon/?offset=0&limit={poke_count}"
        new_response = requests.get(new_url)
        data = new_response.json()
        
        list_pokemons = data['results']
    
    return render_template("list.html", pokemons=list_pokemons)


@app.route("/search", methods=["POST"])
def search():
    pokemon_name = request.form["search_string"]
    if pokemon_name == "":
        return redirect(url_for("pokemons"))
    else:
        
        url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}/"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            result = {
                "id": data["id"],
                "name": data["name"]
            }
    
            return render_template("list.html", pokemons=result, search_string=pokemon_name)
        else:
            return render_template("list.html", pokemons=[], search_string=pokemon_name)

if __name__ == '__main__':
    app.run(port=8000, debug=True)
    