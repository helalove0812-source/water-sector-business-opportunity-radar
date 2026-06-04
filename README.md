# Water Sector Business Opportunity Radar

FastAPI MVP bootstrap for the Water Sector Business Opportunity Radar project.

## 本地运行

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/python scripts/seed_data.py
PYTHONPATH=. .venv/bin/uvicorn app.main:app --reload
```

默认管理员账号：

- 用户名：`admin`
- 密码：`admin123`

## MVP 功能

- 登录后台
- 关键词管理
- 手动采集
- 商机评分
- 商机列表
- 商机详情
- 跟进备注

## 测试

```bash
PYTHONPATH=. .venv/bin/pytest -v
```
