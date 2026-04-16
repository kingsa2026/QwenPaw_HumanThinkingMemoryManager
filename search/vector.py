# -*- coding: utf-8 -*-
"""Human Thinking Tool Vector Search Module"""
import logging
import json
import hashlib
import heapq
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

__version__ = "1.0.2-beta0.3"


class BaseVectorSearcher:
    """向量搜索基类"""
    
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.db = memory_manager.db
    
    def is_available(self) -> bool:
        """检查是否可用"""
        raise NotImplementedError
    
    async def search(
        self,
        query: str,
        max_results: int = 5,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        include_frozen: bool = False
    ) -> List[Dict[str, Any]]:
        """搜索记忆"""
        raise NotImplementedError
    
    def _get_agent_memories(
        self,
        agent_id: str,
        include_frozen: bool = False,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取 Agent 的记忆（带过滤）"""
        if not self.db:
            return []
        
        # 使用数据库的文本搜索方法获取记忆
        return self.db.search_by_text(
            query="",  # 空查询获取所有记忆
            max_results=1000,  # 限制数量以提高性能
            agent_id=agent_id,
            session_id=session_id,
            include_frozen=include_frozen
        )


class TFIDFVectorSearcher(BaseVectorSearcher):
    """
    TF-IDF 向量搜索
    
    基于 TF-IDF 的轻量级向量搜索实现
    """
    
    def __init__(self, memory_manager):
        super().__init__(memory_manager)
        self._index: Dict[str, Dict[str, float]] = {}
        self._document_count = 0
        self._last_index_time = 0
        self._index_interval = 5  # 索引更新间隔（秒）
    
    def is_available(self) -> bool:
        """检查是否可用"""
        return self.db is not None
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        import re
        # 简单分词：按空格和标点分割，转小写
        tokens = re.findall(r'\w+', text.lower())
        return [t for t in tokens if len(t) > 1]
    
    def _calculate_tf(self, tokens: List[str]) -> Dict[str, float]:
        """计算词频"""
        tf = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        
        # 归一化
        total = len(tokens)
        for token in tf:
            tf[token] /= total
        
        return tf
    
    def _calculate_idf(self, documents: List[List[str]]) -> Dict[str, float]:
        """计算逆文档频率"""
        import math
        
        N = len(documents)
        idf = {}
        
        # 统计包含每个词的文档数
        for doc in documents:
            for token in set(doc):
                idf[token] = idf.get(token, 0) + 1
        
        # 计算 IDF
        for token in idf:
            idf[token] = math.log(N / (idf[token] + 1))
        
        return idf
    
    def _build_index(self, memories: List[Dict[str, Any]]):
        """构建 TF-IDF 索引"""
        if not memories:
            return
        
        # 分词
        tokenized_docs = []
        for memory in memories:
            tokens = self._tokenize(memory["content"])
            tokenized_docs.append(tokens)
        
        # 计算 IDF
        self._idf = self._calculate_idf(tokenized_docs)
        self._document_count = len(memories)
        
        # 构建 TF-IDF 向量
        self._index = {}
        for i, (memory, tokens) in enumerate(zip(memories, tokenized_docs)):
            tf = self._calculate_tf(tokens)
            
            # TF-IDF
            tfidf = {}
            for token, tf_value in tf.items():
                tfidf[token] = tf_value * self._idf.get(token, 0)
            
            self._index[memory["id"]] = tfidf
    
    def _cosine_similarity(
        self,
        vec1: Dict[str, float],
        vec2: Dict[str, float]
    ) -> float:
        """计算余弦相似度"""
        import math
        
        # 计算点积
        dot_product = sum(vec1.get(token, 0) * vec2.get(token, 0) 
                         for token in set(vec1) | set(vec2))
        
        # 计算模
        norm1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def search(
        self,
        query: str,
        max_results: int = 5,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        include_frozen: bool = False
    ) -> List[Dict[str, Any]]:
        """
        TF-IDF 搜索
        
        Args:
            query: 查询文本
            max_results: 最大结果数
            agent_id: Agent ID
            session_id: 会话ID，用于过滤特定会话的记忆
            include_frozen: 是否包含冷藏记忆
            
        Returns:
            记忆列表
        """
        if not agent_id:
            agent_id = self.memory_manager.agent_id
        
        # 获取记忆
        memories = self._get_agent_memories(agent_id, include_frozen, session_id)
        
        if not memories:
            return []
        
        # 检查是否需要更新索引
        import time
        current_time = time.time()
        if current_time - self._last_index_time > self._index_interval or not self._index:
            # 构建索引
            self._build_index(memories)
            self._last_index_time = current_time
        
        # 查询向量化
        query_tokens = self._tokenize(query)
        query_tf = self._calculate_tf(query_tokens)
        
        # 计算相似度，加入时间因素和搜索频率
        similarities = []
        current_datetime = datetime.now()
        
        for memory in memories:
            # 计算文本相似度
            memory_vector = self._index.get(memory["id"], {})
            text_similarity = self._cosine_similarity(query_tf, memory_vector)
            
            if text_similarity < 0.01:  # 过滤低相似度
                continue
            
            # 计算时间权重（越近的时间权重越高）
            time_weight = 1.0
            if memory.get("created_at"):
                try:
                    memory_time = datetime.fromisoformat(memory["created_at"])
                    time_diff = (current_datetime - memory_time).total_seconds() / 3600  # 小时
                    # 时间衰减函数：1/(1+time_diff/24)，24小时后权重降为0.5
                    time_weight = 1 / (1 + time_diff / 24)
                except:
                    pass
            
            # 计算访问频率权重
            access_weight = 1.0
            if memory.get("access_count"):
                # 访问次数越多，权重越高，但有上限
                access_weight = min(1.5, 1 + memory["access_count"] / 10)
            
            # 计算综合相似度
            total_similarity = text_similarity * 0.6 + time_weight * 0.3 + access_weight * 0.1
            
            similarities.append((memory, total_similarity))
        
        # 排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # 批量更新搜索频率和分数
        memory_ids = []
        scores = []
        
        # 返回结果
        results = []
        for memory, sim in similarities[:max_results]:
            memory["similarity"] = sim
            # 记录搜索频率并更新权重
            if 'id' in memory:
                memory_ids.append(memory["id"])
                scores.append(sim)
            results.append(memory)
        
        # 批量更新
        if memory_ids:
            self.db.batch_update_memory_search(memory_ids, scores)
        
        return results


class VectorCache:
    """
    向量缓存
    
    缓存查询结果以提升性能
    """
    
    def __init__(self, db, ttl_seconds: int = 3600):
        self.db = db
        self.ttl_seconds = ttl_seconds
    
    def _generate_hash(self, query: str, agent_id: str, max_results: int) -> str:
        """生成查询哈希"""
        key = f"{query}:{agent_id}:{max_results}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(
        self,
        query: str,
        agent_id: str,
        max_results: int
    ) -> Optional[List[Tuple[int, float]]]:
        """获取缓存"""
        query_hash = self._generate_hash(query, agent_id, max_results)
        
        # 使用数据库的缓存查询方法
        cache = self.db.get_cache(query_hash)
        if not cache:
            return None
        
        # 解析结果
        vector_ids = json.loads(cache['vector_ids'])
        scores = json.loads(cache['similarity_scores'])
        
        return list(zip(vector_ids, scores))
    
    def set(
        self,
        query: str,
        agent_id: str,
        max_results: int,
        results: List[Dict[str, Any]]
    ):
        """设置缓存"""
        query_hash = self._generate_hash(query, agent_id, max_results)
        
        vector_ids = [r["id"] for r in results]
        scores = [r.get("similarity", 0) for r in results]
        
        # 使用数据库的缓存插入方法
        self.db.insert_cache(
            query_hash=query_hash,
            query_text=query,
            vector_ids=vector_ids,
            scores=scores,
            ttl_seconds=self.ttl_seconds
        )
    
    def clear_expired(self):
        """清除过期缓存"""
        if self.db:
            self.db.clear_expired_cache()


class HNSWLikeVectorSearcher(BaseVectorSearcher):
    """
    HNSW-like 向量搜索
    
    基于分层的类HNSW算法实现，用于高效的向量搜索
    - 支持增量索引更新
    - 支持多层索引结构
    - 支持近似最近邻搜索
    """
    
    def __init__(self, memory_manager, max_layers: int = 3, ef_construction: int = 100, m: int = 16):
        super().__init__(memory_manager)
        # HNSW 参数
        self.max_layers = max_layers  # 最大层数
        self.ef_construction = ef_construction  # 构建时的动态列表大小
        self.m = m  # 每一层连接数
        
        # 索引结构
        self._graph: Dict[int, Dict[int, List[int]]] = {}  # 邻近图
        self._vectors: Dict[int, List[float]] = {}  # 向量存储
        self._memory_ids: Dict[int, int] = {}  # 索引ID到记忆ID的映射
        self._memory_id_to_idx: Dict[int, int] = {}  # 记忆ID到索引ID的映射
        
        # 层次信息
        self._levels: Dict[int, int] = {}  # 每个节点的层数
        self._entry_point: int = None  # 入口点
        
        # 索引状态
        self._last_index_time = 0
        self._index_interval = 5  # 索引更新间隔（秒）
        self._index_version = 0  # 索引版本，用于增量更新
        
    def is_available(self) -> bool:
        """检查是否可用"""
        return self.db is not None
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        import re
        tokens = re.findall(r'\w+', text.lower())
        return [t for t in tokens if len(t) > 1]
    
    def _get_random_level(self) -> int:
        """生成随机层数（指数衰减概率）"""
        level = 0
        while random.random() < 0.5 and level < self.max_layers - 1:
            level += 1
        return level
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _build_vector(self, tokens: List[str], idf: Dict[str, float]) -> List[float]:
        """构建向量"""
        vector = []
        for token in tokens:
            tf = 1.0 / len(tokens) if tokens else 0
            tfidf = tf * idf.get(token, 0)
            vector.append(tfidf)
        return vector
    
    def _search_layer(self, query_vec: List[float], entry_point: int, layer: int, ef: int) -> List[Tuple[int, float]]:
        """在单层搜索"""
        visited = {entry_point}
        candidates = [(0, entry_point)]
        results = []
        
        while candidates:
            score, current = heapq.heappop(candidates)
            
            if len(results) >= ef:
                break
            
            if current not in self._graph:
                continue
            
            neighbors = self._graph.get(current, {}).get(layer, [])
            
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    
                    if neighbor not in self._vectors:
                        continue
                    
                    neighbor_vec = self._vectors[neighbor]
                    score = self._cosine_similarity(query_vec, neighbor_vec)
                    
                    if len(results) < ef or score > results[0][0]:
                        heapq.heappush(results, (score, neighbor))
                        heapq.heappush(candidates, (-score, neighbor))
        
        # 返回按分数排序的结果
        results.sort(key=lambda x: x[0], reverse=True)
        return [(idx, score) for score, idx in results[:ef]]
    
    def _insert_element(self, memory_id: int, vector: List[float]):
        """插入元素到索引"""
        idx = len(self._vectors)
        self._vectors[idx] = vector
        self._memory_ids[idx] = memory_id
        self._memory_id_to_idx[memory_id] = idx
        
        level = self._get_random_level()
        self._levels[idx] = level
        
        if self._entry_point is None:
            self._entry_point = idx
            self._graph[idx] = {l: [] for l in range(level + 1)}
            return
        
        # 找到所有层级的插入点
        for layer in range(level, -1, -1):
            search_results = self._search_layer(vector, self._entry_point, layer, self.ef_construction)
            
            if not search_results:
                continue
            
            neighbors = [idx for idx, _ in search_results[:self.m]]
            
            if idx not in self._graph:
                self._graph[idx] = {l: [] for l in range(level + 1)}
            
            # 更新连接
            for neighbor in neighbors:
                if neighbor not in self._graph:
                    self._graph[neighbor] = {l: [] for l in range(self._levels.get(neighbor, 0) + 1)}
                
                for l in range(layer + 1):
                    if l not in self._graph[idx]:
                        self._graph[idx][l] = []
                    if l not in self._graph[neighbor]:
                        self._graph[neighbor][l] = []
                    
                    if idx not in self._graph[neighbor][l]:
                        self._graph[neighbor][l].append(idx)
                    if neighbor not in self._graph[idx][l]:
                        self._graph[idx][l].append(neighbor)
    
    def _build_index(self, memories: List[Dict[str, Any]]):
        """构建HNSW索引"""
        if not memories:
            return
        
        # 提取token并计算IDF
        import re
        all_tokens = []
        token_docs = []
        
        for memory in memories:
            tokens = self._tokenize(memory["content"])
            all_tokens.extend(tokens)
            token_docs.append(set(tokens))
        
        # 计算IDF
        N = len(memories)
        idf = {}
        for token in set(all_tokens):
            doc_count = sum(1 for doc in token_docs if token in doc)
            idf[token] = max(1.0, (N - doc_count + 1) / (doc_count + 1))
        
        # 构建向量并插入
        for memory in memories:
            tokens = self._tokenize(memory["content"])
            vector = self._build_vector(tokens, idf)
            
            if memory.get("id") is not None:
                self._insert_element(memory["id"], vector)
        
        self._index_version += 1
    
    def _incremental_index_update(self, new_memories: List[Dict[str, Any]]):
        """增量更新索引"""
        if not new_memories:
            return
        
        import re
        all_tokens = []
        token_docs = []
        existing_ids = set(self._memory_id_to_idx.keys())
        
        for memory in new_memories:
            memory_id = memory.get("id")
            if memory_id and memory_id in existing_ids:
                continue
            
            tokens = self._tokenize(memory["content"])
            all_tokens.extend(tokens)
            token_docs.append(set(tokens))
        
        if not all_tokens:
            return
        
        N = len(self._vectors) + len(new_memories)
        idf = {}
        for token in set(all_tokens):
            doc_count = sum(1 for doc in token_docs if token in doc)
            idf[token] = max(1.0, (N - doc_count + 1) / (doc_count + 1))
        
        for memory in new_memories:
            memory_id = memory.get("id")
            if memory_id and memory_id not in existing_ids:
                tokens = self._tokenize(memory["content"])
                vector = self._build_vector(tokens, idf)
                self._insert_element(memory_id, vector)
        
        self._index_version += 1
    
    async def search(
        self,
        query: str,
        max_results: int = 5,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        include_frozen: bool = False
    ) -> List[Dict[str, Any]]:
        """HNSW-like 搜索"""
        if not agent_id:
            agent_id = self.memory_manager.agent_id
        
        # 获取记忆
        memories = self._get_agent_memories(agent_id, include_frozen, session_id)
        
        if not memories:
            return []
        
        # 检查是否需要更新索引
        import time
        current_time = time.time()
        
        if not self._vectors or current_time - self._last_index_time > self._index_interval:
            # 全量构建
            self._build_index(memories)
            self._last_index_time = current_time
        else:
            # 增量更新
            existing_ids = set(self._memory_id_to_idx.keys())
            new_memories = [m for m in memories if m.get("id") not in existing_ids]
            if new_memories:
                self._incremental_index_update(new_memories)
                self._last_index_time = current_time
        
        # 构建查询向量
        tokens = self._tokenize(query)
        all_tokens = []
        for memory in memories:
            all_tokens.extend(self._tokenize(memory["content"]))
        
        N = len(memories) + 1
        idf = {}
        for token in set(all_tokens):
            doc_count = sum(1 for m in memories if token in self._tokenize(m["content"]))
            idf[token] = max(1.0, (N - doc_count + 1) / (doc_count + 1))
        
        query_vec = self._build_vector(tokens, idf)
        
        if self._entry_point is None:
            return []
        
        # 分层搜索
        current = self._entry_point
        for layer in range(self.max_layers - 1, -1, -1):
            if current is not None:
                candidates = self._search_layer(query_vec, current, layer, self.ef_construction)
                if candidates:
                    current = candidates[0][0]
        
        # 最终搜索
        final_results = self._search_layer(query_vec, self._entry_point, 0, max_results)
        
        # 返回结果
        results = []
        memory_map = {m.get("id"): m for m in memories}
        
        for idx, score in final_results[:max_results]:
            memory_id = self._memory_ids.get(idx)
            if memory_id and memory_id in memory_map:
                memory = memory_map[memory_id].copy()
                memory["similarity"] = score
                results.append(memory)
        
        # 更新搜索统计
        if results:
            memory_ids = [r["id"] for r in results]
            scores = [r.get("similarity", 0) for r in results]
            self.db.batch_update_memory_search(memory_ids, scores)
        
        return results


class VectorSearcher:
    """
    向量搜索引擎
    
    统一的向量搜索接口
    """
    
    def __init__(
        self,
        memory_manager,
        backend: str = "tfidf",
        cache_enabled: bool = True,
        cache_ttl: int = 3600
    ):
        """
        初始化向量搜索
        
        Args:
            memory_manager: 记忆管理器
            backend: 搜索后端 (tfidf, hnsw-like)
            cache_enabled: 是否启用缓存
            cache_ttl: 缓存 TTL（秒）
        """
        self.memory_manager = memory_manager
        self.backend = backend
        self.cache_enabled = cache_enabled
        
        # 选择后端
        if backend == "hnsw-like":
            self._searcher = HNSWLikeVectorSearcher(memory_manager)
        elif backend == "tfidf":
            self._searcher = TFIDFVectorSearcher(memory_manager)
        else:
            # 默认使用TF-IDF
            self._searcher = TFIDFVectorSearcher(memory_manager)
        
        # 初始化缓存
        if cache_enabled and memory_manager.db:
            self._cache = VectorCache(memory_manager.db, cache_ttl)
        else:
            self._cache = None
    
    def is_available(self) -> bool:
        """检查是否可用"""
        return self._searcher.is_available()
    
    async def search(
        self,
        query: str,
        max_results: int = 5,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        include_frozen: bool = False,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        搜索记忆
        
        Args:
            query: 查询文本
            max_results: 最大结果数
            agent_id: Agent ID
            session_id: 会话ID，用于过滤特定会话的记忆
            include_frozen: 是否包含冷藏记忆
            use_cache: 是否使用缓存
            
        Returns:
            记忆列表
        """
        if not agent_id:
            agent_id = self.memory_manager.agent_id
        
        # 尝试从缓存获取
        if use_cache and self._cache:
            cached = self._cache.get(query, agent_id, max_results)
            if cached:
                # 从缓存获取记忆详情
                results = []
                for memory_id, similarity in cached:
                    memory = self.memory_manager.db.get_memory_by_id(memory_id)
                    if memory:
                        memory["similarity"] = similarity
                        results.append(memory)
                return results
        
        # 执行搜索
        results = await self._searcher.search(
            query=query,
            max_results=max_results,
            agent_id=agent_id,
            session_id=session_id,
            include_frozen=include_frozen
        )
        
        # 缓存结果
        if use_cache and self._cache and results:
            self._cache.set(query, agent_id, max_results, results)
        
        return results
    
    def clear_cache(self):
        """清除缓存"""
        if self._cache:
            self._cache.clear_expired()
