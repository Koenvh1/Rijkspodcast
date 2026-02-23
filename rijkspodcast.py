import json
import os
import re
import sys
import time
import urllib

import xml.etree.ElementTree as ET

import requests
import spotipy


def get_podcast_info(spotify_url):
    match = re.search(r"spotify\.com/show/([a-zA-Z0-9]+)", spotify_url)
    if not match:
        raise ValueError("Invalid Spotify podcast URL.")

    show_id = match.group(1)

    # Use environment variables if possible
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
    sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=10, retries=10)

    show = sp.show(show_id)
    if show["episodes"]["next"]:
        # Spotify has a 50 episode limit per page
        i = 1
        while True:
            response = sp.show_episodes(show_id, limit=50, offset=50 * i)
            show["episodes"]["items"].extend(response["items"])
            if response['next']:
                i += 1
            else:
                break
    return show

def get_apple_podcast_info(apple_url):
    apple = get_apple_podcasts_id(apple_url)
    apple_data = requests.get(
        "https://itunes.apple.com/lookup?id=" + get_apple_podcasts_id(apple) + "&entity=podcastEpisode&country=NL&lang=nl_nl&limit=200"
    ).json()["results"]
    for idx, result in enumerate(apple_data):
        apple_data[idx] = {k: v for k, v in sorted(result.items(), key=lambda item: item[0])}
    return apple_data

def get_apple_podcasts_id(s):
    m = re.search(r'\d+$', s)
    return m.group() if m else None

def add_podcasts():
    while True:
        name = input("Enter the URL of the podcast: ")
        spotify = name
        spotify_data = get_podcast_info(name)
        provider = "spotify"

        if spotify.strip() == "":
            continue

        podcasts = json.load(open("podcasts.json"))
        exists = False
        for podcast in podcasts:
            if spotify == podcast["spotify"]:
                exists = True
                print("Podcast al eerder toegevoegd!")

        if not exists:
            apple = input(f"Apple URL https://podcasts.apple.com/nl/search?term={urllib.parse.quote_plus(spotify_data["name"])} : ")
            if apple:
                apple_data = get_apple_podcast_info(apple)
            else:
                apple_data = None
            podcasts.append({
                "provider": provider,
                "spotify": spotify,
                "spotify_data": spotify_data,
                "apple": apple,
                "apple_data": apple_data
            })
            json.dump(podcasts, open("podcasts.json", "w"), indent=2)
            generate_opml()

def generate_opml():
    root = ET.Element("opml")
    root.set("version", "1.0")
    head = ET.SubElement(root, "head")
    title = ET.SubElement(head, "title")
    title.text = "Rijkspodcastregister podcasts"

    body = ET.SubElement(root, "body")

    podcasts = json.load(open("podcasts.json"))
    total = len(podcasts)
    for idx, podcast in enumerate(podcasts):
        if not podcast["apple"]:
            continue
        outline = ET.SubElement(body, "outline")
        outline.set("type", "rss")
        outline.set("text", podcast["spotify_data"]["name"])
        outline.set("title", podcast["spotify_data"]["name"])
        outline.set("xmlUrl", podcast["apple_data"][0]["feedUrl"])

    tree = ET.ElementTree(root)
    ET.indent(tree, space="\t", level=0)
    tree.write("rijkspodcastregister.opml", encoding="utf-8", xml_declaration=True)

def generate_feed():
    root = ET.Element("feed")
    root.set("xmlns", "http://www.w3.org/2005/Atom")
    title = ET.SubElement(root, "title")
    title.text = "Rijkspodcastregister"
    summary = ET.SubElement(root, "subtitle")
    summary.text = "Dit zijn de nieuwste afleveringen van podcasts " \
    "geproduceerd door, in opdracht van, of in samenwerking met de Rijksoverheid."
    link = ET.SubElement(root, "link")
    link.set("href", "https://rijkspodcast.koenvh.nl")
    updated = ET.SubElement(root, "updated")
    updated.text = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    author = ET.SubElement(root, "author")
    author_name = ET.SubElement(author, "name")
    author_name.text = "Koen van Hove"
    feed_id = ET.SubElement(root, "id")
    feed_id.text = "urn:uuid:c63bba2d-b196-4dc4-ae5d-312e0894f8f0"

    podcasts = json.load(open("podcasts.json"))
    episodes = []
    for podcast in podcasts:
        if not podcast["apple"]:
            continue
        for episode in podcast["apple_data"][1:]:
            if episode:
                episode["podcast"] = podcast["apple_data"][0]
                episodes.append(episode)
    episodes.sort(key=lambda x: x["releaseDate"], reverse=True)

    total = len(episodes)
    for idx, episode in enumerate(episodes):
        item = ET.SubElement(root, "entry")
        title = ET.SubElement(item, "title")
        title.text = episode["podcast"]["trackName"] + " - " + episode["trackName"]
        link = ET.SubElement(item, "link")
        link.set("href", episode["trackViewUrl"])
        summary = ET.SubElement(item, "summary")
        summary.text = episode["description"]
        # image = ET.SubElement(item, "image")
        # image.text = episode["images"][0]["url"]
        author = ET.SubElement(item, "author")
        author_name = ET.SubElement(author, "name")
        author_name.text = episode["podcast"]["artistName"]
        content = ET.SubElement(item, "content")
        content.set("src", episode["episodeUrl"])
        content.set("type", "audio/mpeg")
        entry_id = ET.SubElement(item, "id")
        entry_id.text = str(episode["trackId"])
        updated = ET.SubElement(item, "updated")
        updated.text = episode["releaseDate"]

    tree = ET.ElementTree(root)
    ET.indent(tree, space="\t", level=0)
    tree.write("feed.xml", encoding="utf-8", xml_declaration=True)

def update_podcasts():
    previous_podcasts = json.load(open("podcasts.json"))
    podcasts = json.load(open("podcasts.json"))
    for podcast in podcasts:
        try:
            podcast["spotify_data"] = get_podcast_info(podcast["spotify"])
            print(podcast["spotify_data"]["name"])
            time.sleep(0.1)
        except spotipy.SpotifyException as e:
            if e.http_status == 404:
                print("NOT FOUND: " + podcast["spotify_data"]["name"])
            else:
                raise e
        if podcast["apple"]:
            podcast["apple_data"] = get_apple_podcast_info(podcast["apple"])

    json.dump(podcasts, open("podcasts.json", "w"), indent=2)
    return previous_podcasts != podcasts

if __name__ == "__main__":
    if len(sys.argv) == 1:
        add_podcasts()
    else:
        if sys.argv[1] == "update":
            updated = update_podcasts()
            print("Podcasts updated: " + str(updated))
            if updated:
                generate_feed()
        elif sys.argv[1] == "opml":
            generate_opml()
        elif sys.argv[1] == "feed":
            generate_feed()