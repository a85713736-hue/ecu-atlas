"""Начальный координатор: очередь задач без автономного веб-поиска."""
from dataclasses import dataclass
from typing import Literal
Role = Literal['search','ecu_analysis','loader','electronics','verification','publisher']
ROLES: tuple[Role,...] = ('search','ecu_analysis','loader','electronics','verification','publisher')
@dataclass
class Task:
    ecu_id: str
    role: Role
    status: str = 'queued'

def plan_ecu(ecu_id: str) -> list[Task]:
    if not ecu_id.strip():
        raise ValueError('ecu_id required')
    return [Task(ecu_id, role) for role in ROLES]
if __name__=='__main__':
    for task in plan_ecu('example-chinese-ecu'):
        print(task)
