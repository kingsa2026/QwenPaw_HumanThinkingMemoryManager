# -*- coding: utf-8 -*-
"""Human Thinking Tool Vector Search Module"""
import hashlib
import json
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class VectorSearch:
    """向量搜索类"""

    def __init__(self, db, agent_id: str):
        """初始化向量搜索

        Args:
            db: 数据库实例
            agent_id: Agent ID
        """
        self.db = db
        self.agent_id = agent_id
        self.vectorizer = TfidfVectorizer()
        self._cache = {}

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """获取文本的向量嵌入

        Args:
            text: 文本

        Returns:
            List[float]: 向量嵌入
        """
        # 简单的TF-IDF向量作为示例
        # 实际项目中应该使用真实的嵌入模型
        try:
            # 检查缓存
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if text_hash in self._cache:
                return self._cache[text_hash]

            # 计算TF-IDF向量
            vectors = self.vectorizer.fit_transform([text])
            embedding = vectors.toarray()[0].tolist()

            # 缓存结果
            self._cache[text_hash] = embedding
            return embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return None

    async def add_embedding(self, memory_id: int, content: str):
        """添加记忆的向量嵌入

        Args:
            memory_id: 记忆ID
            content: 记忆内容
        """
        try:
            # 获取嵌入
            embedding = await self.get_embedding(content)
            if embedding:
                # 转换为bytes存储
                embedding_bytes = json.dumps(embedding).encode()
                # 插入向量
                vector_id = self.db.insert_vector(embedding_bytes)
                # 更新记忆的向量ID
                self.db.update_memory_vector(memory_id, vector_id)
        except Exception as e:
            print(f"Error adding embedding: {e}")

    def search_similar(self, query_text: str, top_k: int = 5, 
                      min_score: float = 0.1) -> List[Dict[str, Any]]:
        """搜索相似的记忆

        Args:
            query_text: 查询文本
            top_k: 最大返回结果数
            min_score: 最小相关度分数

        Returns:
            List[Dict[str, Any]]: 搜索结果
        """
        try:
            # 检查缓存
            query_hash = hashlib.md5(query_text.encode()).hexdigest()
            cache = self.db.get_cache(query_hash)
            if cache:
                vector_ids = json.loads(cache['vector_ids'])
                scores = json.loads(cache['scores'])
                results = []
                for vector_id, score in zip(vector_ids, scores):
                    if score >= min_score:
                        memory = self.db.get_memory_by_id(vector_id)
                        if memory:
                            memory['score'] = score
                            results.append(memory)
                return results[:top_k]

            # 搜索记忆
            memories = self.db.search_memories(query_text, max_results=100)
            if not memories:
                return []

            # 计算相似度
            query_embedding = self.vectorizer.fit_transform([query_text])
            memory_contents = [mem['content'] for mem in memories]
            memory_embeddings = self.vectorizer.transform(memory_contents)

            # 计算余弦相似度
            similarities = cosine_similarity(query_embedding, memory_embeddings)[0]

            # 排序并过滤
            results = []
            for i, score in enumerate(similarities):
                if score >= min_score:
                    memory = memories[i]
                    memory['score'] = score
                    results.append(memory)

            # 按分数排序
            results.sort(key=lambda x: x['score'], reverse=True)

            # 缓存结果
            if results:
                vector_ids = [r['id'] for r in results]
                scores = [r['score'] for r in results]
                self.db.insert_cache(query_hash, vector_ids, scores)

            return results[:top_k]
        except Exception as e:
            print(f"Error searching similar: {e}")
            #  fallback 到简单搜索
            return self.db.search_memories(query_text, max_results=top_k)


class FallbackVectorSearch:
    """Fallback向量搜索类（当向量搜索不可用时使用）"""

    def __init__(self, db, agent_id: str):
        """初始化Fallback向量搜索

        Args:
            db: 数据库实例
            agent_id: Agent ID
        """
        self.db = db
        self.agent_id = agent_id

    def search_similar(self, query_text: str, top_k: int = 5, 
                      min_score: float = 0.1) -> List[Dict[str, Any]]:
        """搜索相似的记忆

        Args:
            query_text: 查询文本
            top_k: 最大返回结果数
            min_score: 最小相关度分数

        Returns:
            List[Dict[str, Any]]: 搜索结果
        """
        try:
            # 简单的关键词搜索
            memories = self.db.search_memories(query_text, max_results=top_k)
            # 为结果添加默认分数
            for mem in memories:
                mem['score'] = 0.5  # 默认分数
            return memories
        except Exception as e:
            print(f"Error in fallback search: {e}")
            return []
