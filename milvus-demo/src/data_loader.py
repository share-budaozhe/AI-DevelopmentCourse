"""
═══════════════════════════════════════════════════════════════
  📊 Milvus 学习教程 — src/data_loader.py
  示例数据生成器

  提供多种场景的模拟向量数据，用于演示 Milvus 各功能。
═══════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import numpy as np
import random
from typing import List


# ═══════════════════════════════════════════════════════════════
# 数据模型定义
# ═══════════════════════════════════════════════════════════════

PRODUCT_CATEGORIES = ["电子产品", "图书", "服装", "食品", "家居", "运动"]

PRODUCT_NAMES = {
    "电子产品": ["智能手机", "笔记本电脑", "平板电脑", "蓝牙耳机", "智能手表", "相机", "键盘", "显示器"],
    "图书": ["Python 编程", "深度学习", "机器学习实战", "算法导论", "数据结构", "操作系统", "计算机网络"],
    "服装": ["T恤", "牛仔裤", "连衣裙", "运动鞋", "羽绒服", "帽子", "围巾", "手套"],
    "食品": ["巧克力", "坚果", "茶叶", "咖啡", "饼干", "蜂蜜", "干果", "方便面"],
    "家居": ["台灯", "抱枕", "地毯", "花瓶", "挂钟", "收纳盒", "相框", "香薰"],
    "运动": ["瑜伽垫", "哑铃", "跳绳", "篮球", "足球", "泳镜", "手套", "护膝"],
}


def generate_product_vectors(num: int = 1000, dim: int = 128) -> list[dict]:
    """🏪 生成电商商品向量数据。

    模拟：每个商品被表示为 128 维向量，同类商品向量相近。

    Args:
        num: 商品数量
        dim: 向量维度

    Returns:
        [{"id": int, "vector": ndarray, "name": str, "category": str,
          "price": float, "rating": float, "stock": int}, ...]
    """
    np.random.seed(42)
    random.seed(42)

    # 为每个类��生成一个"中心向量"
    category_centers = {}
    for cat in PRODUCT_CATEGORIES:
        category_centers[cat] = np.random.randn(dim).astype(np.float32)
        category_centers[cat] /= np.linalg.norm(category_centers[cat])

    data = []
    for i in range(num):
        cat = random.choice(PRODUCT_CATEGORIES)
        name = random.choice(PRODUCT_NAMES[cat])

        # 向量 = 类别中心 + 随机噪声（同类商品向量接近）
        center = category_centers[cat]
        noise = np.random.randn(dim).astype(np.float32) * 0.3
        vec = center + noise
        vec /= np.linalg.norm(vec)

        data.append({
            "id": i + 1,
            "vector": vec,
            "name": name,
            "category": cat,
            "price": round(random.uniform(9.9, 999.9), 2),
            "rating": round(random.uniform(1.0, 5.0), 1),
            "stock": random.randint(0, 500),
        })

    return data


def generate_text_vectors(num: int = 500, dim: int = 256) -> list[dict]:
    """📄 生成文本文档向量数据。

    模拟：文档嵌入向量，附带元数据。

    Args:
        num: 文档数量
        dim: 向量维度

    Returns:
        [{"id": int, "vector": ndarray, "title": str,
          "tags": list[str], "length": int}, ...]
    """
    np.random.seed(123)
    random.seed(123)

    topics = ["AI", "Python", "数据库", "前端", "DevOps", "安全"]
    tags_pool = {
        "AI": ["机器学习", "深度学习", "NLP", "CV", "强化学习", "Transformer"],
        "Python": ["Django", "Flask", "异步", "类型提示", "性能优化"],
        "数据库": ["MySQL", "Redis", "MongoDB", "PostgreSQL", "向量数据库"],
        "前端": ["React", "Vue", "CSS", "TypeScript", "Webpack"],
        "DevOps": ["Docker", "K8s", "CI/CD", "监控", "日志"],
        "安全": ["加密", "认证", "防火墙", "渗透测试", "零信任"],
    }

    data = []
    for i in range(num):
        topic = random.choice(topics)
        tags = random.sample(tags_pool[topic], random.randint(1, 3))
        vec = np.random.randn(dim).astype(np.float32)
        vec /= np.linalg.norm(vec)

        data.append({
            "id": i + 1,
            "vector": vec,
            "title": f"{topic} 文档 #{i+1:04d}",
            "topic": topic,
            "tags": tags,
            "length": random.randint(500, 10000),
        })

    return data


def generate_face_vectors(num: int = 300, dim: int = 512) -> list[dict]:
    """👤 生成人脸特征向量数据。

    模拟：人脸识别场景，每张人脸有向量特征 + 人员信息。

    Args:
        num: 人脸数量
        dim: 特征维度

    Returns:
        [{"id": str, "vector": ndarray, "person_id": str,
          "name": str, "department": str}, ...]
    """
    np.random.seed(99)
    random.seed(99)

    departments = ["技术部", "产品部", "设计部", "市场部", "HR"]
    people = [
        ("张三", "技术部"), ("李四", "产品部"), ("王五", "设计部"),
        ("赵六", "市场部"), ("钱七", "HR"), ("孙八", "技术部"),
        ("周九", "技术部"), ("吴十", "产品部"), ("郑一", "设计部"),
        ("陈二", "市场部"),
    ]

    # 为每个真人生成一个中心向量
    person_centers = {}
    for name, dept in people:
        person_id = f"P{hash(name) % 10000:04d}"
        center = np.random.randn(dim).astype(np.float32)
        center /= np.linalg.norm(center)
        person_centers[person_id] = {"center": center, "name": name, "dept": dept}

    data = []
    person_ids = list(person_centers.keys())
    for i in range(num):
        pid = random.choice(person_ids)
        info = person_centers[pid]
        # 同一人的多张"照片"（同一中心 + 噪声）
        noise = np.random.randn(dim).astype(np.float32) * 0.2
        vec = info["center"] + noise
        vec /= np.linalg.norm(vec)

        data.append({
            "id": f"face_{i+1:04d}",
            "vector": vec,
            "person_id": pid,
            "name": info["name"],
            "department": info["dept"],
        })

    return data


# ═══════════════════════════════════════════════════════════════
# 批量插入辅助
# ═══════════════════════════════════════════════════════════════

def insert_batch(collection, data: list[dict], batch_size: int = 100):
    """分批插入数据到 Milvus Collection。

    Args:
        collection: Milvus Collection 对象
        data: 数据列表
        batch_size: 每批大小

    Returns:
        插入的总行数
    """
    from pymilvus import Collection

    total = 0
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        ids = [d["id"] for d in batch]
        vectors = [d["vector"].tolist() for d in batch]

        # 构建插入数据（提取除 id 和 vector 外的所有字段）
        insert_data = [ids, vectors]
        # 其他标量字段
        first = batch[0]
        scalar_keys = [k for k in first if k not in ("id", "vector")]
        for key in scalar_keys:
            values = [d[key] for d in batch]
            # Milvus 对 list 字段需要特殊处理
            if isinstance(values[0], list):
                continue  # 跳过复杂字段，简化演示
            insert_data.append(values)

        collection.insert(insert_data)
        total += len(batch)

    collection.flush()
    return total


if __name__ == "__main__":
    # 快速测试数据生成
    products = generate_product_vectors(5)
    for p in products:
        print(f"  [{p['id']}] {p['name']} | {p['category']} | ￥{p['price']} | ⭐{p['rating']}")
    print(f"\n  共生成 {len(products)} 条商品数据（演示用）")
