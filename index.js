let podcasts = [];
let spotify = null;

function convert_description(desc) {
    return desc.replace("\n", "<br>\n");
}

function make_spotify_buttons() {
    if (spotify) {
        document.querySelectorAll('.episode').forEach(episode => {
            episode.addEventListener('click', () => {
                spotify.loadUri(episode.dataset.spotifyId);
            });
        });
    }
}

async function render(podcasts, sorting) {
    let nlBaseCompare = new Intl.Collator("nl", {sensitivity: "base"}).compare;

    document.getElementById("podcast-count").innerText = podcasts.length;

    podcasts.filter(p => p).forEach(p => {
        let name = p.spotify_data.name;
        let publisher = p.spotify_data.publisher;
        let image = p.spotify_data.images[0].url;
        let description = convert_description(p.spotify_data.description);
        let id = p.spotify_data.id;
        let episodes = p.spotify_data.episodes.items;

        let newest_episode = "";
        let episodes_content = "";
        episodes.filter(e => e).forEach(e => {
            if (e.release_date > newest_episode) {
                newest_episode = e.release_date;
            }
            episodes_content += `<div class="d-flex flex-column flex-sm-row justify-content-between align-items-start p-3 mb-2">
  <div class="flex-grow-1 w-100">
    <small>${e.release_date}</small>
    <h6 class="mb-1 mt-1">${e.name}</h6>
    <small class="text-muted podcast-description">${convert_description(e.description)}</small>
  </div>

  <button class="btn btn-primary mt-3 mt-sm-0 ms-0 ms-sm-3 align-self-sm-center episode" data-spotify-id="${e.uri}">
    ▶
  </button>
</div>`
        });
        p["newest_episode"] = newest_episode;
        p["content"] = `<li class="list-group-item">
  <div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center">
    <img src="${image}" class="rounded me-0 mb-3 mb-sm-0 me-sm-3 podcast-thumb" alt="Thumbnail">

    <div class="flex-grow-1">
        <small class="text-muted">Laatste aflevering: ${newest_episode}</small>
        <h6 class="mb-1 mt-1">${name}</h6>
        <p><small class="podcast-description">${description}</small></p>
        <p><small class="podcast-description">Gepubliceerd door: ${publisher}</small></p>
        <p><small><a href="${p.spotify}" class="muted">Spotify</a>${p.apple ? ", <a href='" + p.apple + "'>Apple Podcasts</a>, <a href='" + p.apple_data[0].feedUrl + "'>RSS</a>" : ""}</small></p>
    </div>

    <button class="btn btn-primary mt-3 mt-sm-0 ms-0 ms-sm-3 accordion-toggle" type="button"
      data-bs-toggle="collapse" data-bs-target="#collapse-${id}" aria-expanded="false" aria-controls="collapse-${id}">
      Afleveringen
    </button>
  </div>

  <div class="collapse mt-3" id="collapse-${id}">
      ${episodes_content}
  </div>
</li>`
    });
    podcasts.sort((p1, p2) => {
        if (sorting === "date") {
            return p1["newest_episode"] > p2["newest_episode"] ? -1 : 1;
        } else if (sorting === "search") {
            // These results come pre-sorted
            return 0;
        } else {
            return nlBaseCompare(p1.spotify_data.name.trim(), p2.spotify_data.name.trim());
        }
    });

    let content = podcasts.reduce((tot, p) => tot += p["content"], "");
    document.getElementById("podcasts").innerHTML = content;

    make_spotify_buttons();
}

async function main() {
    podcasts = await fetch("podcasts.json").then(x => x.json());
    render(podcasts, "alphabetical").then(() => {
        window.onSpotifyIframeApiReady = (IFrameAPI) => {
            const element = document.getElementById('embed-iframe');
            const options = {};
            const callback = (EmbedController) => {
                spotify = EmbedController;
                EmbedController.addListener('ready', () => {
                    EmbedController.play();
                });
                make_spotify_buttons();
            };
            IFrameAPI.createController(element, options, callback);
        };
    });
}

async function search(text) {
    if (text.trim() === "") {
        let sorting = document.querySelector('input[name="sorting"]:checked').value;
        render(podcasts, sorting);
        return;
    }
    const fuse = new Fuse(podcasts, {
        keys: [
            {
                name: "spotify_data.name",
                weight: 10
            },
            {
                name: "spotify_data.publisher",
                weight: 10
            },
            {
                name: "spotify_data.description",
                weight: 3
            },
            {
                name: "spotify_data.episodes.items.name",
                weight: 1
            },
            {
                name: "spotify_data.episodes.items.description",
                weight: 0.5
            }
        ]
    });
    let results = fuse.search(text, {
        "ignoreDiacritics": true,
        "threshold": 0,
        "ignoreLocation": true
    });
    results = results.map(x => x.item);
    await render(results, "search");
}

main();
