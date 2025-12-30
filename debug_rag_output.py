
from aixiaoliang_agent.tools.knowledge_tool import search_knowledge

def test_rag_output():
    query = "市盈率 市净率 总市值"
    print(f"Query: {query}")
    print("-" * 50)
    result = search_knowledge(query)
    print("RAG Result:")
    print(result)
    print("-" * 50)
    
    if "data['" in result or "fields=[" in result:
        print("✅ SUCCESS: Usage examples detected in output.")
    else:
        print("❌ FAILURE: No usage examples found. Prompt tuning needed.")

if __name__ == "__main__":
    test_rag_output()
