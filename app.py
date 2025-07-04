# 匯入需要的工具
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from flask_sqlalchemy import SQLAlchemy # <--- 需要的 SQLAlchemy
import os                         # <--- 需要的 os 模組
import datetime                   # <--- 需要的 datetime 模組

# 設定基本的日誌，方便在終端機看訊息
logging.basicConfig(level=logging.INFO)

# 建立 Flask 應用程式
app = Flask(__name__)
# 啟用 CORS，允許來自前端的請求 (開發時用)
CORS(app)

# --- ↓↓↓ 資料庫設定 ↓↓↓ ---
# 從環境變數取得資料庫連線 URL
database_uri = os.environ.get('DATABASE_URL')
if database_uri and database_uri.startswith("postgres://"):
    database_uri = database_uri.replace("postgres://", "postgresql://", 1) # SQLAlchemy 需要 postgresql://

# 如果沒有環境變數 (例如在本機測試)，則使用本地端的 SQLite 作為備用
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri or 'sqlite:///local_messages.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # 關閉不需要的追蹤功能
db = SQLAlchemy(app) # 初始化 SQLAlchemy
# --- ↑↑↑ 資料庫設定結束 ↑↑↑ ---


# --- ↓↓↓ 定義資料庫模型 (Message 表格) ↓↓↓ ---
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True) # 自動增加的整數ID
    name = db.Column(db.String(100), nullable=False) # 姓名 (不允許空)
    email = db.Column(db.String(120), nullable=False) # Email (不允許空)
    subject = db.Column(db.String(200), nullable=True) # 主旨 (允許空)
    message = db.Column(db.Text, nullable=False) # 訊息內容 (不允許空)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow) # 提交時間 (自動填入 UTC 時間)

    def __repr__(self):
        return f'<Message ID: {self.id}, Name: {self.name}>'
# --- ↑↑↑ 定義資料庫模型結束 ↑↑↑ ---


# --- ↓↓↓ 修改處理表單的路由 ↓↓↓ ---
@app.route('/api/contact', methods=['POST'])
def handle_contact_form():
    """這個函數負責處理聯絡表單的提交，並存入資料庫"""
    logging.info("後端：收到來自 /api/contact 的 POST 請求")

    if not request.is_json:
        logging.warning("後端：收到的請求不是 JSON 格式")
        return jsonify({"status": "error", "message": "請求格式錯誤，後端需要 JSON"}), 400

    data = request.get_json()
    logging.info(f"後端：收到的資料內容: {data}")

    # --- 資料驗證 ---
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')
    subject = data.get('subject') # 主旨是選填

    if not name or not email or not message:
        logging.warning("後端：缺少必要欄位 (姓名、Email 或訊息)")
        return jsonify({"status": "error", "message": "請確認姓名、Email 和訊息都已填寫。"}), 400

    # --- 將資料存到資料庫 ---
    try:
        # 建立一個新的 Message 物件，對應資料庫的一筆紀錄
        new_message = Message(
            name=name,
            email=email,
            subject=subject, # 將 subject 也存入
            message=message
            # timestamp 欄位有 default 值，會自動產生
        )
        db.session.add(new_message) # 將新訊息物件加入資料庫 session (暫存區)
        db.session.commit() # 提交 session，將變更實際寫入資料庫
        logging.info("後端：訊息已成功儲存到資料庫")

        # 儲存成功後，回傳成功的 JSON 回應給前端
        return jsonify({"status": "success", "message": "後端：訊息已成功收到並儲存，我們會盡快回覆您！"})

    except Exception as e:
        db.session.rollback() # 如果儲存過程出錯，回復資料庫到之前的狀態
        logging.error(f"後端：儲存資料庫時發生錯誤: {e}")
        # 回傳資料庫錯誤訊息給前端
        return jsonify({"status": "error", "message": "後端資料庫儲存錯誤，請稍後再試。"}), 500
# --- ↑↑↑ 修改處理表單的路由結束 ↑↑↑ ---


# --- ↓↓↓ 加入建立表格的程式碼 ↓↓↓ ---
# 使用應用程式上下文來建立所有定義好的資料庫表格 (如果表格還不存在)
with app.app_context():
    db.create_all()
    print("資料庫表格檢查完畢 (若不存在則已建立)")
# --- ↑↑↑ 加入建立表格的程式碼結束 ↑↑↑ ---


# --- 這段是你原本就有的，用來啟動伺服器 ---
if __name__ == '__main__':
    # 啟動 Flask 開發伺服器
    app.run(host='0.0.0.0', port=5000, debug=True)