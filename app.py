import streamlit as st
import requests
import time

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
if "messages" not in st.session_state:
    st.session_state.messages = []
if "clues" not in st.session_state:
    st.session_state.clues = []

# 3. 사이드바 구성: 발견된 증거 목록
with st.sidebar:
    st.title("📂 CASE #2026-04")
    st.markdown("---")
    st.subheader("📋 발견된 증거 목록")
    
    if not st.session_state.clues:
        st.write("아직 확보된 단서가 없습니다.")
    else:
        for clue in st.session_state.clues:
            # 레벨에 따른 색상 정의
            lvl = clue['level']
            color = "#00ff00" if lvl == 1 else "#ffaa00" if lvl == 2 else "#ff4b4b"
            
            # 레벨 표시가 포함된 커스텀 HTML
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

# 기존 채팅 내역 출력 (rerun 시에도 화면 유지용)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 사용자 입력 처리
if query := st.chat_input("증거를 입력하거나 용의자를 심문하세요..."):
    # 사용자 질문 표시 및 저장
    with st.chat_message("user"):
        st.markdown(query)
    st.session_state.messages.append({"role": "user", "content": query})

    with st.spinner("중앙 데이터베이스 대조 중..."):
        try:
            # 백엔드 서버 호출
            res = requests.post("http://127.0.0.1:8000/investigation/ask", json={"question": query}, timeout=5)
            
            if res.status_code == 200:
                data = res.json()
                ans = data.get("answer", "응답을 받지 못했습니다.")
                lvl = data.get("level", 1)
                
                # 답변 출력 및 저장
                with st.chat_message("assistant"):
                    st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                
                # 증거 수집 성공 시 로직
                if data.get("status") == "success":
                    clean_text = ans.replace("조사 결과:", "").strip()
                    
                    # 중복 체크 (텍스트 기준)
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