from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def get_weblio_info(word):
    url = f"https://www.weblio.jp/content/{word}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=5)
    soup = BeautifulSoup(response.text, "html.parser")

    meaning_elem = soup.select_one(".kiji .content-explanation")
    pos_elem = soup.select_one(".kiji .POS")

    meaning = meaning_elem.text.strip() if meaning_elem else "未找到释义"
    pos = pos_elem.text.strip() if pos_elem else "未知词性"

    return {
        "meaning": meaning,
        "pos": pos
    }

def get_ojad_accent(word):
    search_url = "https://www.gavo.t.u-tokyo.ac.jp/ojad/search/index"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.post(search_url, data={
        "word": word,
        "accent_type": "all"
    }, headers=headers, timeout=5)

    soup = BeautifulSoup(response.text, "html.parser")
    accent_tag = soup.select_one(".table.table-bordered tbody tr td span.accent")
    if accent_tag:
        return accent_tag.text.strip()
    return "无重音信息"

def get_word_info(word):
    info = {"word": word}
    try:
        weblio = get_weblio_info(word)
        accent = get_ojad_accent(word)
        info.update(weblio)
        info["accent"] = accent
    except Exception as e:
        info["error"] = f"查询失败: {str(e)}"
    return info

@app.route('/api/word', methods=['GET'])
def get_word_info_api():
    word = request.args.get('word')
    if not word:
        return jsonify({"error": "参数 'word' 是必须的"}), 400

    info = get_word_info(word)
    if "error" in info:
        return jsonify({"error": info["error"]}), 500

    return jsonify(info)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
