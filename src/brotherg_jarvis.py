import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from jarvis_memory import JarvisMemory
from jarvis_prompts import get_system_prompt

# 1. 頁面基礎設定
st.set_page_config(page_title="BrotherG Jarvis", page_icon="🧠", layout="wide")
load_dotenv()

# 2. 初始化 API Key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key and "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

if not api_key:
    st.error("❌ 找不到 GEMINI_API_KEY，請檢查 Secrets！")
    st.stop()

genai.configure(api_key=api_key)

# 3. 智能模型選擇器 (核心修復：自動尋找可用的模型)
def get_working_model():
    # 優先順序：2.0 (未來) -> 1.5 Flash Latest (穩定) -> 1.5 Flash (原版) -> Pro (保底)
    candidates = [
        "gemini-2.0-flash-exp",      # 嘗試 2025 年新模型
        "gemini-1.5-flash-latest",   # 強制指向最新版
        "gemini-1.5-flash",          # 原本設定
        "gemini-1.5-flash-001",      # 指定版號
        "gemini-pro"                 # 最後保底
    ]
    
    # 如果已經有選定的可用模型，直接回傳
    if "valid_model_name" in st.session_state:
        return genai.GenerativeModel(st.session_state["valid_model_name"])

    # 否則，測試哪個能用
    for model_name in candidates:
        try:
            model = genai.GenerativeModel(model_name)
            # 試打一個極短的用例確認存活
            model.generate_content("Hi") 
            st.session_state["valid_model_name"] = model_name
            # 在側邊欄偷偷告訴開發者現在用哪顆引擎
            with st.sidebar:
                st.caption(f"✅ Engine: {model_name}")
            return model
        except Exception:
            continue
    
    st.error("❌ 所有 Gemini 模型都無法連線，請檢查 API Key 配額或專案權限。")
    st.stop()

# 4. 初始化記憶與模型
@st.cache_resource
def init_memory():
    return JarvisMemory()

try:
    memory = init_memory()
    model = get_working_model() # 獲取自動測試過可用的模型
except Exception as e:
    st.error(f"🔥 系統啟動失敗: {e}")
    st.stop()

# 5. UI 佈局
st.title("🧠 BrotherG Jarvis - 第二大腦")

# 側邊欄
with st.sidebar:
    st.header("🔧 功能")
    if st.button("🗑️ 清除當前對話"):
        st.session_state["messages"] = []
        st.rerun()

# 6. 對話邏輯
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 顯示歷史訊息
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 處理用戶輸入
if prompt := st.chat_input("與 Jarvis 對話..."):
    # 顯示用戶訊息
    st.chat_message("user").markdown(prompt)
    st.session_state["messages"].append({"role": "user", "content": prompt})

    # 產生 AI 回應
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            # 檢索記憶
            related_memories = memory.search_memories(prompt, limit=3)
            memory_text = "\n".join([f"- {m['content']}" for m in related_memories]) if related_memories else "無相關記憶"

            # 組裝 Prompt
            system_prompt = get_system_prompt()
            full_prompt = f"""
            {system_prompt}
            
            [參考記憶]:
            {memory_text}
            
            [用戶問題]:
            {prompt}
            """
            
            # 呼叫模型
            response = model.generate_content(full_prompt)
            answer = response.text
            
            # 顯示並儲存
            message_placeholder.markdown(answer)
            st.session_state["messages"].append({"role": "assistant", "content": answer})
            
            # 寫入新記憶 (Observations)
            memory.add_memory(f"User asked: {prompt} -> AI answered: {answer[:50]}...", category="conversation")
            
        except Exception as e:
            st.error(f"生成失敗: {e}")
