import os
import json
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

class JarvisMemory:
    def __init__(self):
        # 檢查是否已經初始化，避免 Streamlit Rerun 重複初始化報錯
        try:
            firebase_admin.get_app()
        except ValueError:
            # -------------------------------------------------------
            # 1. 優先嘗試從 Streamlit Secrets 讀取 (雲端模式專用)
            # -------------------------------------------------------
            if "FIREBASE_SERVICE_ACCOUNT" in st.secrets:
                # Streamlit 會自動把 TOML 裡的 [Section] 解析為字典
                service_account_info = dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
                
                # 🔧 關鍵修復：處理私鑰中的換行符號
                if "private_key" in service_account_info:
                    service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
                
                cred = credentials.Certificate(service_account_info)
                firebase_admin.initialize_app(cred)
                
            # -------------------------------------------------------
            # 2. 嘗試從環境變數讀取 (本地開發/Docker 模式)
            # -------------------------------------------------------
            elif os.getenv("FIREBASE_SERVICE_ACCOUNT"):
                service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")
                try:
                    # 嘗試解析 JSON 字串
                    cred_dict = json.loads(service_account_json)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                except json.JSONDecodeError:
                    # 如果不是 JSON，可能是檔案路徑
                    cred = credentials.Certificate(service_account_json)
                    firebase_admin.initialize_app(cred)
            else:
                # 都找不到才報錯
                raise ValueError("❌ 錯誤：找不到 FIREBASE_SERVICE_ACCOUNT 配置。\n請檢查 Streamlit Secrets 或環境變數。")

        # 連接數據庫
        self.db = firestore.client()

    def add_memory(self, content, category="observation"):
        """寫入記憶"""
        try:
            doc_ref = self.db.collection("jarvis_memories").document()
            doc_ref.set({
                "content": content,
                "category": category,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            return doc_ref.id
        except Exception as e:
            print(f"寫入記憶失敗: {e}")
            return None

    def get_recent_memories(self, limit=5):
        """讀取記憶"""
        try:
            docs = self.db.collection("jarvis_memories")\
                .order_by("timestamp", direction=firestore.Query.DESCENDING)\
                .limit(limit)\
                .stream()
            return [doc.to_dict().get('content', '') for doc in docs]
        except Exception as e:
            print(f"讀取記憶失敗: {e}")
            return []
    
    def search_memories(self, query, context=None, limit=5):
        """搜索相關記憶"""
        try:
            # 這裡暫時使用簡單查詢，未來升級為向量搜索
            query_ref = self.db.collection("jarvis_memories").order_by("timestamp", direction=firestore.Query.DESCENDING)
            
            if context:
                query_ref = query_ref.where("category", "==", context)
            
            query_ref = query_ref.limit(limit * 2)
            
            results = []
            for doc in query_ref.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                content = data.get('content', '')
                # 簡單關鍵字過濾
                if query.lower() in content.lower():
                    results.append(data)
                    if len(results) >= limit:
                        break
            return results
        except Exception as e:
            print(f"搜索記憶失敗: {e}")
            return []
