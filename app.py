import re
import requests
import yt_dlp
from flask import Flask, request, jsonify, Response, send_from_directory

app = Flask(__name__)
LINK = re.compile(r"^https?://(www\.)?instagram\.com/(p|reel|reels|tv)/[\w-]+", re.I)


def extrair(url):
    opcoes = {"quiet": True, "skip_download": True, "noplaylist": True}
    with yt_dlp.YoutubeDL(opcoes) as y:
        info = y.extract_info(url, download=False)
    if "entries" in info:
        info = info["entries"][0]
    return info["url"], info.get("title") or "video"


@app.get("/")
def inicio():
    return send_from_directory(".", "index.html")


@app.post("/api/info")
def info():
    url = (request.get_json(silent=True) or {}).get("url", "").strip()
    if not LINK.match(url):
        return jsonify(erro="Link inválido. Cole o link de um post ou reel público."), 400
    try:
        _, titulo = extrair(url)
    except Exception:
        return jsonify(erro="Não consegui acessar o vídeo. Ele pode ser privado ou ter sido removido."), 422
    return jsonify(titulo=titulo)


@app.get("/api/baixar")
def baixar():
    url = request.args.get("url", "").strip()
    if not LINK.match(url):
        return "Link inválido", 400
    try:
        direto, _ = extrair(url)
        r = requests.get(direto, stream=True, timeout=20)
        r.raise_for_status()
    except Exception:
        return "Falha ao baixar", 422
    return Response(
        r.iter_content(65536),
        content_type="video/mp4",
        headers={"Content-Disposition": 'attachment; filename="video.mp4"'},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)