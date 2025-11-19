import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from jarvis_memory import JarvisMemory
from jarvis_prompts import get_system_prompt

st.set_page_config(page_title="BrotherG Jarvis", page_icon="🧠", layout="wide")
load_dotenv()

st.title("🧠 BrotherG Jarvis - 簡約版")

# --- 1. API Key ---
api_key = os.getenv("GEMINI_API_KEY")
if not api_key and "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

if not api_key:
    st.error("❌ 找不到 API Key")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. 記憶庫 ---
try:
    memory = JarvisMemory()
    with st.sidebar:
        st.success("✅ Memory: Online")
except Exception as e:
    st.error(f"🔥 Memory Error: {e}")
    st.stop()

# --- 3. 模型 (直接指定，不輪詢) ---
# 使用最通用的標籤，由 Google 自動分配版本
TARGET_MODEL = "gemini-1.5-flash"

try:
    model = genai.GenerativeModel(TARGET_MODEL)
    # 測試一發
    response = model.generate_content("Hi")
    with st.sidebar:
        st.info(f"🚀 Engine: {TARGET_MODEL}")
except Exception as e:
    st.error(f"❌ 模型啟動失敗 (可能是 API Key 額度不足或無效)。\n錯誤訊息: {e}")
    st.stop()

# --- 4. 對話 ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Master Blue 請指示..."):
    st.chat_message("user").markdown(prompt)
    st.session_state["messages"].append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        msg_placeholder = st.empty()
        try:
            memories = memory.search_memories(prompt, limit=3)
            mem_text = "\n".join([f"- {m['content']}" for m in memories]) if memories else "無"
            
            sys_prompt = get_system_prompt()
            full_prompt = f"{sys_prompt}\n\n[參考記憶]:\n{mem_text}\n\nUser: {prompt}"
            
            response = model.generate_content(full_prompt)
            answer = response.text
            
            msg_placeholder.markdown(answer)
            st.session_state["messages"].append({"role": "assistant", "content": answer})
            
            memory.add_memory(f"Q: {prompt} | A: {answer[:30]}...", category="chat")
        except Exception as e:
            st.error(f"生成失敗: {e}")
