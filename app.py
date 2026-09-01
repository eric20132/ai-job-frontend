import streamlit as st
import requests
import uuid

# 替換成你 Render 實際的網址 (注意結尾不要有斜線)
BACKEND_BASE_URL = "https://ai-job-search-agent-24hrs.onrender.com"

st.set_page_config(page_title="專屬求職 Agent", page_icon="🤖")
st.title("🤖 專屬求職 Agent")

# 初始化記憶體
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_task_id" not in st.session_state:
    st.session_state.current_task_id = None

# 渲染對話歷史
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

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
        
        st.chat_message("user").write(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner('連線至伺服器中...'):
            try:
                payload = {"query": prompt, "task_id": new_task_id}
                response = requests.post(f"{BACKEND_BASE_URL}/api/v1/search-jobs", json=payload, timeout=30)
                
                if response.status_code == 200:
                    # 成功啟動後，才切換狀態並強制重新整理畫面
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
    st.info("🔄 Agent 正在背景賣力為您搜尋中... (請耐心等候幾分鐘)")
    
    col1, col2 = st.columns(2)
    
    # 左邊按鈕：取消任務
    with col1:
        if st.button("🛑 發現打錯了！立即取消任務", type="primary", use_container_width=True):
            try:
                cancel_res = requests.post(f"{BACKEND_BASE_URL}/api/v1/cancel-job/{task_id}")
                if cancel_res.status_code == 200:
                    st.success("✅ 已成功攔截任務！後端運算已停止。")
                    st.session_state.messages.append({"role": "assistant", "content": "⚠️ 任務已被使用者手動取消。"})
            except Exception as e:
                st.error(f"取消請求失敗：{e}")
            
            # 清空狀態，讓畫面變回輸入框
            st.session_state.current_task_id = None
            st.rerun()
            
    # 右邊按鈕：手動檢查進度 (取代原本會當機的自動輪詢)
    with col2:
        if st.button("🔄 檢查最新進度", use_container_width=True):
            try:
                status_res = requests.get(f"{BACKEND_BASE_URL}/api/v1/task-status/{task_id}")
                if status_res.status_code == 200:
                    status = status_res.json().get("status")
                    
                    if status == "completed":
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": "✅ 任務完成！專屬職缺分析已經寄送到您的 Slack 頻道中囉！"
                        })
                        st.session_state.current_task_id = None
                        st.rerun()
                    elif status == "failed":
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": "❌ 任務執行過程中發生錯誤，請稍後再試。"
                        })
                        st.session_state.current_task_id = None
                        st.rerun()
                    else:
                        # 用 Streamlit 右下角的 Toast 小氣泡提示，不干擾主畫面
                        st.toast("🏃 Agent 還在努力運算中，請再等一下喔！", icon="⏳")
                else:
                    st.warning("⚠️ 無法取得狀態，可能是任務已結束，或是你的後端 (api.py) 還沒更新唷！")
                    st.session_state.current_task_id = None
                    st.rerun()
            except Exception as e:
                st.error(f"查詢失敗：{str(e)}")