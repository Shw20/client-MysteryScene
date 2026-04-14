import os
import json
import numpy as np

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 1. 코사인 유사도 계산 [cite: 128]
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# 2. 임베딩 생성 (text-embedding-3-small) [cite: 114]
def get_embedding(text):
    response = client.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding

# 3. 데이터 로드 및 임베딩 초기화 [cite: 116, 123]
def load_evidence():
    db_path = "database/evidence.json"
    if not os.path.exists(db_path): return []
    with open(db_path, "r", encoding="utf-8") as f:
        evidences = json.load(f)
    
    # 각 단서에 임베딩이 없으면 생성 (최초 1회) [cite: 63, 125]
    for e in evidences:
        if "embedding" not in e or not e["embedding"]:
            e["embedding"] = get_embedding(e["content"])
    return evidences

# 4. 메인 RAG 함수 (진행자 페르소나 적용)
def get_game_master_response(question, current_level, evidences):
    query_vec = get_embedding(question) # [cite: 66]
    
    # Level 기반 필터링: 현재 레벨 이하의 단서만 검색 대상 [cite: 71, 82]
    filtered = [e for e in evidences if e['level'] <= current_level]
    
    # 유사도 계산 및 Top-3 추출 [cite: 73, 74]
    for e in filtered:
        e["score"] = cosine_similarity(query_vec, e["embedding"])
    top_k = sorted(filtered, key=lambda x: x["score"], reverse=True)[:3]
    
    context = "\n".join([f"- {item['content']}" for item in top_k])
    
    # 진행자(Master) 페르소나 프롬프트 [cite: 130]
    prompt = f"""   
    너는 추리 게임의 '게임 진행자(Master)'다. 사용자가 사건의 진실에 도달하도록 돕는 역할이다.
    
    [규칙]
    1. 반드시 제공된 [단서] 리스트에 있는 정보만 활용할 것. [cite: 130, 132]
    2. 정답이나 범인을 직접 알려주지 말고, 사용자가 스스로 생각하도록 유도할 것. [cite: 134]
    3. 제공된 정보에 답이 없으면 "그 부분은 아직 안개에 가려져 있군요. 다른 쪽을 조사해보세요."라고 답할 것. [cite: 130, 136]
    4. 친절하지만 신비로운 진행자의 말투를 유지할 것.
    
    [단서]
    {context}
    
    [사용자 질문]
    {question}
    """

# 출력용 모델
    response = client.chat.completions.create(
        model="gpt-4o-mini", # [cite: 157]
        messages=[{"role": "system", "content": prompt}]
    )
    return response.choices[0].message.content