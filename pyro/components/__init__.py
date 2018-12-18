from .base import Component
from .combat import CombatComponent
from .door import DoorComponent
from .health import HealthComponent
from .inventory import InventoryComponent
from .monster_ai import MonsterAiComponent
from .potion import PotionComponent


COMPONENT_CLASS = {
    'health': HealthComponent,
    'combat': CombatComponent,
    'door': DoorComponent,
    'monster_ai': MonsterAiComponent,
    'potion': PotionComponent,
    'inventory': InventoryComponent,
}
