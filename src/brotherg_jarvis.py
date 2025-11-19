import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from jarvis_memory import JarvisMemory
from jarvis_prompts import get_system_prompt

st.set_page_config(page_title="BrotherG Jarvis", page_icon="🧠", layout="wide")
load_dotenv()

st.title("🧠 BrotherG Jarvis - Powered by Gemini 2.5")

# ===== 1. API Key 配置 =====
try:
    import streamlit as st
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = os.getenv("GEMINI_API_KEY")
except:
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("❌ 找不到 GEMINI_API_KEY，請在 Streamlit Secrets 或 .env 中設定")
    st.stop()

genai.configure(api_key=api_key)

# ===== 2. 記憶庫初始化 =====
@st.cache_resource
def init_memory():
    """初始化記憶庫"""
    try:
        return JarvisMemory()
    except Exception as e:
        st.sidebar.warning(f"⚠️ 記憶庫離線: {str(e)[:50]}...")
        return None

memory = init_memory()

if memory:
    st.sidebar.success("✅ Memory: Online")
else:
    st.sidebar.warning("⚠️ Memory: Offline")

# ===== 3. 自動偵測並優先使用 Gemini 2.5 =====
@st.cache_resource
def find_best_gemini_model():
    """自動偵測並優先選擇 Gemini 2.5 Flash"""
    try:
        available_models = []
        
        # 列出所有支援 generateContent 的模型
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                available_models.append(model.name)
        
        if not available_models:
            return None, "沒有可用的模型", []
        
        # 🚀 模型優先級策略（2.5 優先！）
        priority_keywords = [
            "gemini-2.5-flash",      # 第一優先：2.5 Flash（最新最快）
            "gemini-2.5-pro",        # 第二優先：2.5 Pro（功能強大）
            "gemini-2.0-flash-exp",  # 第三優先：2.0 Flash 實驗版
            "gemini-1.5-flash",      # 第四優先：1.5 Flash（穩定）
            "gemini-1.5-pro",        # 第五優先：1.5 Pro
        ]
        
        # 依照優先級搜尋
        for keyword in priority_keywords:
            for model_name in available_models:
                if keyword in model_name.lower() and "latest" not in model_name.lower():
                    return model_name, "auto", available_models
        
        # 如果沒有找到優先模型，選第一個可用的
        return available_models[0], "fallback", available_models
        
    except Exception as e:
        return None, f"偵測失敗: {str(e)}", []

# 執行模型偵測
model_name, selection_method, all_models = find_best_gemini_model()

if not model_name:
    st.error(f"❌ 無法找到可用的 Gemini 模型: {selection_method}")
    st.stop()

# 顯示模型資訊
model_display_name = model_name.split('/')[-1]
st.sidebar.markdown("### 🤖 AI 引擎")

# 判斷模型版本並顯示對應圖示
if "2.5" in model_display_name:
    st.sidebar.success(f"🚀 {model_display_name}")
    st.sidebar.caption("⚡ Gemini 2.5 - 最新版本")
elif "2.0" in model_display_name:
    st.sidebar.info(f"🔵 {model_display_name}")
    st.sidebar.caption("🧪 Gemini 2.0 實驗版")
else:
    st.sidebar.info(f"🟢 {model_display_name}")
    st.sidebar.caption("✅ 穩定版本")

# 顯示可用模型列表（摺疊）
with st.sidebar.expander("📋 所有可用模型"):
    for m in all_models:
        st.caption(f"• {m.split('/')[-1]}")

# 初始化模型
try:
    model = genai.GenerativeModel(model_name)
except Exception as e:
    st.error(f"❌ 模型初始化失敗: {str(e)}")
    st.stop()

# ===== 4. 側邊欄功能 =====
with st.sidebar:
    st.markdown("---")
    st.subheader("📝 記憶管理")
    
    # 添加記憶
    with st.expander("➕ 添加新記憶"):
        new_memory = st.text_area("記憶內容", placeholder="輸入你想記住的事情...")
        memory_category = st.selectbox("分類", ["general", "tesla", "shopee", "travel"])
        
        if st.button("💾 儲存記憶"):
            if memory and new_memory:
                try:
                    memory.add_memory(new_memory, category=memory_category)
                    st.success("✅ 記憶已儲存！")
                except Exception as e:
                    st.error(f"儲存失敗: {str(e)}")
            elif not new_memory:
                st.warning("請輸入記憶內容")
            else:
                st.error("記憶庫未啟用")
    
    # 查看記憶
    with st.expander("🔍 查看最近記憶"):
        if memory:
            try:
                recent_memories = memory.get_recent_memories(limit=5)
                if recent_memories:
                    for i, mem in enumerate(recent_memories, 1):
                        st.text(f"{i}. {mem[:50]}...")
                else:
                    st.info("還沒有記憶")
            except Exception as e:
                st.error(f"讀取失敗: {str(e)}")
        else:
            st.warning("記憶庫未啟用")
    
    st.markdown("---")
    
    # 清空對話按鈕
    if st.button("🗑️ 清空對話歷史"):
        st.session_state.chat_history = []
        st.rerun()
    
    st.markdown("---")
    st.caption("💡 提示：對話會自動儲存到記憶庫")
    st.caption("🔧 API Key 已配置")

# ===== 5. 對話介面 =====
# 初始化對話歷史
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 顯示對話歷史
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 使用者輸入
if user_input := st.chat_input("問我任何問題..."):
    # 顯示使用者訊息
    with st.chat_message("user"):
        st.markdown(user_input)
    
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })
    
    # 生成回應
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # 檢索相關記憶
            memory_context = ""
            if memory:
                try:
                    relevant_memories = memory.search_memories(user_input, limit=3)
                    if relevant_memories:
                        memory_context = "\n[相關記憶]:\n" + "\n".join([
                            f"- {mem.get('content', '')[:100]}..."
                            for mem in relevant_memories
                        ])
                except Exception as e:
                    print(f"記憶檢索失敗: {e}")
            
            # 組合 Prompt
            system_prompt = get_system_prompt()
            full_prompt = f"{system_prompt}\n\n{memory_context}\n\n用戶問題: {user_input}"
            
            # 呼叫 Gemini 2.5
            with st.spinner("🤔 Jarvis 思考中..."):
                response = model.generate_content(full_prompt)
                assistant_reply = response.text
            
            # 顯示回應
            message_placeholder.markdown(assistant_reply)
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": assistant_reply
            })
            
            # 儲存對話到記憶庫
            if memory:
                try:
                    memory.add_memory(
                        f"Q: {user_input} | A: {assistant_reply[:100]}...",
                        category="chat"
                    )
                except Exception as e:
                    print(f"記憶儲存失敗: {e}")
            
        except Exception as e:
            error_msg = f"❌ 生成回應失敗: {str(e)}"
            message_placeholder.error(error_msg)
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": error_msg
            })

# 頁腳資訊
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🧠 BrotherG Jarvis v1.0")
with col2:
    st.caption(f"🤖 {model_display_name}")
with col3:
    if memory:
        st.caption("💾 記憶庫已連接")
    else:
        st.caption("💾 記憶庫離線")
