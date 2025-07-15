import json
import re

import requests
import spotipy


def get_podcast_info(spotify_url):
    # Extract the show ID from the URL
    match = re.search(r"spotify\.com/show/([a-zA-Z0-9]+)", spotify_url)
    if not match:
        raise ValueError("Invalid Spotify podcast URL.")

    show_id = match.group(1)

    credentials = json.load(open("spotify-credentials.json"))
    # Authenticate using client credentials
    auth_manager = spotipy.oauth2.SpotifyClientCredentials(
        client_id=credentials["client_id"],
        client_secret=credentials["client_secret"]
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)

    # Get podcast info
    return sp.show(show_id)

def get_trailing_number(s):
    m = re.search(r'\d+$', s)
    return m.group() if m else None

while True:
    name = input("Enter the URL of the podcast: ")
    url = name
    provider = ""
    results = None
    if "podcasts.apple.com" in name:
        name = get_trailing_number(name)
        data = requests.get("https://itunes.apple.com/lookup?id=" + name).json()
        results = data["results"][0]
        provider = "apple"
    elif "spotify.com" in name:
        results = get_podcast_info(name)
        provider = "spotify"

    if url.strip() == "":
        continue

    podcasts = json.load(open("podcasts.json"))
    exists = False
    for podcast in podcasts:
        if url == podcast["url"]:
            exists = True
            print("Podcast al eerder toegevoegd!")

    if not exists:
        podcasts.append({"provider": provider, "url": url, "data": results})
        json.dump(podcasts, open("podcasts.json", "w"), indent=2)

