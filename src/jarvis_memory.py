import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from datetime import datetime

class JarvisMemory:
    def __init__(self):
        """初始化 Firebase"""
        if not firebase_admin._apps:
            try:
                import streamlit as st
                firebase_json = st.secrets.get("FIREBASE_SERVICE_ACCOUNT")
                if isinstance(firebase_json, dict):
                    cred_dict = firebase_json
                else:
                    cred_dict = json.loads(firebase_json)
            except:
                firebase_json = os.getenv('FIREBASE_SERVICE_ACCOUNT')
                if not firebase_json:
                    raise ValueError("需要设置 FIREBASE_SERVICE_ACCOUNT")
                cred_dict = json.loads(firebase_json)
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
        self.collection = self.db.collection('memories')
    
    def add_memory(self, context="", insight="", plan="", risk="", tags="", source="manual"):
        """添加新记忆"""
        memory_data = {
            'context': context,
            'insight': insight,
            'plan': plan,
            'risk': risk,
            'tags': tags,
            'source': source,
            'timestamp': datetime.now().isoformat(),
            'created_at': firestore.SERVER_TIMESTAMP
        }
        
        doc_ref = self.collection.add(memory_data)
        return doc_ref[1].id
    
    def search_memories(self, query, limit=5):
        """搜索记忆"""
        results = []
        
        # 简单的关键词搜索
        all_memories = self.collection.order_by('created_at', direction=firestore.Query.DESCENDING).limit(100).stream()
        
        for doc in all_memories:
            data = doc.to_dict()
            # 检查查询词是否在各个字段中
            if (query.lower() in data.get('context', '').lower() or
                query.lower() in data.get('insight', '').lower() or
                query.lower() in data.get('plan', '').lower() or
                query.lower() in data.get('tags', '').lower()):
                
                data['id'] = doc.id
                results.append(data)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_all_memories(self, limit=50):
        """获取所有记忆"""
        memories = []
        docs = self.collection.order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit).stream()
        
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            memories.append(data)
        
        return memories
