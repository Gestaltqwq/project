import os
import torch
import jieba
from rank_bm25 import BM25Okapi
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from dotenv import load_dotenv

# .env 按日期文件夹各放一份，保证从任意目录运行都能加载
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# ===================== 配置 =====================
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

# 模型/向量库都在仓库根目录；本地模型必须用绝对路径（transformers 5.14.1 相对路径报错）
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
EMBED_PATH = os.path.join(ROOT, "bge-large-zh")        # 本地嵌入模型（构建向量库的同款）
RERANK_PATH = os.path.join(ROOT, "bge-reranker-base")  # 本地重排序模型（缺失则跳过精排）

# 稠密检索（Dense）：向量语义
DENSE_TOP_K = 10
# 稀疏检索（Sparse）：BM25 关键词
SPARSE_TOP_K = 10
# RRF 融合（Reciprocal Rank Fusion）
RRF_K = 60          # 融合常数（越小，名次差距带来的分差越大）
FINAL_TOP_K = 8     # RRF 融合后保留条数
# 精排（Rerank）
RERANK_TOP_K = 2    # 精排后最终输出条数

# ===================== 本地 Reranker（精排） =====================
class LocalReranker:
    def __init__(self, model_path):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.eval()

    def rank(self, query, docs):
        """对候选文档按(query, doc)交叉编码重新打分，从高到低排序"""
        pairs = [[query, doc.page_content] for doc in docs]
        with torch.no_grad():
            inputs = self.tokenizer(
                pairs,
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=512
            )
            scores = self.model(**inputs, return_dict=True).logits.view(-1).float()
            scores = scores.tolist()

        ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, score in ranked]


def download_reranker():
    """把 bge-reranker-base 下载到仓库根目录（走 hf-mirror 镜像，约 1.1GB）"""
    from huggingface_hub import snapshot_download
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    os.makedirs(ROOT, exist_ok=True)
    print(f"⬇️  正在下载 bge-reranker-base 到 {RERANK_PATH} ...")
    snapshot_download("BAAI/bge-reranker-base", local_dir=RERANK_PATH)
    print("✅ 下载完成")


# 全局加载一次（避免重复加载）；模型缺失时跳过，不阻塞检索
reranker = None
if os.path.isdir(RERANK_PATH):
    reranker = LocalReranker(RERANK_PATH)
else:
    print(f"⚠️ 未找到本地重排序模型：{RERANK_PATH}")
    print("   （可调用 download_reranker() 下载，或跳过精排）")

# ===================== 混合检索器 =====================
def tokenize(text):
    """中文分词（jieba），供稀疏检索 BM25 使用"""
    return [t.strip() for t in jieba.cut(text) if t.strip()]


