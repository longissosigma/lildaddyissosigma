from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
import os
import random
import hashlib
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'lildaddy_secret_key_123'

# Lấy Key từ biến môi trường (Nhớ set trên Render nhé ông)
API_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL_XIN = "openai/gpt-4o"  # Hoặc model ông đang dùng

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

# Hàm xác định tier dựa trên nội dung thẻ (dùng hash để ổn định)
def determine_tier(title, content):
    hash_val = int(hashlib.md5((title + content).encode()).hexdigest(), 16)
    rand = hash_val % 100
    if rand < 60:
        return "common"
    elif rand < 90:
        return "epic"
    else:
        return "legendary"

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

# === DAILY ADVICE ROUTE ===
@app.route('/daily_advice', methods=['POST'])
def daily_advice():
    try:
        data = request.json
        emotion = data.get('emotion', '')
        user_name = session.get('user_name', 'con')
        
        if not emotion:
            return jsonify({'response': 'Bố cần biết cảm xúc của con mới khuyên được!', 'status': 'error'})
        
        # Prompt riêng cho Daily Advice dựa trên cảm xúc
        emotion_prompts = {
            "Buồn": f"Con đang buồn. Hãy an ủi con thật nhẹ nhàng, cho con biết rằng nỗi buồn là bình thường và rồi sẽ qua. Đưa ra lời khuyên giúp con vượt qua. Gọi con là {user_name}.",
            "Lo lắng": f"Con đang lo lắng. Hãy trấn an con, giúp con nhìn vấn đề rõ ràng hơn, đưa ra các bước cụ thể để con bớt lo. Gọi con là {user_name}.",
            "Bực bội": f"Con đang bực bội. Hãy giúp con bình tĩnh, không phán xét, đưa ra cách để con xả hơi an toàn và nhìn vấn đề tích cực hơn. Gọi con là {user_name}.",
            "Bất an": f"Con đang bất an. Hãy lắng nghe, trấn an con rằng con không cô đơn, gợi ý những điều nhỏ để con cảm thấy an toàn hơn. Gọi con là {user_name}.",
            "Mơ hồ": f"Con đang mơ hồ, không biết nên thế nào. Hãy giúp con nhìn nhận vấn đề đơn giản hơn, đưa ra hướng đi rõ ràng, có thể là những bước nhỏ. Gọi con là {user_name}.",
            "Muốn được động viên": f"Con đang cần động viên. Hãy dành cho con những lời khích lệ chân thành, nhấn mạnh giá trị của con và niềm tin bố dành cho con. Gọi con là {user_name}.",
            "Hôm nay ổn, chỉ muốn nhận thẻ bài": f"Con cảm thấy ổn và muốn nhận thẻ bài. Hãy chia sẻ một bài học sống ngắn gọn, ý nghĩa, và đóng gói nó thành thẻ bài [CARD: ...]. Đây là cơ hội để con học thêm điều mới. Gọi con là {user_name}."
        }
        
        # Lấy prompt theo cảm xúc, mặc định là động viên nếu không khớp
        advice_prompt = emotion_prompts.get(emotion, emotion_prompts["Muốn được động viên"])
        
        # Gọi AI để tạo lời khuyên
        response = client.chat.completions.create(
            model=MODEL_XIN,
            messages=[
                {"role": "system", "content": system_prompt + "\n\n" + advice_prompt},
                {"role": "user", "content": f"Con đang cảm thấy: {emotion}. Bố hãy cho con lời khuyên nhé."}
            ],
            temperature=0.7,
            timeout=30
        )
        
        ai_response = response.choices[0].message.content
        
        return jsonify({
            'response': ai_response,
            'status': 'success',
            'emotion': emotion
        })
        
    except Exception as e:
        print(f"Daily Advice Error: {e}")
        return jsonify({
            'response': "Bố đang bận, tí nữa con thử lại nhé!",
            'status': 'error'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)