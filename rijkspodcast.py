import json
import os
import re
import sys
import time

import requests
import spotipy


def get_podcast_info(spotify_url):
    match = re.search(r"spotify\.com/show/([a-zA-Z0-9]+)", spotify_url)
    if not match:
        raise ValueError("Invalid Spotify podcast URL.")

    show_id = match.group(1)

    if os.environ.get("SPOTIFY_CLIENT_ID"):
        credentials = {
            "client_id": os.environ["SPOTIFY_CLIENT_ID"],
            "client_secret": os.environ["SPOTIFY_CLIENT_SECRET"]
        }
    else:
        credentials = json.load(open("spotify-credentials.json"))
    auth_manager = spotipy.oauth2.SpotifyClientCredentials(
        client_id=credentials["client_id"],
        client_secret=credentials["client_secret"]
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)

    show = sp.show(show_id)
    if show["episodes"]["next"]:
        i = 1
        while True:
            response = sp.show_episodes(show_id, limit=50, offset=50 * i)
            show["episodes"]["items"].extend(response["items"])
            if response['next']:
                i += 1
            else:
                break
    return show

def get_apple_podcasts_id(s):
    m = re.search(r'\d+$', s)
    return m.group() if m else None

def add_podcasts():
    while True:
        name = input("Enter the URL of the podcast: ")
        url = name
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
            apple = input("Apple URL: ")
            if apple:
                apple_data = requests.get("https://itunes.apple.com/lookup?id=" + get_apple_podcasts_id(apple)).json()["results"][0]
            else:
                apple_data = None
            podcasts.append({"provider": provider, "url": url, "data": results, "apple": apple, "apple_data": apple_data})
            json.dump(podcasts, open("podcasts.json", "w"), indent=2)

def update_podcasts():
    podcasts = json.load(open("podcasts.json"))
    for podcast in podcasts:
        podcast["data"] = get_podcast_info(podcast["url"])
        print(podcast["data"]["name"])
        time.sleep(0.1)
    json.dump(podcasts, open("podcasts.json", "w"), indent=2)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        add_podcasts()
    else:
        if sys.argv[1] == "update":
            update_podcasts()