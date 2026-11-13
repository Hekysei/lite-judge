import asyncio
from src.storage import load_results_log, save_results_log

results_log = []
log_lock = asyncio.Lock()
next_id = 1


def load_data():
    """Читает лог с диска при старте и вычисляет следующий номер посылки."""
    global next_id
    data = load_results_log()
    results_log.clear()
    results_log.extend(data)
    
    if results_log:
        max_id = max([res.get("id", 0) for res in results_log], default=0)
        next_id = max_id + 1
        
    print(f"Восстановлено {len(results_log)} записей с диска.")


async def add_log(entry: dict) -> int:
    """Добавляет запись в начало лога, присваивает ID и сохраняет."""
    global next_id
    async with log_lock:
        entry["id"] = next_id
        next_id += 1
        
        results_log.insert(0, entry)
        await asyncio.to_thread(save_results_log, results_log)
        
    return entry["id"]


async def update_log(entry: dict, new_status: str):
    """Обновляет статус и сохраняет."""
    async with log_lock:
        entry["status"] = new_status
        await asyncio.to_thread(save_results_log, results_log)
