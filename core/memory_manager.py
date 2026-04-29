import chromadb
import uuid
import time
import numpy as np
from typing import List, Dict, Tuple, Optional
import os
from pathlib import Path
from configs.static_config import get_normalization_config

# 持久化存储根路径
DB_ROOT_PATH = Path(__file__).parent.parent / "chroma_db"


class MemoryManager:
    """
    H-RAG 记忆中枢 (Phase 3.5: Dynamic Manifold Search)
    功能：
    1. 7D 向量检索 (Temp, Occ, Price, PMV, Trend_T, Trend_Occ, Trend_P)
    2. 基于配置的 Min-Max 归一化。
    3. 预冷死锁解锁机制。
    """

    def __init__(self, case_name, collection_name="hvac_memories"):
        self.case_db_path = DB_ROOT_PATH / case_name
        self.case_db_path.mkdir(parents=True, exist_ok=True)
        print(f"🧠 [Memory] Initializing Dynamic DB for '{case_name}' at: {self.case_db_path}")

        self.client = chromadb.PersistentClient(path=str(self.case_db_path))
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.norm_cfg = get_normalization_config()

    def add_memory(self, doc_text: str, metadata: Dict, context_state: Dict):
        mem_id = str(uuid.uuid4())

        full_metadata = metadata.copy()
        # 存入所有物理特征用于检索过滤
        full_metadata.update({
            "meta_outdoor_temp": float(context_state.get('outdoor_temp', 0.0)),
            "meta_occupancy": float(context_state.get('occupancy', 0.0)),
            "meta_price": float(context_state.get('price', 0.0)),
            "meta_avg_pmv": float(context_state.get('avg_pmv', 0.0)),
            "meta_temp_trend": float(context_state.get('temp_trend', 0.0)),
            "meta_occ_trend": float(context_state.get('occ_trend', 0.0)),
            "meta_price_trend": float(context_state.get('price_trend', 0.0)),
            "meta_clo": float(context_state.get('clo', 0.5))
        })

        self.collection.add(
            documents=[doc_text],
            metadatas=[full_metadata],
            ids=[mem_id]
        )

    def _normalize_val(self, val, key):
        """通用归一化函数"""
        min_v, max_v = self.norm_cfg.get(key, (0, 1))
        # Clip
        val = max(min_v, min(max_v, val))
        return (val - min_v) / (max_v - min_v) if max_v > min_v else 0.0

    def _get_state_vector(self, ctx: Dict, max_occ: float):
        """
        构造 7 维归一化向量
        """
        # 1. 基础维度
        n_temp = self._normalize_val(ctx.get('outdoor_temp', 0), 'temp')
        n_occ = float(ctx.get('occupancy', 0)) / max_occ if max_occ > 0 else 0.0
        n_price = self._normalize_val(ctx.get('price', 0), 'price')
        n_pmv = self._normalize_val(ctx.get('avg_pmv', 0), 'pmv')

        if 'clo' in self.norm_cfg:
            n_clo = self._normalize_val(ctx.get('clo', 0.5), 'clo')
        else:
            raw_clo = ctx.get('clo', 0.5)
            n_clo = (raw_clo - 0.3) / (1.5 - 0.3)  # Hardcoded fallback
            n_clo = max(0.0, min(1.0, n_clo))

        # 2. 趋势维度
        n_dT = self._normalize_val(ctx.get('temp_trend', 0), 'temp_trend')
        n_dP = self._normalize_val(ctx.get('price_trend', 0), 'price_trend')

        # Occ Trend 特殊处理: -1, 0, 1。无需太复杂归一化，直接用
        n_dOcc = ctx.get('occ_trend', 0.0)

        return np.array([n_temp, n_occ, n_price, n_pmv, n_dT, n_dOcc, n_dP])

    def _normalize_rewards(self, rewards: List[float]) -> List[float]:
        if not rewards: return []
        arr = np.array(rewards)
        min_r, max_r = arr.min(), arr.max()
        if max_r == min_r: return [1.0] * len(rewards)
        return ((arr - min_r) / (max_r - min_r)).tolist()

    def retrieve_contrastive(self, query_text: str, zone_id: str, current_context: Dict, max_occupancy: float,
                             n_results=5, distance_threshold=1.5) -> Dict[str, List[str]]:
        """
        物理感知对比检索 (趋势增强版)
        """
        target_vec = self._get_state_vector(current_context, max_occupancy)

        # 1. 数据库粗筛 (Pre-filtering)
        curr_occ = current_context.get('occupancy', 0)
        curr_occ_trend = current_context.get('occ_trend', 0)

        # 构造 Where Clause
        conditions = [{"zone_id": {"$eq": zone_id}}]

        # [CRITICAL] 预冷死锁解锁机制
        # 如果当前是"预冷时刻" (Occ=0但趋势=+1)，强制搜索历史中同样的预冷时刻
        if curr_occ == 0 and curr_occ_trend > 0:
            conditions.append({"meta_occ_trend": {"$gt": 0}})
        else:
            # 常规逻辑: 有人配有人，无人配无人
            is_occupied = curr_occ > 0
            conditions.append({"meta_occupancy": {"$gt": 0} if is_occupied else {"$eq": 0}})

        where_clause = {"$and": conditions}

        results = self.collection.get(
            where=where_clause,
            include=['documents', 'metadatas']
        )

        metas = results['metadatas']
        docs = results['documents']

        if not metas:
            return {"positive": [], "negative": []}

        # 2. 计算 7D 物理距离
        candidates = []
        for i in range(len(metas)):
            m = metas[i]
            # 还原 Memory 的 Context 字典
            mem_ctx = {
                'outdoor_temp': m.get('meta_outdoor_temp'),
                'occupancy': m.get('meta_occupancy'),
                'price': m.get('meta_price'),
                'avg_pmv': m.get('meta_avg_pmv'),
                'temp_trend': m.get('meta_temp_trend'),
                'occ_trend': m.get('meta_occ_trend'),
                'price_trend': m.get('meta_price_trend'),
                'clo': m.get('meta_clo', 0.5)
            }
            mem_vec = self._get_state_vector(mem_ctx, max_occupancy)

            dist = np.linalg.norm(target_vec - mem_vec)


            candidates.append({
                "doc": docs[i],
                "meta": m,
                "dist": dist,
                "reward": float(m.get('reward', -9999.0))
            })

        # 3. 确定局部邻域
        candidates.sort(key=lambda x: x['dist'])
        if not candidates or candidates[0]['dist'] > distance_threshold:
            print(
                f"⚠️ [RAG] New Scenario Detected for {zone_id}! Min Dist: {candidates[0]['dist']:.2f} > {distance_threshold}. Skipping retrieval to avoid hallucination.")
            return {"positive": [], "negative": []}
        neighborhood_size = min(len(candidates), 15)
        local_neighborhood = candidates[:neighborhood_size]

        local_neighborhood.sort(key=lambda x: x['reward'], reverse=True)

        # 提取 Positive (Reward 最高)
        positives = []
        for item in local_neighborhood:
            mem_occ = item['meta'].get('meta_occupancy', 0)
            mem_pmv = item['meta'].get('meta_avg_pmv', 0.0)
            mem_max_pmv = item['meta'].get('meta_max_pmv', 0.0)  # [NEW] Check Peak

            # 红线过滤：虽然分高，但如果过热，坚决不学
            if mem_occ > 0 and mem_max_pmv > 0.5:
                continue

            positives.append(item['doc'])
            if len(positives) >= 2: break  # 取前2个最好的

        # 提取 Negative (Reward 最低)
        negatives = []
        # 反转列表找最差的 (在已经是物理近邻的子集中找)
        worst_candidates = sorted(local_neighborhood, key=lambda x: x['reward'])

        for item in worst_candidates:
            # 只有当 Reward 真的比较差时才作为反面教材
            # 防止把 "还可以" 的策略当成垃圾
            if item['reward'] < -2.0:
                negatives.append(item['doc'])
                if len(negatives) >= 2: break

        return {
            "positive": positives,
            "negative": negatives
        }

    def prune_old_memories(self, retention_seconds: int = 7 * 24 * 3600):
        cutoff_time = time.time() - retention_seconds
        try:
            self.collection.delete(where={"timestamp": {"$lt": cutoff_time}})
            print(f"🧹 [Memory] Pruned old memories.")
        except Exception as e:
            print(f"⚠️ [Memory] Pruning skipped: {e}")

    def count(self):
        return self.collection.count()