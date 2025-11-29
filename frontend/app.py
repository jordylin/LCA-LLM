import streamlit as st
import requests
import time
from typing import Optional

# Simple page configuration
st.set_page_config(
    page_title="EcoLLM",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Clean CSS design
st.markdown("""
<style>
    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    .stDecoration {display: none;}
    
    /* Main container */
    .main > div {
        padding-top: 1rem;
        max-width: 800px;
        margin: 0 auto;
    }
    
    /* Title styles */
    .main-title {
        text-align: center;
        font-size: 2rem;
        font-weight: 400;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    
    .main-subtitle {
        text-align: center;
        font-size: 1rem;
        color: #7f8c8d;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    
    /* Card container */
    .card {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e1e8ed;
        margin-bottom: 1.5rem;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }
    
    .status-active { background-color: #27ae60; }
    .status-inactive { background-color: #e74c3c; }
    
    /* Message styles */
    .user-message {
        background: #f8f9fa;
        border-left: 3px solid #3498db;
        padding: 0.8rem;
        margin: 0.8rem 0;
        border-radius: 0 6px 6px 0;
    }
    
    .assistant-message {
        background: #ffffff;
        border-left: 3px solid #2ecc71;
        padding: 0.8rem;
        margin: 0.8rem 0;
        border-radius: 0 6px 6px 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    /* Chat container */
    .chat-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        background-color: #fafafa;
        margin-bottom: 1rem;
    }
    
    .chat-container::-webkit-scrollbar {
        width: 4px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 2px;
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 2px;
    }
</style>
""", unsafe_allow_html=True)

# 后端API配置
# 使用环境变量或默认 localhost（服务器端渲染时会自动解析）
import os
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# 初始化session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'mode' not in st.session_state:
    st.session_state.mode = "ai_chat"  # 🔥 默认使用 AI Chat 模式
if 'llm_session_id' not in st.session_state:
    st.session_state.llm_session_id = None
if 'llm_chat_history' not in st.session_state:
    st.session_state.llm_chat_history = []

def upload_pdf(file) -> Optional[str]:
    """上传PDF文件到后端（使用统一的 /tools/process-document 接口）"""
    try:
        import base64
        
        # 编码文件内容为base64
        file_content = base64.b64encode(file.getvalue()).decode()
        
        # 调用统一的工具接口
        payload = {
            "file_content": file_content,
            "filename": file.name
        }
        response = requests.post(
            f"{BACKEND_URL}/tools/process-document",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                # 从工具响应中提取session_id
                return result.get("data", {}).get("session_id")
            else:
                st.error(f"上传失败: {result.get('error', '未知错误')}")
                return None
        else:
            st.error(f"上传失败: {response.text}")
            return None
    except Exception as e:
        st.error(f"上传过程中出错: {str(e)}")
        return None

def search_lci_data(session_id: str, instruction: str) -> dict:
    """搜索LCI数据"""
    try:
        payload = {
            "session_id": session_id,
            "instruction": instruction
        }
        
        response = requests.post(
            f"{BACKEND_URL}/search-lci-data",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"请求失败: {response.text}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"请求过程中出错: {str(e)}"
        }

def check_session_status(session_id: str) -> bool:
    """检查会话状态"""
    try:
        response = requests.get(f"{BACKEND_URL}/session/{session_id}/status")
        if response.status_code == 200:
            result = response.json()
            return result.get("exists", False)
        return False
    except:
        return False

def create_llm_chat_session(pdf_session_id: str = None) -> Optional[str]:
    """创建LLM聊天会话"""
    try:
        payload = {"pdf_session_id": pdf_session_id}
        response = requests.post(
            f"{BACKEND_URL}/chat/create-session",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result.get("session_id")
        return None
    except Exception as e:
        st.error(f"Failed to create chat session: {str(e)}")
        return None

def send_llm_message(llm_session_id: str, message: str, pdf_session_id: str = None) -> dict:
    """发送消息给LLM"""
    try:
        payload = {
            "session_id": llm_session_id,
            "message": message
        }
        
        if pdf_session_id:
            payload["message"] = f"[PDF_SESSION_ID: {pdf_session_id}] {message}"
        
        response = requests.post(
            f"{BACKEND_URL}/chat/message",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"请求失败: {response.text}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"请求过程中出错: {str(e)}"
        }

# ==================== MAIN INTERFACE ====================

# Title section
st.markdown('<h1 class="main-title">LCA-LLM</h1>', unsafe_allow_html=True)
st.markdown('<p class="main-subtitle">Life Cycle Assessment Analysis Platform</p>', unsafe_allow_html=True)

# Status and reset
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    if st.session_state.session_id and check_session_status(st.session_state.session_id):
        st.markdown('<span class="status-indicator status-active"></span>Document Ready', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-indicator status-inactive"></span>No Document', unsafe_allow_html=True)
        if st.session_state.session_id:
            st.session_state.session_id = None

with col2:
    if st.session_state.llm_session_id:
        st.markdown('<span class="status-indicator status-active"></span>AI Assistant Ready', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-indicator status-inactive"></span>AI Assistant Inactive', unsafe_allow_html=True)

with col3:
    if st.button("Reset", type="secondary", use_container_width=True):
        st.session_state.session_id = None
        st.session_state.chat_history = []
        st.session_state.llm_session_id = None
        st.session_state.llm_chat_history = []
        if hasattr(st.session_state, 'start_mode'):
            del st.session_state.start_mode
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Starting options
if not st.session_state.session_id and not st.session_state.llm_session_id:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### Choose Analysis Mode")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Document Analysis**")
        st.markdown("Upload PDF for document-based analysis")
        if st.button("Upload Document", type="primary", use_container_width=True):
            st.session_state.start_mode = "document"
            st.rerun()
    
    with col2:
        st.markdown("**LCA Assistant**")
        st.markdown("Chat with AI assistant (no document needed)")
        if st.button("Start Chat", type="secondary", use_container_width=True):
            with st.spinner("Initializing..."):
                llm_session_id = create_llm_chat_session(pdf_session_id=None)
                if llm_session_id:
                    st.session_state.llm_session_id = llm_session_id
                    st.session_state.start_mode = "standalone"
                    st.success("AI assistant ready")
                    st.rerun()
                else:
                    st.error("Failed to initialize AI assistant")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Document upload
if hasattr(st.session_state, 'start_mode') and st.session_state.start_mode == "document" and not st.session_state.session_id:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### Upload Document")
    
    uploaded_file = st.file_uploader(
        label="Choose PDF file",
        type=['pdf'],
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        # 检查是否已经处理过这个文件（避免重复处理）
        if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != uploaded_file.name:
            with st.spinner("Processing document..."):
                session_id = upload_pdf(uploaded_file)
                
                if session_id:
                    st.session_state.session_id = session_id
                    st.session_state.last_uploaded_file = uploaded_file.name
                    # 不立即 rerun，让成功消息显示
                else:
                    st.error("❌ Failed to process document. Please check backend logs.")
        
        # 显示处理结果（rerun 后也能看到）
        if st.session_state.session_id:
            st.success(f"✅ Document processed successfully!")
            st.info(f"📄 Session ID: `{st.session_state.session_id[:8]}...`")
            
            # 添加按钮进入分析模式
            if st.button("Continue to Analysis →", type="primary", use_container_width=True):
                st.rerun()
    
    if st.button("← Back"):
        if hasattr(st.session_state, 'start_mode'):
            del st.session_state.start_mode
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Analysis mode selection (for document-based)
if st.session_state.session_id:
    # 🔥 自动初始化 AI Chat（不再需要手动切换模式）
    if not st.session_state.llm_session_id:
        with st.spinner("Initializing AI Chat..."):
            llm_session_id = create_llm_chat_session(st.session_state.session_id)
            if llm_session_id:
                st.session_state.llm_session_id = llm_session_id
                st.session_state.mode = "ai_chat"
                # 添加初始欢迎消息到聊天历史
                if not st.session_state.llm_chat_history:
                    session_id_short = st.session_state.session_id[:8] if st.session_state.session_id else "unknown"
                    st.session_state.llm_chat_history.append({
                        "role": "assistant",
                        "content": f"✅ Document successfully processed and ready for analysis!\n\nDocument ID: {session_id_short}...\n\nI have access to the document content and can search through it to answer your questions. What would you like to know about the document?"
                    })
                st.rerun()
            else:
                st.error("Failed to initialize AI assistant")
    
# Analysis interface
if st.session_state.session_id and st.session_state.mode:
    
    # AI Chat Mode (document-based)
    if st.session_state.mode == "ai_chat":
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### AI Chat")
        
        # Chat history
        if st.session_state.llm_chat_history:
            for i, msg in enumerate(st.session_state.llm_chat_history):
                if msg["role"] == "user":
                    with st.chat_message("user"):
                        st.write(msg["content"])
                else:
                    with st.chat_message("assistant"):
                        # 🔥 新增：如果有思考过程，用折叠面板显示
                        if msg.get("thinking"):
                            with st.expander("💭 Thinking Process", expanded=False):
                                st.text(msg["thinking"])
                        
                        # 显示实际回复
                        st.write(msg["content"])
                        
                        # Tool results
                        if msg.get("tool_results"):
                            with st.expander(f"🔧 Tool Results", expanded=False):
                                for tool_result in msg["tool_results"]:
                                    st.markdown(f"**{tool_result.get('tool_name', 'Unknown')}**")
                                    if tool_result.get("success"):
                                        st.success("Success")
                                        if tool_result.get("result"):
                                            st.json(tool_result["result"])
                                    else:
                                        st.error(f"Error: {tool_result.get('error', 'Unknown')}")
        
        # Chat input
        user_input = st.chat_input("Ask about your document...")
        
        if user_input and st.session_state.llm_session_id:
            st.session_state.llm_chat_history.append({
                "role": "user", 
                "content": user_input
            })
            
            with st.spinner("AI thinking..."):
                result = send_llm_message(
                    llm_session_id=st.session_state.llm_session_id, 
                    message=user_input,
                    pdf_session_id=st.session_state.session_id
                )
            
            if result.get("success"):
                assistant_msg = {
                    "role": "assistant",
                    "content": result.get("message", ""),
                    "thinking": result.get("thinking", ""),  # 🔥 新增：思考过程
                    "tool_results": result.get("tool_results")
                }
                st.session_state.llm_chat_history.append(assistant_msg)
            else:
                error_msg = {
                    "role": "assistant", 
                    "content": f"Error: {result.get('error', 'Unknown error')}"
                }
                st.session_state.llm_chat_history.append(error_msg)
            
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# Standalone AI Chat Mode
elif st.session_state.llm_session_id and not st.session_state.session_id:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### LCA Assistant")
    
    # Chat history
    if st.session_state.llm_chat_history:
        for i, msg in enumerate(st.session_state.llm_chat_history):
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["content"])
            else:
                with st.chat_message("assistant"):
                    # 🔥 新增：如果有思考过程，用折叠面板显示
                    if msg.get("thinking"):
                        with st.expander("💭 Thinking Process", expanded=False):
                            st.text(msg["thinking"])
                    
                    # 显示实际回复
                    st.write(msg["content"])
                    
                    # Tool results
                    if msg.get("tool_results"):
                        with st.expander(f"🔧 Tool Results", expanded=False):
                            for tool_result in msg["tool_results"]:
                                st.markdown(f"**{tool_result.get('tool_name', 'Unknown')}**")
                                if tool_result.get("success"):
                                    st.success("Success")
                                    if tool_result.get("result"):
                                        st.json(tool_result["result"])
                                else:
                                    st.error(f"Error: {tool_result.get('error', 'Unknown')}")
    
    # Chat input
    user_input = st.chat_input("Ask about LCA methodology or request data...")
    
    if user_input and st.session_state.llm_session_id:
        st.session_state.llm_chat_history.append({
            "role": "user", 
            "content": user_input
        })
        
        with st.spinner("AI thinking..."):
            result = send_llm_message(
                llm_session_id=st.session_state.llm_session_id, 
                message=user_input,
                pdf_session_id=None
            )
            
            if result and result.get("success"):
                assistant_msg = {
                    "role": "assistant", 
                    "content": result.get("message", "No response"),
                    "thinking": result.get("thinking", ""),  # 🔥 新增：思考过程
                    "tool_results": result.get("tool_results")
                }
                st.session_state.llm_chat_history.append(assistant_msg)
            else:
                error_msg = {
                    "role": "assistant", 
                    "content": f"Error: {result.get('error', 'Unknown error')}"
                }
                st.session_state.llm_chat_history.append(error_msg)
        
        st.rerun()
    
    # Reset option
    if st.button("New Conversation"):
        st.session_state.llm_session_id = None
        st.session_state.llm_chat_history = []
        if hasattr(st.session_state, 'start_mode'):
            del st.session_state.start_mode
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)