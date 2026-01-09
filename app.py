from flask import Flask, render_template, request, jsonify, Response
import requests
import os
import json
from typing import Generator

app = Flask(__name__)

# 定义不同模型的API配置
MODEL_CONFIGS = {
    "iquestcoder-instruct": {
        "base_url": "",
        "headers": {
            "Authorization": "Bearer EMPTY",
            "Content-Type": "application/json"
        },
        "model_id": "iquestcoder-instruct"
    },
    "iquestloopcoder-instruct": {
        "base_url": "",
        "headers": {
            "Authorization": "Bearer EMPTY",
            "Content-Type": "application/json"
        },
        "model_id": "iquestloopcoder-instruct"
    },
    "iquestcoder-stage1-int4": {
        "base_url": "",
        "headers": {
            "Authorization": "Bearer EMPTY",
            "Content-Type": "application/json"
        },
        "model_id": "iquestcoder-stage1-int4"
    }
}

# 预定义的模型列表 - 使用实际的模型ID
MODELS = [
    "iquestcoder-instruct",
    "iquestloopcoder-instruct", 
    "iquestcoder-stage1-int4"
]

@app.route('/')
def index():
    return render_template('index.html', models=MODELS)

@app.route('/api/models', methods=['GET'])
def get_models():
    try:
        # 尝试从每个模型服务获取模型信息
        available_models = []
        for model_name, config in MODEL_CONFIGS.items():
            try:
                response = requests.get(f"{config['base_url']}/models", headers=config['headers'], timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    model_ids = [model['id'] for model in data.get('data', [])]
                    available_models.extend(model_ids)
            except:
                # 如果某个服务不可用，跳过它
                continue
        
        # 如果从API获取失败，返回预定义列表
        if not available_models:
            available_models = MODELS
            
        return jsonify({"models": available_models})
    except Exception as e:
        # 如果请求失败，返回预定义列表
        return jsonify({"models": MODELS})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    messages = data.get('messages', [])
    model = data.get('model', MODELS[0])
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens', 1024)
    stream = data.get('stream', False)
    
    # 根据模型名称选择对应的API配置
    selected_config = None
    for config_model_name, config in MODEL_CONFIGS.items():
        if model == config_model_name or model == config['model_id']:  # 精确匹配模型
            selected_config = config
            model = config['model_id']  # 使用实际的模型ID
            break
    
    # 如果没有找到对应的配置，使用默认配置
    if selected_config is None:
        selected_config = MODEL_CONFIGS.get("iquestcoder-stage1-int4", {
            "base_url": "",
            "headers": {
                "Authorization": "Bearer EMPTY",
                "Content-Type": "application/json"
            },
            "model_id": "iquestcoder-stage1-int4"
        })
        model = selected_config['model_id']
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream
    }
    
    try:
        if stream:
            return Response(
                stream_response(payload, selected_config),
                mimetype='text/plain'
            )
        else:
            response = requests.post(
                f"{selected_config['base_url']}/chat/completions",
                headers=selected_config['headers'],
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return jsonify({
                    "content": result["choices"][0]["message"]["content"],
                    "model": result.get("model", model)
                })
            else:
                return jsonify({"error": f"API request failed with status {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def stream_response(payload, config) -> Generator[str, None, None]:
    try:
        with requests.post(
            f"{config['base_url']}/chat/completions",
            headers=config['headers'],
            json=payload,
            stream=True
        ) as response:
            for chunk in response.iter_lines():
                if chunk:
                    decoded_chunk = chunk.decode('utf-8')
                    
                    if decoded_chunk.startswith('data: '):
                        data = decoded_chunk[6:]  # Remove 'data: ' prefix
                        
                        if data == '[DONE]':
                            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
                            break
                        
                        try:
                            parsed = json.loads(data)
                            if 'choices' in parsed and len(parsed['choices']) > 0:
                                delta = parsed['choices'][0].get('delta', {})
                                if 'content' in delta and delta['content']:
                                    yield f"data: {json.dumps({'content': delta['content']})}\n\n"
                        except json.JSONDecodeError:
                            continue
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)