# 🚀 Milvus 安装部署指南

## 方案 1：Milvus Lite（推荐学习）

**零配置、秒级启动。数据存储在本地文件。**

```bash
pip install milvus-lite
```

已集成在 `requirements.txt` 中，安装依赖即可使用。

**连接代码**：
```python
from pymilvus import connections
connections.connect(alias="default", uri="./milvus_data.db")
```

**限制**：
- 仅支持单进程，不能并发写入
- 不支持分布式
- 仅供开发测试，不能用于生产

---

## 方案 2：Milvus Standalone（Docker）

**适合项目开发和中小规模生产。**

```bash
# 启动
docker-compose up -d

# 检查状态
docker-compose ps

# 停止
docker-compose down
```

**连接代码**：
```python
from pymilvus import connections
connections.connect(alias="default", host="localhost", port="19530")
```

**系统要求**：
- Docker & Docker Compose
- 内存 >= 8GB
- 磁盘 >= 10GB（SSD 推荐）

---

## 方案 3：Zilliz Cloud（生产推荐）

**全托管服务，免运维。**

1. 注册 https://cloud.zilliz.com
2. 创建 Cluster（有免费额度）
3. 获取 URI 和 API Token

**连接代码**：
```python
from pymilvus import connections
connections.connect(
    alias="default",
    uri="https://xxx.api.zillizcloud.com",
    token="your-token",
)
```

---

## 验证安装

```python
from pymilvus import connections, utility

connections.connect(alias="default", uri="./test.db")
print(utility.list_collections())  # 应该返回 []
connections.disconnect("default")
```

## 常见问题

### Q: Milvus Lite 报错 "no such module: milvus_lite"？
先 `pip uninstall milvus-lite` 再 `pip install milvus-lite`。

### Q: Docker 启动失败？
检查端口 19530 是否被占用：`netstat -ano | findstr 19530`

### Q: 数据存在哪里？
- Milvus Lite：`milvus_data.db`（项目根目录）
- Docker：`volumes/` 目录（Docker volume）
