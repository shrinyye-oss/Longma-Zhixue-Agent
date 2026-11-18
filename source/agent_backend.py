"""Optional local, server-side tool-calling Agent for Longma Study.

No third-party packages are required. Defaults to 127.0.0.1 and refuses to
expose the API key to the browser. Supports OpenAI-compatible /chat/completions.
"""
import json
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
DB = json.loads((ROOT / 'data' / 'knowledge.json').read_text(encoding='utf-8'))
TOPICS = {t['id']: t for t in DB['topics']}
KEY = os.getenv('LLM_API_KEY', '').strip()
BASE_URL = os.getenv('LLM_BASE_URL', 'https://api.openai.com/v1').rstrip('/')
MODEL = os.getenv('LLM_MODEL', '').strip()
HOST = '127.0.0.1'
PORT = int(os.getenv('LONGMA_PORT', '8765'))

TOOLS = [
    {"type": "function", "function": {"name": "search_notes", "description": "Search local DEMO study cards. Sources are original demo cards, NOT the study platform's teaching materials.", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Concise concept to retrieve"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "get_progress", "description": "Read current chapter attempt count and accuracy from local user-submitted record.", "parameters": {"type": "object", "properties": {"topic_id": {"type": "string", "description": "One of 1.1, 1.2, ..., 2.6"}}, "required": ["topic_id"]}}},
    {"type": "function", "function": {"name": "select_practice", "description": "Select one existing demonstrative practice question for a topic. Questions are not official course questions.", "parameters": {"type": "object", "properties": {"topic_id": {"type": "string"}}, "required": ["topic_id"]}}},
]


def search_notes(query):
    query = str(query).strip().lower()[:180]
    items = []
    for t in DB['topics']:
        score = 0
        for term in [t['id'], *t['tags']]:
            if term.lower() in query:
                score += 4 + min(len(term), 10)
        if t['title'].lower() in query:
            score += 10
        if score:
            items.append((score, t))
    items.sort(key=lambda x: -x[0])
    if not items:
        items = [(0, TOPICS['1.3'])]
    return [{"topic_id": t['id'], "title": t['title'], "summary": t['summary'], "points": t['points'], "source": "original_demo_card_not_course_original"} for _, t in items[:3]]


def safe_progress(progress, topic_id):
    p = progress.get(topic_id, {})
    if not isinstance(p, dict):
        p = {}
    attempts = max(0, min(10000, int(p.get('attempts') or 0)))
    correct = max(0, min(attempts, int(p.get('correct') or 0)))
    return {"topic_id": topic_id, "attempts": attempts, "correct": correct, "accuracy": round(correct / attempts * 100) if attempts else None}


def tool_run(name, arguments, progress):
    if name == 'search_notes':
        return search_notes(arguments.get('query', ''))
    tid = str(arguments.get('topic_id', '1.3'))
    if tid not in TOPICS:
        return {"error": "invalid topic_id", "allowed": list(TOPICS)}
    if name == 'get_progress':
        return safe_progress(progress, tid)
    if name == 'select_practice':
        questions = TOPICS[tid]['questions']
        p = progress.get(tid, {})
        last = p.get('questions') if isinstance(p, dict) else {}
        if not isinstance(last, dict):
            last = {}
        question = min(questions, key=lambda q: ((last.get(q['id']) or {}).get('attempts', 0), q['id']))
        return {"topic_id": tid, "question_id": question['id'], "question": question['prompt'], "choices": question['options'], "note": "demonstration_question"}
    return {"error": "tool not permitted"}


def chat_completion(messages):
    if not KEY or not MODEL:
        raise ValueError('模型未配置：需要 LLM_API_KEY 和 LLM_MODEL')
    # The base URL is chosen and supplied by the local operator, not by the browser.
    if not BASE_URL.startswith(('https://', 'http://127.0.0.1:', 'http://localhost:')):
        raise ValueError('LLM_BASE_URL 必须使用 HTTPS 或本机 HTTP')
    payload = json.dumps({"model": MODEL, "messages": messages, "tools": TOOLS, "tool_choice": "auto", "temperature": 0.3}, ensure_ascii=False).encode('utf-8')
    request = Request(BASE_URL + '/chat/completions', payload, headers={"Content-Type": "application/json", "Authorization": 'Bearer '+KEY}, method='POST')
    try:
        with urlopen(request, timeout=35) as response:
            data = json.loads(response.read(1024 * 1024).decode('utf-8'))
            return data['choices'][0]['message']
    except HTTPError as e:
        raise RuntimeError('模型服务返回 HTTP '+str(e.code)+'；请检查模型配置与额度。') from e
    except (URLError, KeyError, ValueError, TimeoutError) as e:
        raise RuntimeError('模型服务调用失败或不支持工具调用：'+str(e)[:130]) from e


def run_agent(goal, progress, topic_id, completion=chat_completion):
    goal = str(goal).strip()[:500]
    if not goal:
        raise ValueError('学习目标不能为空')
    if not isinstance(progress, dict):
        progress = {}
    system = ("你是‘龙马智学’学习助手。背景为高校 AI 入门课程复习。"
              "特别声明：章节标题来自用户的学习通截图；所有知识卡与练习题是项目原创演示材料，"
              "不是学习通原文，也不是教师标准答案。绝不可伪称官方课程资料。"
              "回答前必须至少调用一次可用工具进行资料检索或学习状态读取。"
              "你可以根据目标调用 search_notes/get_progress/select_practice。"
              "对未检索到的知识保守表述，并明确说明来源。中文回答，180字以内，给出下一步学习行动。"
              "不可要求提供密钥、密码或其他个人隐私。")
    messages = [{"role": "system", "content": system}, {"role": "user", "content": f"学习目标：{goal}\n当前章节：{topic_id}"}]
    trace = []
    for _ in range(4):
        message = completion(messages)
        call_list = message.get('tool_calls') or []
        if not call_list:
            answer = message.get('content') or ''
            return {"answer": str(answer)[:2500], "tool_calls": trace, "model_used": bool(trace)}
        messages.append({"role":"assistant", "content": message.get('content') or '', "tool_calls": call_list})
        for call in call_list[:4]:
            fn = call.get('function') or {}
            name = str(fn.get('name', ''))
            try:
                arguments = json.loads(fn.get('arguments') or '{}')
                if not isinstance(arguments, dict):
                    raise ValueError('arguments must be object')
            except (ValueError, TypeError):
                arguments = {}
            if name not in ('search_notes','get_progress','select_practice'):
                result = {"error": "tool not permitted"}
            else:
                result = tool_run(name, arguments, progress)
                trace.append({"name": name, "argument_preview": str(arguments)[:150]})
            messages.append({"role": "tool", "tool_call_id": call.get('id', 'unknown'), "content": json.dumps(result, ensure_ascii=False)})
    messages.append({"role": "system", "content":"现在直接总结，禁止进一步调用工具。"})
    # If the model insists on more tool calls, do not pretend they were executed.
    return {"answer":"已达到工具调用轮次上限。请缩小问题范围后重试。", "tool_calls":trace, "model_used":bool(trace)}


class AppHandler(BaseHTTPRequestHandler):
    def reply_json(self, status, obj):
        body=json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path=urlsplit(self.path).path
        if path == '/api/status':
            return self.reply_json(200,{"agent_enabled":bool(KEY and MODEL),"model":MODEL if KEY and MODEL else None})
        if path not in ('/','/index.html','/longma.html'):
            return self.reply_json(404,{"error":"not found"})
        body=(ROOT/'dist'/'龙马智学-离线可运行.html').read_bytes()
        self.send_response(200)
        self.send_header('Content-Type','text/html; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if urlsplit(self.path).path != '/api/agent':
            return self.reply_json(404,{"error":"not found"})
        if not KEY or not MODEL:
            return self.reply_json(503,{"error":"未配置模型；请使用离线规则模式，或配置服务端环境变量。"})
        try:
            length=int(self.headers.get('Content-Length') or '0')
            if length <= 0 or length > 40000:
                return self.reply_json(413,{"error":"请求体无效或过大"})
            body=json.loads(self.rfile.read(length))
            answer=run_agent(body.get('goal',''),body.get('progress',{}),body.get('topic_id','1.3'))
            return self.reply_json(200,answer)
        except Exception as exc:
            return self.reply_json(422,{"error":str(exc)[:250]})


if __name__ == '__main__':
    print(f'龙马智学本地服务: http://{HOST}:{PORT}')
    print('模式：' + (f'真实模型工具调用（{MODEL}）' if KEY and MODEL else '离线规则演示（未配置模型）'))
    print('提醒：不要公开分享真实 API Key、配置文件或使用记录。')
    ThreadingHTTPServer((HOST,PORT),AppHandler).serve_forever()
