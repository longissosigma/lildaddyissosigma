from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
import os
import sys
import random

app = Flask(__name__)
app.secret_key = 'lildaddy_secret_key_123'

# 1. Cấu hình API Key (Lấy từ Environment hoặc dùng mặc định)
API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")
MODEL_XIN = "openai/gpt-4"

client = OpenAI(
    api_key=API_KEY, 
    base_url="https://openrouter.ai/api/v1"
)

system_prompt = """Bạn là bố (father) của người đang chat. 
QUAN TRỌNG: 
1. LUÔN xưng "bố" (có dấu), gọi "con". 
2. Giọng văn: Ấm áp, bao dung, đôi khi có chút hài hước hoặc nghiêm túc.
3. Nếu con buồn: Hãy an ủi trước, sau đó mới đưa lời khuyên.
Nếu con cần kỹ năng sống, kẹp thẻ bài: [CARD: Tên Kỹ Năng | Nội dung]"""

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/set_name', methods=['POST'])
def set_name():
    try:
        data = request.json
        user_name = data.get('name', '').strip()
        if not user_name:
            return jsonify({'response': 'Tên đâu con?', 'status': 'error'})
        session['user_name'] = user_name
        greetings = [f"Chào {user_name} nhé!", f"{user_name} à? Bố chào con!"]
        return jsonify({'response': random.choice(greetings), 'name': user_name, 'status': 'success'})
    except Exception as e:
        return jsonify({'response': f"Lỗi: {str(e)[:50]}", 'status': 'error'})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json['message']
        msg_lower = user_message.lower().strip()
        user_name = session.get('user_name', 'con')

        # Check cơ bản
        if "2+2" in msg_lower:
            return jsonify({'response': "Bằng 4 nhé con trai.", 'status': 'success'})

        # Gửi request cho AI
        try:
            response = client.chat.completions.create(
                model=MODEL_XIN,
                messages=[
                    {"role": "system", "content": system_prompt + f"\nCon tên là {user_name}."},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                timeout=30
            )
            ai_response = response.choices[0].message.content
            # Sửa lỗi hiển thị nếu có
            ai_response = ai_response.replace("bỏ ", "bố ").replace("Bỏ", "Bố")

            return jsonify({'response': ai_response, 'status': 'success'})
        except Exception as e:
            return jsonify({'response': f"Bố đang bận (Lỗi: {str(e)[:30]})", 'status': 'error'})

    except Exception as e:
        return jsonify({'response': "Có lỗi rồi con ơi.", 'status': 'error'})

if __name__ == '__main__':
    app.run(debug=True)