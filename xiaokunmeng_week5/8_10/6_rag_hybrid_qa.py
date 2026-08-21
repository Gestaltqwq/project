import os
import jieba
from rank_bm25 import BM25Okapi
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

from embedding import get_embeddings

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
llm_model = os.getenv("MODEL_NAME")

VECTOR_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "chroma_db")
)


def tokenize(text):
    return [t.strip() for t in jieba.cut(text) if t.strip()]# 分词


class HybridRetriever:
    def __init__(self, vectorstore, vector_top=10, bm25_top=10, fusion_k=60):
        self.vectorstore = vectorstore
        self.vector_top = vector_top
        self.bm25_top = bm25_top
        self.K = fusion_k
        col = vectorstore._collection
        data = col.get(include=["documents"])
        self.chunks = data["documents"]
        self.bm25 = BM25Okapi([tokenize(c) for c in self.chunks])# 构建BM25索引
        print(f"BM25 索引构建完成，共 {len(self.chunks)} 个分块。")

    def vector_search(self, query, top_k):
        hits = self.vectorstore.similarity_search_with_score(query, k=top_k)# 向量检索
        return [(d.page_content, s) for d, s in hits]

    def bm25_search(self, query, top_k):
        scores = self.bm25.get_scores(tokenize(query))
        ranked = sorted(range(len(self.chunks)), key=lambda i: scores[i], reverse=True)[:top_k]# BM25检索
        return [(self.chunks[i], scores[i]) for i in ranked]

    def hybrid_search(self, query, top_k=5):
        vec = self.vector_search(query, self.vector_top)
        bm = self.bm25_search(query, self.bm25_top)

        rrf = {}
        for rank, (content, _) in enumerate(vec):
            rrf[content] = rrf.get(content, 0.0) + 1.0 / (self.K + rank + 1)
        for rank, (content, _) in enumerate(bm):
            rrf[content] = rrf.get(content, 0.0) + 1.0 / (self.K + rank + 1)

        ranked = sorted(rrf.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


def run_hybrid_rag_qa(query, top_k=5):
    embeddings = get_embeddings()
    vectorstore = Chroma(persist_directory=VECTOR_DIR, embedding_function=embeddings)

    retriever = HybridRetriever(vectorstore)

    vec_top = retriever.vector_search(query, 3)
    bm_top = retriever.bm25_search(query, 3)
    hybrid_top = retriever.hybrid_search(query, top_k=top_k)

    print("三种检索方式对比")
    print(f"提问: {query}\n")
    print("纯向量语义检索Top3")
    for i, (content, s) in enumerate(vec_top, 1):
        print(f"  [{i}] {content[:60].replace(chr(10), ' ')}  (距离{s:.3f})")
    print("纯 BM25 关键词检索Top3")
    for i, (content, s) in enumerate(bm_top, 1):
        print(f"  [{i}] {content[:60].replace(chr(10), ' ')}  (分{s:.1f})")
    print(f"混合检索(RRF融合)Top{top_k}")
    for i, (content, s) in enumerate(hybrid_top, 1):
        print(f"  [{i}] {content[:60].replace(chr(10), ' ')}  (融合分{s:.4f})")

    context = "\n".join(content for content, _ in hybrid_top)
    llm = ChatOpenAI(model=llm_model, temperature=0, api_key=api_key, base_url=base_url)
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "你是一个严谨的文档问答助手。\n"
            "请严格基于【参考文档内容】回答用户问题，不要编造信息。\n"
            "如果文档中没有相关信息，请直接回答“根据提供的文档，我无法回答该问题”。\n\n"
            "【参考文档内容】\n{context}"
        )),
        ("human", "{input}"),
    ])
    chain = prompt | llm | StrOutputParser()

    print("\n" + "=" * 60)
    print("用户提问:", query)
    print("正在生成答案...\n")
    answer = chain.invoke({"context": context, "input": query})
    print("回答:")
    print(answer)
    print("=" * 60 + "\n")


if __name__ == "__main__":
    test_queries = [
        "华为2025年的营业收入是多少？",
        "华为每年研发投入占销售收入的比例是多少？",
        "华为目前的员工数量是多少？",
    ]
    for q in test_queries:
        run_hybrid_rag_qa(q)
