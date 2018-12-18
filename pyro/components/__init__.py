from .base import Component, ComponentType
from .combat import CombatComponent
from .door import DoorComponent
from .health import HealthComponent
from .inventory import InventoryComponent
from .monster_ai import MonsterAIComponent
from .potion import PotionComponent


COMPONENT_CLASS = {
    'health': HealthComponent,
    'combat': CombatComponent,
    'door': DoorComponent,
    'monster_ai': MonsterAIComponent,
    'potion': PotionComponent,
    'inventory': InventoryComponent,
}
