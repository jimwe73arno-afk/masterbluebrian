import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from jarvis_memory import JarvisMemory
from jarvis_prompts import get_system_prompt

# 頁面設定
st.set_page_config(page_title="BrotherG Jarvis", page_icon="🧠", layout="wide")
load_dotenv()

# 標題
st.title("🧠 BrotherG Jarvis - 診斷模式")

# API Key 檢查
api_key = os.getenv("GEMINI_API_KEY")
if not api_key and "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

if not api_key:
    st.error("❌ 找不到 GEMINI_API_KEY，請檢查 Secrets！")
    st.stop()
else:
    # 隱碼顯示 Key 的前幾碼，確認有讀到
    masked_key = api_key[:5] + "..." + api_key[-3:]
    st.success(f"🔑 API Key 已載入: {masked_key}")

genai.configure(api_key=api_key)

# 初始化記憶
@st.cache_resource
def init_memory():
    return JarvisMemory()

try:
    memory = init_memory()
    st.success("📚 Firebase 記憶庫連線成功")
except Exception as e:
    st.error(f"🔥 Firebase 連線失敗: {e}")
    st.stop()

# 模型連線測試 (顯示詳細錯誤)
st.info("🔄 正在嘗試連線 Gemini 模型...")

candidates = [
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
    "gemini-2.0-flash-exp",
    "gemini-pro"
]

valid_model = None
error_logs = []

for model_name in candidates:
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Test")
        valid_model = model
        st.success(f"✅ 成功連線模型: **{model_name}**")
        break
    except Exception as e:
        error_msg = str(e)
        st.warning(f"⚠️ 嘗試 {model_name} 失敗: {error_msg}")
        error_logs.append(f"{model_name}: {error_msg}")

if not valid_model:
    st.error("❌ 所有模型連線失敗。請截圖此畫面回報。")
    with st.expander("查看詳細錯誤日誌"):
        for log in error_logs:
            st.code(log)
    st.stop()

# --- 如果成功連線，下面才是對話介面 ---

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("啟動診斷對話..."):
    st.chat_message("user").markdown(prompt)
    st.session_state["messages"].append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            # 這裡簡化流程，專注測試生成
            system_prompt = get_system_prompt()
            response = valid_model.generate_content(f"{system_prompt}\n\nUser: {prompt}")
            answer = response.text
            
            message_placeholder.markdown(answer)
            st.session_state["messages"].append({"role": "assistant", "content": answer})
        except Exception as e:
            st.error(f"生成回應時發生錯誤: {e}")
