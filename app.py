import streamlit as st
import requests

st.set_page_config(page_title="추리 게임: 기록 시스템", layout="wide")

# 1. 세션 상태 초기화 (찾은 단서들을 저장할 리스트)
if "clues" not in st.session_state:
    st.session_state.clues = []

# 사이드바 설정: 발견한 단서 기록장
with st.sidebar:
    st.header("📋 추리 기록장")
    if not st.session_state.clues:
        st.write("아직 발견된 단서가 없습니다.")
    else:
        for i, clue in enumerate(st.session_state.clues):
            st.info(f"{i+1}. {clue}")
    
    if st.button("기록 초기화"):
        st.session_state.clues = []
        st.rerun()

# 메인 화면
st.title("🕵️ 크라임씬: 증거 조사")

question = st.text_input("질문을 입력하세요", placeholder="예: 시계에 대해 조사해줘")

if question:
    try:
        response = requests.post("http://127.0.0.1:8000/ask", json={"question": question})
        
        if response.status_code == 200:
            answer = response.json().get("answer")
            st.chat_message("assistant").write(answer)
            
            # [핵심 로직] 답변에 '조사 결과'라는 단어가 포함되면 사이드바에 저장
            if "조사 결과:" in answer:
                # '조사 결과: ' 뒷부분만 추출해서 저장
                clue_text = answer.split("조사 결과:")[1].strip()
                if clue_text not in st.session_state.clues: # 중복 저장 방지
                    st.session_state.clues.append(clue_text)
                    st.rerun() # 사이드바 즉시 업데이트를 위해 재실행
        else:
            st.error("백엔드 오류 발생")
    except Exception as e:
        st.error(f"연결 실패: {e}")