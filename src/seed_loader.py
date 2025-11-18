import os
from dotenv import load_dotenv
from jarvis_memory import JarvisMemory
from seed_memories import SEED_MEMORIES

load_dotenv()
memory = JarvisMemory()
for seed in SEED_MEMORIES:
    memory.add_memory(insight=seed['insight'], context=seed['context'], 
                     plan=seed.get('plan',''), risk=seed.get('risk',''),
                     tags=seed.get('tags',[]), source='seed')
print("✅ 导入完成")
