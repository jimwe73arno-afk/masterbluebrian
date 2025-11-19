import os
import json
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

class JarvisMemory:
    def __init__(self):
        # 防止 Streamlit 重跑時重複初始化
        if not firebase_admin._apps:
            try:
                cred = self._get_cred()
                firebase_admin.initialize_app(cred)
            except Exception as e:
                st.error(f"🔥 決策大腦啟動失敗 (Firebase Error): {str(e)}")
                st.stop()

        self.db = firestore.client()

    def _get_cred(self):
        """自動取得憑證並清洗格式"""
        # 優先：Streamlit Cloud Secrets
        if "FIREBASE_SERVICE_ACCOUNT" in st.secrets:
            # 轉成普通字典
            info = dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
            
            # 關鍵修復：把 '\\n' 字串強制轉回真正的換行符號
            if "private_key" in info:
                raw_key = info["private_key"]
                # 移除可能多餘的引號
                raw_key = raw_key.strip().strip('"').strip("'")
                # 替換換行符號
                info["private_key"] = raw_key.replace("\\n", "\n")
            
            return credentials.Certificate(info)

        # 備用：本機環境變數
        env_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")
        if env_json:
            try:
                return credentials.Certificate(json.loads(env_json))
            except:
                return credentials.Certificate(env_json)

        raise ValueError("未設定 FIREBASE_SERVICE_ACCOUNT")

    def add_memory(self, content, category="observation"):
        try:
            self.db.collection("jarvis_memories").add({
                "content": content,
                "category": category,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
        except:
            pass # 暫時忽略寫入錯誤，保證對話流暢

    def get_recent_memories(self, limit=5):
        return [] # 暫時回傳空，確保 v0.1 先能動
    
    def search_memories(self, query, context=None, limit=5):
        return [] # 暫時回傳空
