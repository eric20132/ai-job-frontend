import streamlit as st
import requests
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo # 🌟 引入內建的時區套件
import time

# 設定目標時區 (會自動處理 PDT/PST)
PACIFIC_TZ = ZoneInfo("America/Los_Angeles")

# 替換成你 Render 實際的網址 (注意結尾不要有斜線)
BACKEND_BASE_URL = "https://ai-job-search-agent-24hrs.onrender.com"

st.set_page_config(page_title="專屬求職 Agent", page_icon="🤖")
st.title("🤖 專屬求職 Agent")

# 初始化記憶體
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_task_id" not in st.session_state:
    st.session_state.current_task_id = None

# 渲染對話歷史，並在對話上方加上時間戳記
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "timestamp" in msg:
            st.caption(f"🕒 {msg['timestamp']}")
        st.write(msg["content"])

st.divider()

# ==========================================
# 狀態 1：系統閒置中 (只顯示輸入框)
# ==========================================
if st.session_state.current_task_id is None:
    with st.form(key="chat_form", clear_on_submit=True):
        prompt = st.text_area(
            "你想找什麼樣的工作？", 
            placeholder="例如：幫我在 Seattle 尋找適合的 AI Engineer 職缺...",
            height=100
        )
        submit_button = st.form_submit_button("送出任務 🚀")

    if submit_button and prompt.strip():
        new_task_id = str(uuid.uuid4())
        
        # 🌟 取得當下太平洋時間 (並加上 %Z 自動顯示 PDT 或 PST)
        current_time = datetime.now(PACIFIC_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")
        st.session_state.messages.append({
            "role": "user", 
            "content": prompt,
            "timestamp": current_time
        })

        with st.spinner('連線至伺服器中...'):
            try:
                payload = {"query": prompt, "task_id": new_task_id}
                response = requests.post(f"{BACKEND_BASE_URL}/api/v1/search-jobs", json=payload, timeout=30)
                
                if response.status_code == 200:
                    st.session_state.current_task_id = new_task_id
                    st.rerun()
                else:
                    st.error(f"伺服器發生錯誤 (狀態碼: {response.status_code})")
            except Exception as e:
                st.error(f"連線失敗：{str(e)}")

# ==========================================
# 狀態 2：任務執行中 (隱藏輸入框，只顯示操作按鈕)
# ==========================================
else:
    
    task_id = st.session_state.current_task_id
    st.info("🔄 Agent 正在跨網搜尋與分析，請耐心等候幾分鐘... (同時將同步發送至 Slack)")
    
    # 🌟 1. 現在只需要一個大大的取消按鈕
    if st.button("🛑 發現打錯了！立即取消任務", type="primary", use_container_width=True):
        try:
            cancel_res = requests.post(f"{BACKEND_BASE_URL}/api/v1/cancel-job/{task_id}")
            cancel_time = datetime.now(PACIFIC_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")
            if cancel_res.status_code == 200:
                st.success("✅ 已成功攔截任務！後端運算已停止。")
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": "⚠️ 任務已被手動取消。",
                    "timestamp": cancel_time
                })
        except Exception as e:
            st.error(f"取消請求失敗：{e}")
        
        st.session_state.current_task_id = None
        st.rerun()
            
    # 🌟 2. 核心魔法：自動背景輪詢 (Auto-polling)
    try:
        status_res = requests.get(f"{BACKEND_BASE_URL}/api/v1/task-status/{task_id}")
        
        if status_res.status_code == 200:
            data = status_res.json()
            status = data.get("status")
            
            if status == "completed":
                check_time = datetime.now(PACIFIC_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")
                # 🌟 拿到後端傳來的完整 Markdown 報告！
                final_result = data.get("result", "✅ 任務完成！") 
                
                # 將這份精美的報告加入對話紀錄中
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": final_result,
                    "timestamp": check_time
                })
                # 清除任務狀態，讓畫面變回輸入框
                st.session_state.current_task_id = None
                st.rerun()
                
            elif status == "failed":
                check_time = datetime.now(PACIFIC_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": "❌ 任務執行過程中發生錯誤或被 Critic 退件達上限，請稍後再試。",
                    "timestamp": check_time
                })
                st.session_state.current_task_id = None
                st.rerun()
                
            elif status == "running":
                # 🌟 如果還在跑，暫停 2.5 秒後自動刷新網頁，再次進來查進度
                time.sleep(2.5)
                st.rerun()
                
        else:
            st.warning("⚠️ 無法取得狀態，可能是任務已結束，或是後端尚未更新。")
            st.session_state.current_task_id = None
            st.rerun()
            
    except Exception as e:
        # 如果網路瞬斷，就等 3 秒再試一次，不要崩潰
        time.sleep(3)
        st.rerun()