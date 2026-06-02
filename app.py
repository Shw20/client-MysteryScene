import streamlit as st
import requests
import time
import os  # 파일 존재 여부 확인을 위해 추가
import uuid


BACKEND_URL = os.getenv("MYSTERY_BACKEND_URL", "http://127.0.0.1:8000")


def create_session_id():
    """서버의 default 세션을 공유하지 않도록 접속마다 고유 세션 ID를 만든다."""

    return f"streamlit-{uuid.uuid4().hex}"


def load_story():
    """첫 화면에 보여줄 사건 도입부를 읽어온다."""

    story_path = "story.txt"
    if os.path.exists(story_path):
        with open(story_path, "r", encoding="utf-8") as f:
            return f.read()
    return "📁 사건 파일을 불러오지 못했습니다. story.txt 파일을 확인해주세요."


def reset_case_state():
    """새 사건 시작 시 프론트 상태와 서버 세션 ID를 함께 초기화한다."""

    st.session_state.session_id = create_session_id()
    st.session_state.clues = []
    st.session_state.messages = [{"role": "assistant", "content": load_story()}]

# 1. 페이지 설정 및 스타일 적용
st.set_page_config(page_title="Crime Scene AI", page_icon="🕵️", layout="wide")

st.markdown("""
    <style>
    /* 메인 배경색 및 텍스트 스타일 */
    .main { background-color: #1a1a1a; }
    .stTextInput>div>div>input { background-color: #2d2d2d; color: #00ff00; font-family: 'Courier New'; }
    
    /* 사이드바 증거 박스 스타일 */
    .clue-box { 
        padding: 12px; 
        border-radius: 8px; 
        border-left: 5px solid #ff4b4b; 
        margin-bottom: 15px; 
        background-color: #262626;
        color: #e0e0e0;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    
    /* 전체 텍스트 가독성 조절 */
    div[data-testid="stExpander"] p { color: #cccccc; }
    </style>
    """, unsafe_allow_html=True)

# 2. 세션 상태 초기화 (채팅 내역 및 증거 보관함)
if "session_id" not in st.session_state:
    st.session_state.session_id = create_session_id()

if "clues" not in st.session_state:
    st.session_state.clues = []

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": load_story()}]

# 3. 사이드바 구성: 발견된 증거 목록
with st.sidebar:
    st.title("📂 CASE #2026-04")
    if st.button("새 사건 시작", use_container_width=True):
        reset_case_state()
        st.rerun()
    st.markdown("---")
    st.subheader("📋 발견된 증거 목록")
    
    if not st.session_state.clues:
        st.write("아직 확보된 단서가 없습니다.")
    else:
        for clue in st.session_state.clues:
            lvl = clue['level']
            color = "#00ff00" if lvl == 1 else "#ffaa00" if lvl == 2 else "#ff4b4b"
            
            st.markdown(f"""
                <div class="clue-box">
                    <span style="color:{color}; font-weight:bold; font-size:0.8rem;">
                        [LEVEL {lvl}]
                    </span><br>
                    {clue['text']}
                </div>
                """, unsafe_allow_html=True)

# 4. 메인 화면 표시
st.title("🕵️ AI Investigation System")
st.caption("실시간 증거 분석 및 데이터베이스 대조 시스템 가동 중...")

# 기존 채팅 내역 출력
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # 💡 [추가] 첫 번째 메시지(index가 0인 시나리오 텍스트) 아래에 이미지 2개를 가로로 나란히 배치
        if idx == 0:
            col1, col2 = st.columns(2)
            with col1:
                if os.path.exists("beer.png"):
                    st.image("beer.png", caption="현장 단서 #1 (beer)", use_column_width=True)
                else:
                    st.caption("⚠️ beer.png 파일을 찾을 수 없습니다.")
            with col2:
                if os.path.exists("paper.png"):
                    st.image("paper.png", caption="현장 단서 #2 (paper)", use_column_width=True)
                else:
                    st.caption("⚠️ paper.png 파일을 찾을 수 없습니다.")

# 5. 사용자 입력 처리
if query := st.chat_input("증거를 입력하거나 용의자를 심문하세요..."):
    with st.chat_message("user"):
        st.markdown(query)
    st.session_state.messages.append({"role": "user", "content": query})

    with st.spinner("중앙 데이터베이스 대조 중..."):
        try:
            res = requests.post(
                f"{BACKEND_URL}/investigation/ask",
                json={
                    "question": query,
                    "session_id": st.session_state.session_id,
                },
                timeout=5,
            )
            
            if res.status_code == 200:
                data = res.json()
                ans = data.get("answer", "응답을 받지 못했습니다.")
                lvl = data.get("level", 1)
                
                with st.chat_message("assistant"):
                    st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                
                if data.get("status") == "success":
                    clean_text = ans.replace("조사 결과:", "").strip()
                    
                    if not any(c['text'] == clean_text for c in st.session_state.clues):
                        st.session_state.clues.append({
                            "text": clean_text,
                            "level": lvl
                        })
                        st.toast(f"🚨 Level {lvl} 증거 확보!", icon="✔")
                        st.rerun()
            else:
                st.error(f"서버 오류 (Code: {res.status_code})")
        
        except Exception as e:
            st.error(f"백엔드 연결 실패: {e}")
