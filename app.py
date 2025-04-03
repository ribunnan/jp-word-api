from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

def get_weblio_info(word):
    url = f"https://www.weblio.jp/content/{word}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return {
            "meaning": f"Weblio 请求失败: {e}",
            "pos": "未知",
        }

    soup = BeautifulSoup(response.text, "html.parser")

    # 释义
    meaning_elem = (
        soup.select_one(".kiji .content-explanation")
        or soup.select_one(".kiji .NetDicBody")
        or soup.select_one(".Kejje")
    )
    meaning = meaning_elem.get_text(strip=True) if meaning_elem else "未找到释义"

    # 词性
    pos_elem = soup.select_one(".kiji .POS") or soup.find("span", class_="prop POS")
    pos = pos_elem.get_text(strip=True) if pos_elem else "未知词性"

    return {
        "meaning": meaning,
        "pos": pos
    }

def get_ojad_accent(word):
    search_url = "https://www.gavo.t.u-tokyo.ac.jp/ojad/search/index"
    try:
        response = requests.post(search_url, data={
            "word": word,
            "accent_type": "all"
        }, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return f"OJAD 请求失败: {e}"

    soup = BeautifulSoup(response.text, "html.parser")

    # 找到第一个音调标记
    accent_tag = soup.select_one("span.accent")
    if accent_tag:
        return accent_tag.get_text(strip=True)

    return "无重音信息"

def get_word_info(word):
    info = {"word": word}
    try:
        weblio = get_weblio_info(word)
        accent = get_ojad_accent(word)
        info.update(weblio)
        info["accent"] = accent
    except Exception as e:
        info["error"] = f"查询失败: {e}"
    return info

@app.route('/api/word', methods=['GET'])
def get_word_info_api():
    word = request.args.get('word')
    if not word:
        return jsonify({"error": "缺少参数 word"}), 400

    info = get_word_info(word)
    return jsonify(info)

if __name__ == '__main__':
    # Render 要求绑定 0.0.0.0 和动态端口
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