class HybridRetriever:
    """检索链路：稠密检索 + 稀疏检索 → RRF 融合 → 精排"""

    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        data = vectorstore.get(include=["documents", "metadatas"])
        self.docs = [
            Document(page_content=d, metadata=m if m else {})
            for d, m in zip(data["documents"], data["metadatas"])
        ]
        # 稀疏索引：BM25 + jieba 分词，一次性构建（避免每次检索重建）
        self.bm25 = BM25Okapi([tokenize(d.page_content) for d in self.docs])
        print(f"✅ 稀疏检索索引（BM25）构建完成，共 {len(self.docs)} 个分块")

    # ---------- 稠密检索（Dense Retrieval）----------
    def dense_search(self, query, top_k=DENSE_TOP_K):
        """稠密检索：嵌入向量算语义相似度，返回 [(Document, 距离)]"""
        return self.vectorstore.similarity_search_with_score(query, k=top_k)

    # ---------- 稀疏检索（Sparse Retrieval）----------
    def sparse_search(self, query, top_k=SPARSE_TOP_K):
        """稀疏检索：BM25 按关键词精确匹配打分，返回 [Document]"""
        scores = self.bm25.get_scores(tokenize(query))
        ranked = sorted(range(len(self.docs)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [self.docs[i] for i in ranked]

    # ---------- RRF 融合 ----------
    def hybrid_search(self, query, top_k=FINAL_TOP_K):
        """把稠密/稀疏两个榜单按名次融合，返回 [(Document, 融合分)]"""
        dense = self.dense_search(query)
        sparse = self.sparse_search(query)

        # 名次越靠前贡献越高：1/(K + rank + 1)，两榜分数直接相加
        rrf = {}      # page_content -> 融合分
        doc_map = {}  # page_content -> Document
        for rank, (doc, _score) in enumerate(dense):
            doc_map[doc.page_content] = doc
            rrf[doc.page_content] = rrf.get(doc.page_content, 0.0) + 1.0 / (RRF_K + rank + 1)
        for rank, doc in enumerate(sparse):
            doc_map[doc.page_content] = doc
            rrf[doc.page_content] = rrf.get(doc.page_content, 0.0) + 1.0 / (RRF_K + rank + 1)

        ranked = sorted(rrf.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [(doc_map[content], score) for content, score in ranked]

    # ---------- 精排（Rerank）----------
    def rerank(self, query, docs):
        """用交叉编码 Reranker 对 RRF 结果二次排序；无模型则直接截断"""
        if reranker is None:
            return docs[:RERANK_TOP_K]
        return reranker.rank(query, docs)[:RERANK_TOP_K]


def format_docs(docs):
    return "\n".join(x.page_content for x in docs)

# ===================== RAG 主流程 =====================
def run_rag_qa(query, persist_directory=None):
    if persist_directory is None:
        persist_directory = os.path.join(ROOT, "chroma_db")
    if not os.path.exists(persist_directory):
        print("❌ 请先构建向量数据库")
        return

    # 向量库（必须和构建时用同一个嵌入模型）
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_PATH,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )
    vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)

    retriever = HybridRetriever(vectorstore)

    # —— 双路召回对比：稠密 vs 稀疏 ——
    dense_top = retriever.dense_search(query, 3)
    sparse_top = retriever.sparse_search(query, 3)
    print("\n" + "=" * 60)
    print(f"双路召回对比（问题：{query}）")
    print("=" * 60)
    print("▶ 稠密检索（向量语义）Top3：")
    for i, (doc, score) in enumerate(dense_top, 1):
        print(f"  [{i}] {doc.page_content[:60].replace(chr(10), ' ')}  (距离 {score:.4f})")
    print("▶ 稀疏检索（BM25 关键词）Top3：")
    for i, doc in enumerate(sparse_top, 1):
        print(f"  [{i}] {doc.page_content[:60].replace(chr(10), ' ')}")

    # —— RRF 融合（稠密 + 稀疏）——
    fused = retriever.hybrid_search(query)
    print(f"\n▶ RRF 融合 Top{len(fused)}：")
    for i, (doc, score) in enumerate(fused, 1):
        print(f"  [{i}] {doc.page_content[:60].replace(chr(10), ' ')}  (RRF {score:.4f})")

    # —— 精排（Reranker 二次打分）——
    docs = retriever.rerank(query, [doc for doc, _ in fused])

    print("\n" + "=" * 60)
    print(f"✅ 稠密+稀疏 RRF 融合 + 精排完成，最终返回 {len(docs)} 条")
    print("=" * 60)
    for i, d in enumerate(docs):
        print(f"\n结果 {i + 1}：\n{d.page_content}\n")

    # LLM
    llm = ChatOpenAI(model=model_name, temperature=0, api_key=api_key, base_url=base_url)

    system_prompt = (
        "你是星讯科技有限公司的内部智能人事/行政助手。\n"
        "请严格基于以下提供的公司内部文档内容回答用户问题。\n"
        "如果找不到答案，请直接说“根据提供的文档，我无法回答该问题”，不要编造。\n\n"
        "【参考文档】\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # RAG 链
    rag_chain = (
        {"context": lambda x: format_docs(docs), "input": lambda x: x["input"]}
        | prompt
        | llm
        | StrOutputParser()
    )

    print("================ 问答 ================")
    print(f"问题：{query}")
    answer = rag_chain.invoke({"input": query})
    print(f"\n回答：\n{answer}")
    print("=" * 60)

if __name__ == "__main__":
    run_rag_qa("节日和生日福利有什么？")
