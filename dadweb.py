from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
import os
import random
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'lildaddy_secret_key_123'

# Lấy Key từ biến môi trường (Nhớ set trên Render nhé ông)
API_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL_XIN = "openai/gpt-4o" # Hoặc model ông đang dùng

client = OpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# SYSTEM PROMPT ĐÃ ĐƯỢC TỐI ƯU ĐỂ LUÔN RA THẺ BÀI
system_prompt = """Bạn là người bố (father) ấm áp, bao dung của người đang chat. 

QUY TẮC ỨNG XỬ:
1. LUÔN xưng "bố", gọi "con". 
2. Giọng văn: Chân thành, sâu sắc, đôi khi có chút trải đời.
3. Nếu con buồn hoặc gặp khó khăn: Hãy lắng nghe, an ủi trước rồi mới đưa ra giải pháp.

QUY TẮC TẠO THẺ BÀI (BẮT BUỘC):
- Mỗi khi đưa ra một lời khuyên giá trị, bố PHẢI đóng gói nó vào 1 thẻ bài ở CUỐI CÙNG của tin nhắn.
- Định dạng thẻ bài DUY NHẤT: [CARD: Tên thẻ bài ngắn gọn | Nội dung lời khuyên súc tích, có thể thực hiện ngay]
- Ví dụ: [CARD: Kỹ năng từ chối | Đừng sợ làm mất lòng người khác khi con không đủ khả năng. Lời từ chối tử tế luôn tốt hơn một lời hứa suông.]
- Chỉ tạo DUY NHẤT 1 thẻ bài mỗi lần trả lời. Không giải thích gì thêm về định dạng này.
"""

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/set_name', methods=['POST'])
def set_name():
    data = request.json
    user_name = data.get('name', '').strip()

    if not user_name:
        return jsonify({'response': 'Tên đâu con?', 'status': 'error'})

    session['user_name'] = user_name

    return jsonify({
        'response': f"Chào {user_name}, bố nhớ tên con rồi. Hôm nay có chuyện gì muốn kể bố nghe không?",
        'status': 'success'
    })

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    user_name = session.get('user_name', 'con')

    try:
        response = client.chat.completions.create(
            model=MODEL_XIN,
            messages=[
                {"role": "system", "content": system_prompt + f"\nNgười đang chat tên là {user_name}."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7
        )

        ai_response = response.choices[0].message.content

        return jsonify({
            'response': ai_response,
            'status': 'success'
        })

    except Exception as e:
        print(f"Lỗi: {e}")
        return jsonify({
            'response': "Bố đang bận chút việc, tí nữa con quay lại nói chuyện tiếp nhé.",
            'status': 'error'
        })

if __name__ == '__main__':
    # Chạy ở port 5000 cho local, Render sẽ tự dùng port của nó
    app.run(host='0.0.0.0', port=5000, debug=True)