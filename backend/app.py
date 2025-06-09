from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

import spacy
import os
import requests

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)  

load_dotenv()

# Load trained model
nlp = spacy.load("backend/football_ner_model") 


api_key = os.getenv("API_FOOTBALL_KEY") 
headers = {"x-apisports-key": api_key}

@app.route("/analyze", methods=["POST"])
def analyze():
    text = request.json.get("text", "")
    doc = nlp(text)
    
    results = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
    return jsonify(results)

@app.route("/player_info", methods=["POST"])
def get_player_info():
    import requests
    data = request.get_json()
    player_name = data.get("player", "").split()

    first_name = player_name[0]
    last_name = player_name[-1]

    url = "https://v3.football.api-sports.io/players/profiles"
    
    
    params = {
        "search": last_name,
    }

    response = requests.get(url, headers=headers, params=params)
    print("API response JSON:", response.json())
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch player info"}), 500

    results = response.json().get("response", [])
    if not results:
        return jsonify({"error": "Player not found"}), 404
    
    # Find player matching the first name
    matched_player = None
    for entry in results:
        player = entry.get("player")

        if not isinstance(player, dict):
            continue
        
        firstname_api = player.get("firstname")
        lastname_api = player.get("lastname")

        if isinstance(firstname_api, str):
            print(f"Comparing '{firstname_api.strip().lower()}' to '{first_name.strip().lower()}'")
        if isinstance(firstname_api, str) and first_name.strip().lower() in firstname_api.strip().lower() and last_name.strip().lower() in lastname_api.strip().lower():
            matched_player = entry
            break

    if not matched_player:
        return jsonify({"error": "Player not found with matching first name"}), 404

    
    player_data = matched_player.get("player", {})
    birth = player_data.get("birth", {})
    return jsonify({
        "photo": player_data.get("photo"),
        "nationality": player_data.get("nationality"),
        "age": player_data.get("age"),
        "date_of_birth": birth.get("date"),
        "position": player_data.get("position"),
        "height": player_data.get("height"),
        "weight": player_data.get("weight"),
    }) 

@app.route("/club_info", methods=["POST"])
def club_info():
    data = request.get_json()
    club_name = data.get("club")

    if not club_name:
        return jsonify({"error": "Missing club name"}), 400

    team_url = "https://v3.football.api-sports.io/teams"
    team_params = {
        "search": club_name
    }

    team_response = requests.get(team_url, headers=headers, params=team_params)
    team_data = team_response.json()
    print("API response JSON (club):", team_data)

    if not team_data.get("response"):
        return jsonify({"error": "Club not found"}), 404

    team = team_data["response"][0]["team"]
    venue = team_data["response"][0]["venue"]

    return jsonify({
        "logo": team.get("logo"),
        "city_country": f'{venue.get("city")}, {team.get("country")}',
        "founded": team.get("founded"),
        "venue": venue.get("name")
    })

if __name__ == "__main__":
    app.run(debug=True)