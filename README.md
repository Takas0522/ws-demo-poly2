# ws-demo-poly2

ユーザー管理サービスリポジトリ

## 概要

このリポジトリには、CRUD操作とテナント分離を備えたユーザー管理サービスが含まれています。

## サービス

### User Management Service

パス: `src/user-management-service`

マルチテナント環境でのユーザー管理機能を提供するPython FastAPIベースのサービスです。

詳細は [src/user-management-service/README.md](src/user-management-service/README.md) を参照してください。

## クイックスタート

```bash
cd src/user-management-service
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## ドキュメント

- API Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 依存関係

- Takas0522/ws-demo-poly3#1 (JWT認証サービス)
- Takas0522/ws-demo-poly-integration#6 (共有型ライブラリ)
- Takas0522/ws-demo-poly-integration#4 (CosmosDBスキーマ)