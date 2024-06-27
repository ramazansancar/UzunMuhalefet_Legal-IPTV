import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
import json
import sys

sys.path.insert(0, '../../utilities')
from jsontom3u import create_single_m3u, create_m3us

site_base_url = "https://www.kanald.com.tr"

def get_dailystream_url(media_secure_path_id):
    url = "https://www.dailymotion.com/player/metadata/video/"+ media_secure_path_id
    try:
        r = requests.get(url)
        data = r.json()
        return data["qualities"]["auto"][0]["url"]
    except:
        return " "

def get_stream_url(media_id):
    url = "https://www.kanald.com.tr/actions/media"
    params = {
        "id": media_id,
        "p": "1",
        "pc": "1",
        "isAMP": "false"
    }
    try:
        r = requests.get(url, params=params)
        data = r.json()["data"]
        if data["media"]["link"]["type"] == "video/dailymotion":
            url = get_dailystream_url(data["media"]["link"]["securePath"])
            return url
        else:
            path = data["media"]["link"]["securePath"].split("?")[0]
            if path[0] != "/":
                path = "/" + path
            url = data["media"]["link"]["serviceUrl"] + path
            return url
    except:
        return " "
 
def parse_bolum_page(url):
    try:
        r = requests.get(url)
        soup = BeautifulSoup(r.content, "html.parser")
        media_id = soup.find("link", {"itemprop": "embedURL"}).get("href").split("/")[-1]
        if media_id:
            return media_id
        return ""
    except:
        return ""

def parse_bolumler_page(url):
    item_list = []
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    items = soup.find("section", {"class": "listing-holder"}).find_all("div", {"class": "item"})
    for item in items:
        item_url = site_base_url + item.find("a").get("href")
        item_img = item.find("img").get("src")
        item_name = item.find("h3", {"class": "title"}).get_text().strip()
        temp_item = {
            "name": item_name,
            "img": item_img,
            "url": item_url
        }
        item_list.append(temp_item)
    return item_list

def get_bolumler_page(url):
    all_items = []
    url = url + "/bolumler"
    r = requests.get(url, allow_redirects=False)
    try:
        soup = BeautifulSoup(r.content, "html.parser")
        if r.status_code == 200:
            pages = soup.find("ul", {"class": "pagination"}).find_all("li")
            for page in pages:
                page_url = r.url + page.find("a").get("href")
                page_items = parse_bolumler_page(page_url)
                all_items = all_items + page_items
        return all_items
    except:
        return all_items

def parse_arsiv_page(url):
    item_list = []
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    items = soup.find("section", {"class": "listing-holder"}).find_all("div", {"class": "item"})
    for item in items:
        item_url = site_base_url + item.find("a").get("href")
        item_img = item.find("img").get("src")
        item_name = item.find("h3", {"class": "title"}).get_text().strip()
        temp_item = {
            "name": item_name,
            "img": item_img,
            "url": item_url
        }
        item_list.append(temp_item)
    return item_list

def get_arsiv_page(url):
    all_items = []
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    pages = soup.find("ul", {"class": "pagination"}).find_all("li")
    for page in pages:
        page_url = r.url + page.find("a").get("href")
        page_items = parse_arsiv_page(page_url)
        all_items = all_items + page_items
    return all_items

def main(url, name, start=0, end=0):
    data = []
    series_list = get_arsiv_page(url)
    if end == 0:
        end_index = len(series_list)
    else:
        end_index = end
    for i in tqdm(range(start, end_index)):
        serie = series_list[i]
        print(i, serie["name"])
        episodes = get_bolumler_page(serie["url"])
        if episodes:
            temp_serie = serie.copy()
            temp_serie["episodes"] = []
            for episode in tqdm(episodes):
                media_url = parse_bolum_page(episode["url"])
                stream_url = get_stream_url(media_url)
                episode["stream_url"] = stream_url
                if stream_url == " ":
                    continue
                elif stream_url:
                    temp_serie["episodes"].append(episode)
                else: 
                    break
            data.append(temp_serie)
    create_single_m3u("../../lists/video/sources/www-kanald-com-tr", data, name)
    f = open("www-kanald-com-tr-" + name + ".json", "w+")
    json.dump(data, f, ensure_ascii=False, indent=4)
    create_m3us("../../lists/video/sources/www-kanald-com-tr/" + name, data)

dizi_arsiv = "https://www.kanald.com.tr/diziler/arsiv"
program_arsiv = "https://www.kanald.com.tr/programlar/arsiv"

main(dizi_arsiv, "arsiv-diziler")
main(program_arsiv, "arsiv-programlar")
