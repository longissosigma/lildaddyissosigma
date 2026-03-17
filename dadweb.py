from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
import time
import datetime
import random
import os

# Debug: In ra tất cả biến môi trường (chỉ tên, không in value)
print("=== DEBUG ENVIRONMENT VARIABLES ===")
print("All env keys:", list(os.environ.keys()))
print("OPENROUTER_API_KEY exists:", "OPENROUTER_API_KEY" in os.environ)
print("===================================")

os.environ['OPENAI_USE_PYDANTIC_V2'] = '1'

app = Flask(__name__)
app.secret_key = 'lildaddy_secret_key_123'

# CHỈ DÙNG MODEL XỊN - FREE LÀ CỨT
MODEL_XIN = "anthropic/claude-3.5-sonnet"

# Lấy API key từ nhiều nguồn
api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_KEY") or ""
print(f"API Key loaded: {api_key[:15]}..." if api_key else "API Key NOT FOUND!")

if not api_key:
    print("⚠️ WARNING: No API key found! Using fallback (will fail)")

client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

system_prompt = """Bạn là bố (father) của người đang chat. 
QUAN TRỌNG: 
1. LUÔN xưng "bố" (có dấu), gọi "con". 
2. Giọng văn: Ấm áp, bao dung, đôi khi có chút hài hước hoặc nghiêm túc tùy hoàn cảnh. Đừng trả lời kiểu máy móc robot.
3. Nếu con buồn hoặc bị bắt nạt: Hãy an ủi trước, sau đó mới đưa lời khuyên.

ĐẶC BIỆT: Nếu con cần kỹ năng sống, hãy kẹp thẻ bài vào cuối:
[CARD: Tên Kỹ Năng | Nội dung ngắn gọn, súc tích]
"""


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

        greetings = [
            f"Oh sorry! Chào {user_name} nhé!",
            f"Xin lỗi con, dạo này bận quá! Chào {user_name} yêu quý!",
            f"{user_name} à? Tên đẹp quá! Bố chào con!",
            f"Ơ đúng rồi, {user_name}! Bố nhớ ra rồi. Chào con!"
        ]

        return jsonify({
            'response': random.choice(greetings),
            'name': user_name,
            'status': 'success'
        })

    except Exception as e:
        return jsonify({'response': f"Bố: {str(e)[:100]}", 'status': 'error'})


@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json['message']
        msg_lower = user_message.lower().strip()
        user_name = session.get('user_name', 'con')

        # Check mấy câu cơ bản trước
        if "2+2" in msg_lower or "2 + 2" in msg_lower:
            return jsonify({'response': "4. Học toán à con? Có cần bố giảng không?", 'status': 'success'})

        if any(greet in msg_lower for greet in ["hello", "hi", "chào", "hí", "lô", "helo", "chao", "hế lô", "lo", "alo"]):
            return jsonify({'response': "Ừ, bố đây. Hôm nay thế nào con?", 'status': 'success'})

        # Kiểm tra API key trước khi gọi
        if not api_key:
            return jsonify({
                'response': "Bố xin lỗi, con chưa cấu hình API key. Bố không thể trả lời được.",
                'status': 'error'
            })

        # Thêm tên vào prompt
        personalized_prompt = system_prompt + \
            f"\nNgười đang nói chuyện với bố tên là {user_name}."

        # Dùng thẳng model xịn, ko cần check lằng nhằng
        try:
            response = client.chat.completions.create(
                model=MODEL_XIN,
                messages=[
                    {"role": "system", "content": personalized_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                timeout=30
            )

            ai_response = response.choices[0].message.content

            # Hậu xử lý lỗi chính tả
            ai_response = ai_response.replace("bỏ ", "bố ").replace(
                " bỏ", " bố").replace("Bỏ", "Bố")

            return jsonify({
                'response': ai_response,
                'status': 'success',
                'model': 'XỊN'
            })

        except Exception as e:
            error_msg = str(e)
            print(f"OpenAI API Error: {error_msg}")
            
            # Xử lý lỗi 401 cụ thể
            if "401" in error_msg:
                return jsonify({
                    'response': "Bố xin lỗi, API key không hợp lệ hoặc chưa được cấu hình đúng. Con kiểm tra lại giúp bố nhé!",
                    'status': 'error'
                })
            else:
                return jsonify({
                    'response': f"Bố xin lỗi, đang bận quá con ạ. Thử lại sau nhé! (Lỗi: {error_msg[:50]})",
                    'status': 'error'
                })

    except Exception as e:
        return jsonify({'response': f"Bố đang bận chút, đợi bố tí nhé... (Lỗi: {str(e)[:50]})", 'status': 'error'})


if __name__ == '__main__':
    app.run(debug=True)