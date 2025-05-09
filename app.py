from flask import Flask, request, jsonify, send_from_directory
import requests
import time

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/test', methods=['POST'])
def test_proxy():
    data = request.json
    target_url = data.get('targetUrl')
    proxy_url = data.get('proxyUrl')
    request_id = data.get('requestId')
    
    try:
        proxy = {
            'http': proxy_url,
            'https': proxy_url
        } if proxy_url else None
        
        start_time = time.time()
        response = requests.get(target_url, proxies=proxy, timeout=10)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                details = f"请求ID: {request_id}\n响应时间: {elapsed_time:.2f}秒\n状态码: {response.status_code}\n\n响应数据:\n{response_data}"
            except:
                details = f"请求ID: {request_id}\n响应时间: {elapsed_time:.2f}秒\n状态码: {response.status_code}\n\n响应数据:\n{response.text}"
            
            return jsonify({
                'success': True,
                'statusCode': response.status_code,
                'responseTime': elapsed_time,
                'details': details
            })
        else:
            return jsonify({
                'success': False,
                'error': str(response.status_code),
                'details': f"HTTP错误: {response.status_code}\n响应内容:\n{response.text}"
            })
            
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'timeout',
            'details': "连接超时"
        })
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': 'CONNECTION_ERROR',
            'details': f"连接错误: {str(e)}"
        })

if __name__ == '__main__':
    app.run(debug=True, port=5000)