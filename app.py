import streamlit as st
import requests

# 替換成你 Render 實際的網址與端點
BACKEND_URL = "https://ai-job-search-agent-24hrs.onrender.com/api/chat"

st.set_page_config(page_title="專屬求職 Agent", page_icon="🤖")
st.title("🤖 專屬求職 Agent")

# 初始化對話紀錄
if "messages" not in st.session_state:
    st.session_state.messages = []

# 渲染過去的對話
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 接收使用者輸入 (預設帶入找尋西雅圖 AI 工程師的提示字作為範例)
default_prompt = "幫我在 Seattle 尋找適合的 AI Engineer 職缺..."
if prompt := st.chat_input(default_prompt):
    
    # 顯示並儲存使用者的訊息
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 呼叫 Render 後端 API
    with st.spinner('Agent 正在為您跨網搜尋與分析職缺中，這可能需要幾分鐘...'):
        try:
            response = requests.post(BACKEND_URL, json={"query": prompt}, timeout=300)
            
            if response.status_code == 200:
                ai_response = response.json().get("result", "任務已完成，請至 Slack 查看詳細報告！")
            else:
                ai_response = f"伺服器發生錯誤 (狀態碼: {response.status_code})"
                
        except requests.exceptions.Timeout:
            ai_response = "請求超時！Render 伺服器可能正在冷啟動，或分析時間過長。"
        except Exception as e:
            ai_response = f"連線失敗：{str(e)}"

    # 顯示並儲存 Agent 的回應
    st.chat_message("assistant").write(ai_response)
    st.session_state.messages.append({"role": "assistant", "content": ai_response})