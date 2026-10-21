"""
OCS 本地 AI 答题服务
====================
接收 OCS 题库请求，调用大模型 API 返回答案。
OCS 配置中 url 指向此服务的 /api/answer 端点。

运行: python server.py
"""

import json
import time
import traceback
from http.client import HTTPException

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

# ---------- 配置 ----------
CONFIG_PATH = "config.json"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

PORT = CONFIG.get("port", 7077)
HOST = CONFIG.get("host", "127.0.0.1")
API_KEY = CONFIG.get("apiKey", "sk-your-api-key-here")
API_BASE = CONFIG.get("apiBase", "https://api.longcat.chat/openai/v1").rstrip("/")
MODEL = CONFIG.get("model", "LongCat-2.0")
SYSTEM_PROMPT = CONFIG.get("systemPrompt", "你是一个答题助手。请只给出答案，不要解释。")
TEMPERATURE = CONFIG.get("temperature", 0.1)
TIMEOUT = CONFIG.get("timeout", 30)

# ---------- Flask ----------
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


def call_llm(question: str, options: str, qtype: str) -> str:
    """调用大模型获取答案，纯文本返回。"""
    if not API_KEY or API_KEY == "sk-your-api-key-here":
        return "【错误】尚未配置 API Key，请修改 config.json 中的 apiKey 字段"

    # 拼 prompt
    type_hint = f"题目类型：{qtype}\n" if qtype else ""
    options_hint = f"选项：\n{options}\n" if options else ""
    user_msg = f"{type_hint}题目：{question}\n{options_hint}请直接给出答案。"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "temperature": TEMPERATURE,
        "stream": False,
    }

    url = f"{API_BASE}/chat/completions"
    resp = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    try:
        answer = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as e:
        answer = f"【解析错误】API 返回格式异常: {data}"

    return answer


@app.route("/api/answer", methods=["GET", "POST"])
def api_answer():
    """
    OCS 请求入口。
    OCS 会以 GET 或 POST 发送 type/question/options/key。
    返回 OCS 能识别的 handler 格式: { code: 1, question, answer }
    """
    # 兼容 GET 查询参数 和 POST form/JSON
    if request.method == "GET":
        data = request.args.to_dict()
    elif request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        raw = request.get_data(as_text=True)
        data = {}
        if raw:
            try:
                data = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                data = request.form.to_dict() or {}

    qtype = (data.get("type") or "").strip()
    question = (data.get("question") or data.get("title") or "").strip()
    options = (data.get("options") or "").strip()

    if not question:
        return jsonify({"code": 0, "message": "题目为空"})

    t0 = time.time()
    answer = call_llm(question, options, qtype)
    elapsed = round(time.time() - t0, 2)

    # 与 OCS handler 约定一致
    return jsonify({
        "code": 1,
        "question": question,
        "answer": answer,
        "time": elapsed,
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": MODEL})


@app.route("/", methods=["GET", "POST"])
def root():
    if request.method == "GET":
        return jsonify({"hint": "POST to /api/answer instead"})
    # POST 到根路径时当答题处理
    return api_answer()


@app.before_request
def log_request():
    # 打印每个请求的路径和方法，方便排查
    if request.path not in ("/health",):
        print(f'[REQ] {request.method} {request.path}  args={dict(request.args)}')


@app.route("/favicon.ico")
def favicon():
    return "", 204
@app.errorhandler(Exception)
def on_error(e):
    traceback.print_exc()
    return jsonify({"code": -1, "message": str(e)}), 500


if __name__ == "__main__":
    print(f"=== OCS AI 答题服务 ===")
    print(f"监听地址: http://{HOST}:{PORT}")
    print(f"答题端点: http://{HOST}:{PORT}/api/answer")
    print(f"模型: {MODEL}")
    print(f"API Base: {API_BASE}")
    print(f"========================")
    app.run(host=HOST, port=PORT, debug=False)
