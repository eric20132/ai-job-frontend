import streamlit as st
import requests
import uuid
import time # 🌟 引入時間套件來做輪詢等待

BACKEND_BASE_URL = "https://ai-job-search-agent-24hrs.onrender.com"

st.set_page_config(page_title="專屬求職 Agent", page_icon="🤖")
st.title("🤖 專屬求職 Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_task_id" not in st.session_state:
    st.session_state.current_task_id = None

# 渲染過去的對話歷史
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

st.divider()

# 🌟 1. 利用 Columns 實現左右排版 (左邊 4 份寬，右邊 1 份寬)
col_input, col_cancel = st.columns([4, 1])

# 左側：輸入框與送出按鈕
with col_input:
    with st.form(key="chat_form", clear_on_submit=True):
        prompt = st.text_area("你想找什麼樣的工作？", height=100)
        # 如果有任務在跑，就把送出按鈕鎖死 (disabled=True)
        submit_button = st.form_submit_button(
            "送出任務 🚀", 
            disabled=st.session_state.current_task_id is not None
        )

# 右側：取消按鈕放在這裡！
with col_cancel:
    # 加上一點空白讓按鈕對齊文字框的底部
    st.write("") 
    st.write("")
    if st.session_state.current_task_id:
        if st.button("🛑 取消任務", type="primary", use_container_width=True):
            task_id = st.session_state.current_task_id
            try:
                requests.post(f"{BACKEND_BASE_URL}/api/v1/cancel-job/{task_id}")
                st.session_state.messages.append({"role": "assistant", "content": "⚠️ 任務已被手動取消。"})
            except:
                pass
            st.session_state.current_task_id = None
            st.rerun()
    else:
        # 平常沒任務時，顯示灰色的不可點擊按鈕，保持版面整齊
        st.button("🛑 取消任務", disabled=True, use_container_width=True)

# 🌟 2. 處理新任務送出
if submit_button and prompt.strip():
    new_task_id = str(uuid.uuid4())
    st.session_state.current_task_id = new_task_id
    
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        payload = {"query": prompt, "task_id": new_task_id}
        requests.post(f"{BACKEND_BASE_URL}/api/v1/search-jobs", json=payload, timeout=30)
    except Exception as e:
        st.error(f"連線失敗：{str(e)}")
        st.session_state.current_task_id = None
    
    st.rerun()

# 🌟 3. 核心魔法：輪詢機制 (如果現在有任務，就一直檢查)
if st.session_state.current_task_id:
    task_id = st.session_state.current_task_id
    st.info("🔄 Agent 正在背景檢索並推播至 Slack，請稍候...")
    
    try:
        # 去問後端目前的狀態
        status_res = requests.get(f"{BACKEND_BASE_URL}/api/v1/task-status/{task_id}")
        if status_res.status_code == 200:
            status = status_res.json().get("status")
            
            if status == "completed":
                # 任務完成！顯示訊息並清空狀態
                final_msg = "✅ 任務完成！專屬職缺分析已經寄送到您的 Slack 頻道中囉！"
                st.session_state.messages.append({"role": "assistant", "content": final_msg})
                st.session_state.current_task_id = None
                time.sleep(1) # 暫停 1 秒讓使用者看清楚 UI 變化
                st.rerun()
                
            elif status == "failed":
                st.session_state.messages.append({"role": "assistant", "content": "❌ 任務執行過程中發生錯誤，請稍後再試。"})
                st.session_state.current_task_id = None
                st.rerun()
                
            elif status == "running":
                # 如果還在跑，就原地睡 3 秒，然後強制刷新網頁再檢查一次
                time.sleep(3)
                st.rerun()
                
    except Exception:
        # 如果網路不穩查不到，睡 3 秒再試一次
        time.sleep(3)
        st.rerun()