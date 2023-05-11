import requests
import base64
from flask import Flask, request, jsonify
from textblob import TextBlob
from flask_cors import CORS
import openai
import re
import dotenv
dotenv.load_dotenv()
import os

app = Flask(__name__)
cors = CORS(app)


SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
openai.api_key = os.getenv("OPENAI_API_KEY")


@app.route("/analyze", methods=["POST"])
def analyze_mood():
    data = request.get_json()
    message = data["text"]

    # Use the get_mood function to analyze the mood
    mood = get_mood(message)

    # Get song recommendations based on mood from Spotify
    songs = get_songs_by_mood(mood)

    # Get a chatbot response based on the mood
    chatbot_response = get_chatbot_response(mood)

    # Return the mood and song recommendations as a JSON response
    response = {"mood": mood, "songs": songs,"chatbot_response":chatbot_response}
    print (response)
    return jsonify(response)


def get_mood(message):
    # Use TextBlob to analyze the sentiment of the message
    blob = TextBlob(message)
    polarity = blob.sentiment.polarity

    # Determine the mood based on the polarity score

    # Determine the mood based on the polarity score
    if polarity > 0.5:
        mood = "ecstatic"
    elif polarity > 0:
        mood = "happy"
    elif polarity < -0.5:
        mood = "devastated"
    elif polarity < 0:
        mood = "sad"
    else:
        mood = "neutral"

    return mood


def get_songs_by_mood(mood):
    # Get song recommendations based on mood and valence from Spotify
    url = "https://api.spotify.com/v1/recommendations"
    headers = {
        "Authorization": "Bearer " + get_access_token(),
        "Content-Type": "application/json",
    }

    # Set the target valence based on the mood
    if mood == "ecstatic":
        target_valence = 0.8
        genre = "pop"
    elif mood == "happy":
        target_valence = 0.6
        genre = "rock"
    elif mood == "devastated":
        target_valence = 0.2
        genre = "soul"
    elif mood == "sad":
        target_valence = 0.4
        genre = "classical"
    else:
        target_valence = 0.5
        genre = "electronic"

    # Set the request parameters
    params = {
        "seed_genres": genre,
        "target_valence": target_valence,
        "limit": 3,
    }

    # Send the request to the Spotify API
    response = requests.get(url, headers=headers, params=params)

    # Parse the response and extract the song names
    if response.ok:
        tracks = response.json().get("tracks", [])
        songs = []
        for track in tracks:
            song = {
                "name": track.get("name", ""),
                "artist": track.get("artists", [])[0].get("name", ""),
                "album": track.get("album", {}).get("name", ""),
                "url": track.get("external_urls", {}).get("spotify", ""),
            }
            songs.append(song)
    else:
        songs = []

    return songs


def get_access_token():
    # Get access token from Spotify API
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic "
        + base64.b64encode(
            (SPOTIFY_CLIENT_ID + ":" + SPOTIFY_CLIENT_SECRET).encode()
        ).decode(),
    }
    data = {
        "grant_type": "client_credentials",
    }
    response = requests.post(url, headers=headers, data=data)

    if response.ok:
        access_token = response.json().get("access_token", "")
    else:
        access_token = ""

    return access_token


# Define a function to generate a response using GPT-3
def generate_response(prompt):
    # Set the parameters for GPT-3
    model_engine = "text-davinci-002"
    max_tokens = 60
    temperature = 0.7

    # Generate a response using GPT-3
    response = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature
    )

    # Extract the response text from the API response
    response_text = response.choices[0].text.strip()

    # Clean up the response text
    response_text = re.sub(r"\n", "", response_text)

    return response_text

# Define a function to get a response from the chatbot


def get_chatbot_response(user_input):
    prompt = f"The user is feeling {user_input}.Motivate the user. The chatbot says:"
    response = generate_response(prompt)
    return response

if __name__ == "__main__":
    app.run(debug=True)
