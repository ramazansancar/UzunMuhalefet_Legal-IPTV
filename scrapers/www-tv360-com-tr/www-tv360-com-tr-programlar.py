import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
import json
import sys

sys.path.insert(0, '../../utilities')
from jsontom3u import create_single_m3u, create_m3us, create_json

base_url = "https://www.tv360.com.tr"

def parse_episode_page(episode_url):
    try:
        r = requests.get(episode_url)
        soup = BeautifulSoup(r.content, "html.parser")
        source_tag = soup.find("source")
        streams = {"stream_url": "", "embed_url": ""}
        if source_tag:
            streams["stream_url"] = source_tag.get("src").strip()
        iframe_tag = soup.find("iframe")
        if iframe_tag:
            streams["embed_url"] = iframe_tag.get("src").strip()
        return streams
    except Exception as e:
        print(f"Error parsing episode page {episode_url}: {e}")
        return {"stream_url": "", "embed_url": ""}

def get_episodes_page(content_url):
    all_episodes = []
    if "ekonomi" in content_url:
        episodes_url = content_url.replace("ekonomi/", "").replace("--", "-") + "-tum-bolumleri"
    else:
        episodes_url = content_url.replace("yasam/", "").replace("--", "-") + "-tum-bolumleri"
    r = requests.get(episodes_url, allow_redirects=False)
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, "html.parser")
        episodes = soup.find("div", {"class": "pragram-list-wrapper"}).find_all("div", {"class": "item"})
        for episode in episodes:
            episode_name = episode.find("div", {"class": "name"}).get_text().strip()
            episode_img = episode.find("img").get("src")
            episode_url = base_url + episode.find("a").get("href")
            temp_episode = {
                "name": episode_name,
                "img": episode_img,
                "url": episode_url
            }
            all_episodes.insert(0,temp_episode)            
    return all_episodes

def get_programs_page(url):
    all_items = []
    #url = "https://www.tv360.com.tr/yasam-programlar"
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    contents = soup.find("div", {"class": "pragram-list-wrapper"}).find_all("div", {"class": "item"})
    for content in contents:
        content_img = content.find("img").get("src")
        content_name = content.find("div", {"class": "name"}).get_text().strip()
        content_url = base_url + content.find("a").get("href")
        #print(content_name, content_url)
        temp_content = {
            "name": content_name,
            "img": content_img,
            "url": content_url
        }
        all_items.append(temp_content)

    return all_items

def main(url, name, start=0, end=0):
    data = []
    programs_list = get_programs_page(url)
    if end == 0:
        end_index = len(programs_list)
    else:
        end_index = end
    for i in tqdm(range(start, end_index)):
        program = programs_list[i]
        print(i, program["name"])
        episodes = get_episodes_page(program["url"])
        if episodes:
            temp_program = program.copy()
            temp_program["episodes"] = []
            for episode in tqdm(episodes):
                streams = parse_episode_page(episode["url"])
                if streams["stream_url"]:
                    episode["stream_url"] = streams["stream_url"]
                if streams["embed_url"]:
                    episode["embed_url"] = streams["embed_url"]
                if streams:
                    temp_program["episodes"].append(episode)
            data.append(temp_program)
    create_single_m3u("../../lists/video/sources/www-tv360-com-tr", data, name)
    create_json("www-tv360-com-tr-" + name + ".json", data)
    create_m3us("../../lists/video/sources/www-tv360-com-tr/" + name, data)

main("https://www.tv360.com.tr/yasam-programlar", "programlar")
main("https://www.tv360.com.tr/arsiv-programlar", "arsiv")
