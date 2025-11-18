import streamlit as st
import os
from jarvis_memory import JarvisMemory
from jarvis_prompts import SYSTEM_PROMPT
import google.generativeai as genai

# 页面配置
st.set_page_config(
    page_title="BrotherG Jarvis",
    page_icon="🧠",
    layout="wide"
)

# 初始化 Gemini
try:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
except:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    st.error("❌ 未设置 GEMINI_API_KEY")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# 初始化记忆系统
@st.cache_resource
def init_memory():
    return JarvisMemory()

memory = init_memory()

# 主界面
st.title("🧠 BrotherG Jarvis - 第二大脑")

# 侧边栏
with st.sidebar:
    st.header("🎯 功能")
    
    # 添加记忆
    with st.expander("➕ 添加记忆"):
        context = st.text_input("场景/分类", key="add_context")
        insight = st.text_area("洞察/想法", key="add_insight")
        plan = st.text_area("计划/行动", key="add_plan")
        risk = st.text_area("风险/注意", key="add_risk")
        tags = st.text_input("标签（用逗号分隔）", key="add_tags")
        
        if st.button("💾 保存记忆"):
            if insight:
                memory_id = memory.add_memory(
                    context=context,
                    insight=insight,
                    plan=plan,
                    risk=risk,
                    tags=tags
                )
                st.success(f"✅ 记忆已保存！ID: {memory_id}")
            else:
                st.warning("⚠️ 请至少输入洞察内容")
    
    # 搜索记忆
    with st.expander("🔍 搜索记忆"):
        search_query = st.text_input("搜索关键词", key="search_query")
        search_limit = st.slider("返回结果数", 1, 10, 5)
        
        if st.button("🔎 搜索"):
            if search_query:
                results = memory.search_memories(search_query, limit=search_limit)
                if results:
                    st.write(f"找到 {len(results)} 条记忆：")
                    for mem in results:
                        with st.container():
                            st.markdown(f"**📅 {mem['timestamp']}**")
                            st.markdown(f"**🏷️ {mem['context']}**")
                            st.markdown(f"💡 {mem['insight']}")
                            if mem['plan']:
                                st.markdown(f"📋 {mem['plan']}")
                            if mem['tags']:
                                st.markdown(f"🔖 {mem['tags']}")
                            st.divider()
                else:
                    st.info("未找到相关记忆")

# 对话界面
st.header("💬 与 Jarvis 对话")

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示对话历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入
if prompt := st.chat_input("问我任何问题..."):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 搜索相关记忆
    relevant_memories = memory.search_memories(prompt, limit=3)
    
    # 构建上下文
    context = SYSTEM_PROMPT + "\n\n"
    if relevant_memories:
        context += "## 相关记忆：\n"
        for mem in relevant_memories:
            context += f"- [{mem['context']}] {mem['insight']}\n"
        context += "\n"
    
    # 调用 Gemini
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(context + "\n用户问题：" + prompt)
                answer = response.text
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"❌ 错误：{str(e)}")

# 页脚
st.divider()
st.caption("🧠 BrotherG Jarvis - 你的第二大脑 | Powered by Gemini & Firebase")
