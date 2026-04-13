let podcasts = [];
let spotify = null;

function convert_description(desc) {
    return desc.replace("\n", "<br>\n");
}

function make_play_buttons() {
    document.querySelectorAll('.episode').forEach(episode => {
        if (episode.dataset.streamUrl) {
            episode.addEventListener('click', () => {
                document.querySelector(".podcast-frame").innerHTML =
                `<audio src="${episode.dataset.streamUrl}" controls autoplay>`
            });
        } else {
            // episode.remove();
        }
    });
}

async function render(podcasts, sorting) {
    let nlBaseCompare = new Intl.Collator("nl", {sensitivity: "base"}).compare;

    document.getElementById("podcast-count").innerText = podcasts.length;

    podcasts.filter(p => p).forEach(p => {
        let isApple = !!p.apple_data;

        let name = isApple ? p.apple_data[0].collectionName : p.spotify_data.name;
        let publisher = isApple ? p.apple_data[0].artistName : "";
        let image = isApple ? p.apple_data[0].artworkUrl600 : p.spotify_data.images[0].url;
        let description = isApple ? "" : convert_description(p.spotify_data.description);
        let id = isApple ? p.apple_data[0].collectionId : p.spotify_data.id;
        let episodes = isApple ? p.apple_data.slice(1) : [];

        let newest_episode = "";
        let episodes_content = "";
        episodes.filter(e => e).forEach(e => {
            let release_date = isApple ? 
                new Date(e.releaseDate).toISOString().replace("T", " ").split(".")[0] : 
                e.release_date;
            let name = isApple ? e.trackName : e.name;
            let description = isApple ? e.description : e.description;
            let episodeUrl = isApple ? e.episodeUrl : e.external_urls.spotify;
            if (release_date > newest_episode) {
                newest_episode = release_date;
            }
            let episode_play = ``;
            if (isApple) {
                episode_play = `<button class="btn btn-primary mt-3 mt-sm-0 ms-0 ms-sm-3 align-self-sm-center episode" data-stream-url="${episodeUrl}">
    ▶
  </button>`
            }
            episodes_content += `<div class="d-flex flex-column flex-sm-row justify-content-between align-items-start p-3 mb-2">
  <div class="flex-grow-1 w-100">
    <small>${release_date}</small>
    <h6 class="mb-1 mt-1">${name}</h6>
    <small class="text-muted podcast-description">${convert_description(description)}</small>
  </div>
    ${episode_play}
</div>`
        });
        p["newest_episode"] = newest_episode;
        p["content"] = `<li class="list-group-item">
  <div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center">
    <img src="${image}" class="rounded me-0 mb-3 mb-sm-0 me-sm-3 podcast-thumb" alt="Thumbnail">

    <div class="flex-grow-1">
        ${newest_episode ? `<small class="text-muted">Laatste aflevering: ${newest_episode}</small>` : ``}
        <h6 class="mb-1 mt-1">${name}</h6>
        <!--p><small class="podcast-description">${description}</small></p-->
        ${publisher ? `<p><small class="podcast-description">${publisher}</small></p>` : ``}
        <p><small>${isApple ? "<a href='" + p.spotify + "'>Spotify</a>, <a href='" + p.apple + "'>Apple Podcasts</a>, <a href='" + p.apple_data[0].feedUrl + "'>RSS</a>" : ""}</small></p>
    </div>
    ${isApple ? 
        `<button class="btn btn-primary mt-3 mt-sm-0 ms-0 ms-sm-3 accordion-toggle" type="button"
            data-bs-toggle="collapse" data-bs-target="#collapse-${id}" aria-expanded="false" aria-controls="collapse-${id}">
            Afleveringen
        </button>`
        :
        `<a class="btn btn-primary mt-3 mt-sm-0 ms-0 ms-sm-3" href="${p.spotify}" target="_blank">
            Open&nbsp;op&nbsp;Spotify&nbsp;🗗
        </a>`
    }
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
            let isApple1 = !!p1.apple_data;
            let name1 = isApple1 ? p1.apple_data[0].collectionName : p1.spotify_data.name;
            let isApple2 = !!p2.apple_data;
            let name2 = isApple2 ? p2.apple_data[0].collectionName : p2.spotify_data.name;
            name1 = name1.trim();
            name2 = name2.trim();
            
            return nlBaseCompare(name1, name2);
        }
    });

    let content = podcasts.reduce((tot, p) => tot += p["content"], "");
    document.getElementById("podcasts").innerHTML = content;

    make_play_buttons();
}

async function main() {
    podcasts = await fetch("podcasts.json").then(x => x.json());
    render(podcasts, "alphabetical").then(() => {
        make_play_buttons();
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
