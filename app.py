import streamlit as st
import requests
import uuid # 引入 UUID 套件

# 替換成你 Render 實際的網址 (注意結尾不要有斜線)
BACKEND_BASE_URL = "https://ai-job-search-agent-24hrs.onrender.com"

st.set_page_config(page_title="專屬求職 Agent", page_icon="🤖")
st.title("🤖 專屬求職 Agent")

# 初始化對話紀錄與當前任務 ID
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_task_id" not in st.session_state:
    st.session_state.current_task_id = None

# 🌟 實作取消按鈕區塊
if st.session_state.current_task_id:
    st.warning("🔄 Agent 正在背景賣力為您搜尋中...")
    if st.button("🛑 發現打錯了！立即取消搜尋任務", type="primary"):
        task_id = st.session_state.current_task_id
        try:
            cancel_res = requests.post(f"{BACKEND_BASE_URL}/api/v1/cancel-job/{task_id}")
            if cancel_res.status_code == 200:
                st.success("✅ 已成功攔截任務！後端運算已停止。")
                st.session_state.messages.append({"role": "assistant", "content": "⚠️ 任務已被使用者手動取消。"})
            else:
                st.error("無法取消，任務可能已經執行完畢。")
        except Exception as e:
            st.error(f"取消請求失敗：{e}")
        
        # 清空當前任務狀態並重新整理
        st.session_state.current_task_id = None
        st.rerun()

st.divider()

# 渲染過去的對話歷史
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 接收使用者輸入
with st.form(key="chat_form", clear_on_submit=True):
    prompt = st.text_area(
        "你想找什麼樣的工作？", 
        placeholder="例如：幫我在 Seattle 尋找適合的 AI Engineer 職缺...",
        height=100
    )
    submit_button = st.form_submit_button("送出任務 🚀")

if submit_button and prompt.strip():
    # 🌟 產生這次任務的專屬身分證
    new_task_id = str(uuid.uuid4())
    st.session_state.current_task_id = new_task_id
    
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner('連線至伺服器中...'):
        try:
            # 把 task_id 一起傳給後端
            payload = {"query": prompt, "task_id": new_task_id}
            response = requests.post(f"{BACKEND_BASE_URL}/api/v1/search-jobs", json=payload, timeout=30)
            
            if response.status_code == 200:
                ai_response = response.json().get("result", "任務已啟動！")
            else:
                ai_response = f"伺服器發生錯誤 (狀態碼: {response.status_code})"
                st.session_state.current_task_id = None # 發生錯誤就清空任務 ID
                
        except Exception as e:
            ai_response = f"連線失敗：{str(e)}"
            st.session_state.current_task_id = None

    st.chat_message("assistant").write(ai_response)
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    
    st.rerun()