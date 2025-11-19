"""
種子記憶導入工具 v2.0
用途：將 seed_memories 中的核心記憶批量導入到 Firebase Firestore
支援兩種格式：
1. 決策框架格式 (insight + plan + risk)
2. 戰略記憶格式 (content + category)
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 導入記憶管理模組和種子資料
try:
    from jarvis_memory import JarvisMemory
    from seed_memories import SEED_MEMORIES
except ImportError as e:
    print(f"❌ 導入失敗: {e}")
    print("請確保在正確的目錄執行此腳本")
    sys.exit(1)


def format_memory_content(seed):
    """
    根據記憶格式組合內容
    支援兩種格式：
    1. insight + plan + risk (決策框架)
    2. content (戰略記憶)
    """
    
    # 格式 1：決策框架格式
    if 'insight' in seed:
        content = f"""
【洞察】{seed['insight']}

【計劃】{seed['plan']}

【風險】{seed['risk']}

【來源】{seed.get('source', 'seed')}
        """.strip()
        category = seed.get('context', 'general')
    
    # 格式 2：戰略記憶格式
    elif 'content' in seed:
        content = seed['content']
        category = seed.get('category', 'general')
    
    else:
        raise ValueError(f"未知的記憶格式: {seed}")
    
    return content, category


def load_seed_memories():
    """載入種子記憶到 Firebase"""
    
    print("=" * 60)
    print("🌱 BrotherG Jarvis - 種子記憶導入工具 v2.0")
    print("=" * 60)
    print()
    
    # 初始化記憶庫
    print("📡 正在連接 Firebase...")
    try:
        memory = JarvisMemory()
        print("✅ Firebase 連接成功！")
    except Exception as e:
        print(f"❌ Firebase 連接失敗: {e}")
        print()
        print("請檢查：")
        print("1. .env 檔案是否存在並包含 FIREBASE_SERVICE_ACCOUNT")
        print("2. Firebase 專案是否已建立")
        print("3. Firestore 是否已啟用")
        sys.exit(1)
    
    print()
    print(f"📦 準備導入 {len(SEED_MEMORIES)} 條種子記憶...")
    print()
    
    # 統計資料
    success_count = 0
    fail_count = 0
    context_stats = {}
    format_stats = {"framework": 0, "strategic": 0}
    
    # 逐條導入
    for i, seed in enumerate(SEED_MEMORIES, 1):
        try:
            # 格式化記憶內容
            content, category = format_memory_content(seed)
            
            # 判斷格式類型
            format_type = "framework" if 'insight' in seed else "strategic"
            format_stats[format_type] += 1
            
            # 添加到 Firestore
            memory.add_memory(
                content=content,
                category=category
            )
            
            # 統計
            success_count += 1
            context_stats[category] = context_stats.get(category, 0) + 1
            
            # 顯示進度
            preview = seed.get('insight', seed.get('content', ''))[:50]
            print(f"✅ [{i}/{len(SEED_MEMORIES)}] {category}: {preview}...")
            
        except Exception as e:
            fail_count += 1
            print(f"❌ [{i}/{len(SEED_MEMORIES)}] 失敗: {e}")
    
    # 顯示結果
    print()
    print("=" * 60)
    print("📊 導入結果")
    print("=" * 60)
    print(f"✅ 成功: {success_count} 條")
    print(f"❌ 失敗: {fail_count} 條")
    print()
    
    print("📋 格式統計:")
    print(f"   • 決策框架格式: {format_stats['framework']} 條")
    print(f"   • 戰略記憶格式: {format_stats['strategic']} 條")
    print()
    
    if context_stats:
        print("📂 分類統計:")
        for context, count in sorted(context_stats.items()):
            print(f"   • {context}: {count} 條")
    
    print()
    print("🎉 種子記憶導入完成！")
    print()
    
    # 驗證導入
    print("🔍 驗證導入結果...")
    try:
        recent = memory.get_recent_memories(limit=3)
        if recent:
            print(f"✅ 可以讀取記憶，最新 3 條:")
            for i, mem in enumerate(recent, 1):
                print(f"   {i}. {mem[:60]}...")
        else:
            print("⚠️  記憶庫為空，可能導入失敗")
    except Exception as e:
        print(f"⚠️  驗證時發生錯誤: {e}")
    
    print()
    print("=" * 60)


def clear_all_memories():
    """清空所有記憶（危險操作）"""
    
    print("⚠️  警告：此操作將清空所有記憶！")
    confirm = input("請輸入 'YES' 確認清空: ")
    
    if confirm != "YES":
        print("❌ 操作已取消")
        return
    
    try:
        memory = JarvisMemory()
        
        # 獲取所有記憶
        all_memories = memory.get_all_memories(limit=1000)
        
        print(f"🗑️  正在刪除 {len(all_memories)} 條記憶...")
        
        # 刪除每一條
        for mem in all_memories:
            memory.db.collection('memories').document(mem['id']).delete()
        
        print("✅ 所有記憶已清空")
        
    except Exception as e:
        print(f"❌ 清空失敗: {e}")


def show_memory_stats():
    """顯示記憶庫統計"""
    
    print("📊 記憶庫統計")
    print("=" * 60)
    
    try:
        memory = JarvisMemory()
        
        # 獲取所有記憶
        all_memories = memory.get_all_memories(limit=1000)
        
        print(f"總記憶數: {len(all_memories)}")
        print()
        
        # 按分類統計
        category_stats = {}
        for mem in all_memories:
            cat = mem.get('category', 'unknown')
            category_stats[cat] = category_stats.get(cat, 0) + 1
        
        if category_stats:
            print("分類統計:")
            for cat, count in sorted(category_stats.items(), key=lambda x: -x[1]):
                print(f"   • {cat}: {count} 條")
        
        print()
        
        # 顯示最近 5 條
        print("最近 5 條記憶:")
        recent = memory.get_recent_memories(limit=5)
        for i, mem in enumerate(recent, 1):
            print(f"   {i}. {mem[:80]}...")
        
    except Exception as e:
        print(f"❌ 統計失敗: {e}")
    
    print("=" * 60)


def export_memories_to_json():
    """匯出記憶為 JSON 格式（備份用）"""
    import json
    
    print("📤 匯出記憶到 JSON...")
    
    try:
        memory = JarvisMemory()
        all_memories = memory.get_all_memories(limit=1000)
        
        # 準備匯出資料
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "total_count": len(all_memories),
            "memories": all_memories
        }
        
        # 寫入檔案
        filename = f"memories_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ 已匯出 {len(all_memories)} 條記憶到: {filename}")
        
    except Exception as e:
        print(f"❌ 匯出失敗: {e}")


if __name__ == "__main__":
    import sys
    
    # 解析命令行參數
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "load":
            load_seed_memories()
        elif command == "clear":
            clear_all_memories()
        elif command == "stats":
            show_memory_stats()
        elif command == "export":
            export_memories_to_json()
        else:
            print("❌ 未知命令")
            print()
            print("使用方式:")
            print("   python seed_loader.py load     # 導入種子記憶")
            print("   python seed_loader.py stats    # 顯示統計")
            print("   python seed_loader.py clear    # 清空記憶（危險）")
            print("   python seed_loader.py export   # 匯出備份")
    else:
        # 預設執行導入
        load_seed_memories()
