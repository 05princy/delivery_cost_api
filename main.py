from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
import itertools
import math

app = FastAPI()
@app.get("/")
def read_root():
    return {"message": "API is live!"}
warehouse_stock_weights = {
    "C1": {"A": 3, "B": 2, "C": 8},
    "C2": {"D": 12, "E": 25, "F": 15},
    "C3": {"G": 0.5, "H": 1, "I": 2}
}

distances = {
    ('C1', 'L1'): 3,
    ('C2', 'L1'): 2.5,
    ('C3', 'L1'): 2,
    ('C1', 'C2'): 4,
    ('C1', 'C3'): 5,
    ('C2', 'C3'): 3,
}

# Add reverse distances
for (a, b), d in list(distances.items()):
    distances[(b, a)] = d

class Order(BaseModel):
    A: int = 0
    B: int = 0
    C: int = 0
    D: int = 0
    E: int = 0
    F: int = 0
    G: int = 0
    H: int = 0
    I: int = 0
@app.post("/delivery-cost")
def calculate_cost(order: Order):
    # 🔁 Replace with your actual logic
    total_items = sum([
        order.A, order.B, order.C, order.D,
        order.E, order.F, order.G, order.H, order.I
    ])
    cost = total_items * 10  # Dummy example
    return {"total_cost": cost}

def get_required_centers(order: Dict[str, int]) -> List[str]:
    required = set()
    for center, stock in warehouse_stock_weights.items():
        for item in order:
            if item in stock and order[item] > 0:
                required.add(center)
    return list(required)

def compute_cost(weight: float, distance: float) -> float:
    if weight == 0:
        return distance * 10
    cost = 10 * distance
    if weight > 5:
        weight -= 5
        blocks = math.ceil(weight / 5)
        cost += blocks * 8 * distance
    return cost

def get_items_by_center(center: str, order: Dict[str, int]) -> Dict[str, int]:
    return {item: qty for item, qty in order.items() if item in warehouse_stock_weights[center] and qty > 0}

@app.post("/calculate")
def calculate(order: Order):
    order_dict = order.dict()
    required_centers = get_required_centers(order_dict)
    min_cost = float('inf')

    for perm in itertools.permutations(required_centers):
        inventory = order_dict.copy()
        cost = 0
        for i, center in enumerate(perm):
            items = get_items_by_center(center, inventory)
            weight = sum(warehouse_stock_weights[center][k] * v for k, v in items.items())
            dist_to_l1 = distances[(center, 'L1')]
            cost += compute_cost(weight, dist_to_l1)
            for k in items:
                inventory[k] = 0

            # Move from L1 to next center (empty vehicle)
            if i < len(perm) - 1:
                next_center = perm[i + 1]
                cost += distances[("L1", next_center)] * 10

        if cost < min_cost:
            min_cost = cost

    return {"minimum_cost": round(min_cost)}
