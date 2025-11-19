import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from jarvis_memory import JarvisMemory
from jarvis_prompts import get_system_prompt

st.set_page_config(page_title="BrotherG Jarvis", page_icon="🧠", layout="wide")
load_dotenv()

st.title("🧠 BrotherG Jarvis - 混合動力版")

# --- API Key ---
api_key = os.getenv("GEMINI_API_KEY")
if not api_key and "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

if not api_key:
    st.error("❌ 找不到 API Key")
    st.stop()

genai.configure(api_key=api_key)

# --- 記憶庫 ---
@st.cache_resource
def init_memory():
    return JarvisMemory()

try:
    memory = init_memory()
    with st.sidebar:
        st.caption("✅ Memory: Online")
except Exception as e:
    st.error(f"🔥 Memory Error: {e}")
    st.stop()

# --- 模型選擇策略 (關鍵更新) ---
# 策略：先攻頂 (2.0/Pro)，失敗則守成 (1.5 Flash)
candidates = [
    "gemini-2.0-flash-exp",    # 1. 嘗試最新 (可能 429)
    "gemini-1.5-pro-002",      # 2. 嘗試最強智商 (可能慢)
    "gemini-1.5-flash-002",    # 3. 穩定且快 (主力保底)
    "gemini-1.5-flash",        # 4. 通用標籤 (最後防線)
]

if "valid_model_name" not in st.session_state:
    st.session_state["valid_model_name"] = None

# 自動輪詢
if not st.session_state["valid_model_name"]:
    progress_text = "正在測試最佳引擎..."
    my_bar = st.progress(0, text=progress_text)
    
    for i, model_name in enumerate(candidates):
        try:
            # 更新進度條
            my_bar.progress((i + 1) * 25, text=f"正在測試引擎: {model_name}...")
            
            model = genai.GenerativeModel(model_name)
            model.generate_content("Hi") # 測試一發
            
            st.session_state["valid_model_name"] = model_name
            my_bar.empty()
            st.toast(f"🚀 成功啟動引擎: {model_name}")
            break
        except Exception as e:
            # 如果是 429 (額度爆了)，就默默換下一個
            continue

if not st.session_state["valid_model_name"]:
    st.error("❌ 所有引擎啟動失敗。請檢查 API Key 額度。")
    st.stop()

# 顯示當前使用的引擎
active_model_name = st.session_state["valid_model_name"]
active_model = genai.GenerativeModel(active_model_name)

with st.sidebar:
    st.divider()
    st.write("🔥 **當前動力核心**")
    if "2.0" in active_model_name:
        st.success(f"⚡ {active_model_name} (最新版)")
    elif "pro" in active_model_name:
        st.info(f"🧠 {active_model_name} (高智商)")
    else:
        st.warning(f"🛡️ {active_model_name} (穩定模式)")
    
    st.caption("若顯示穩定模式，代表最新版額度已滿 (429)，系統自動降級以維持運作。")

# --- 對話介面 ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Master Blue 請指示..."):
    st.chat_message("user").markdown(prompt)
    st.session_state["messages"].append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            # 記憶檢索
            memories = memory.search_memories(prompt, limit=3)
            mem_text = "\n".join([f"- {m['content']}" for m in memories]) if memories else "無"

            # Prompt
            sys_prompt = get_system_prompt()
            full_prompt = f"{sys_prompt}\n\n[相關記憶]:\n{mem_text}\n\nUser: {prompt}"
            
            # 生成
            response = active_model.generate_content(full_prompt)
            answer = response.text
            
            message_placeholder.markdown(answer)
            st.session_state["messages"].append({"role": "assistant", "content": answer})
            
            # 寫入記憶
            memory.add_memory(f"Q: {prompt} | A: {answer[:30]}...", category="chat")
            
        except Exception as e:
            st.error(f"回答生成失敗: {e}")
