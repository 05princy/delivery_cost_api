from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
import uvicorn
import itertools
import math

app = FastAPI()

inventory = {
    "C1": {"A", "B", "C", "G"},
    "C2": {"B", "C", "D", "E", "G", "H", "I"},
    "C3": {"C", "D", "E", "F", "G", "H", "I"}
}

weights = {
    "A": 3, "B": 2, "C": 8,
    "D": 12, "E": 25,
    "F": 0.5, "G": 15,
    "H": 1, "I": 2
}

distances = {
    ("C1", "L1"): 4, ("L1", "C1"): 4,
    ("C2", "L1"): 2.5, ("L1", "C2"): 2.5,
    ("C3", "L1"): 3, ("L1", "C3"): 3,
    ("C1", "C2"): 4, ("C2", "C1"): 4,
    ("C1", "C3"): 3, ("C3", "C1"): 3,
    ("C2", "C3"): 2, ("C3", "C2"): 2
}

def cost_per_km(weight: float) -> int:
    if weight <= 5:
        return 10
    extra = math.ceil((weight - 5) / 5)
    return 10 + (extra * 8)

class OrderRequest(BaseModel):
    __root__: Dict[str, int]

@app.post("/calculate-cost")
def calculate_cost(order: OrderRequest):
    order_items = {k: v for k, v in order.__root__.items() if v > 0}
    required_products = set(order_items.keys())

    # Product availability map
    product_locations = {
        product: [c for c in inventory if product in inventory[c]]
        for product in required_products
    }

    # Return 0 if any product is not found in any center
    if any(len(locs) == 0 for locs in product_locations.values()):
        return {"minimum_cost": 0}

    min_cost = float("inf")

    # Generate all product -> center assignments
    def generate_assignments(products, current={}):
        if not products:
            return [current]
        product = products[0]
        result = []
        for center in product_locations[product]:
            new_assign = current.copy()
            new_assign[product] = center
            result += generate_assignments(products[1:], new_assign)
        return result

    all_assignments = generate_assignments(list(order_items.keys()))

    for assignment in all_assignments:
        centers_involved = set(assignment.values())
        for start_center in centers_involved:
            other_centers = [c for c in centers_involved if c != start_center]
            for perm in itertools.permutations(other_centers):
                route = [start_center] + list(perm)
                total_cost = 0
                delivered = set()

                for center in route:
                    # Pick up items from current center
                    delivery_items = [p for p, loc in assignment.items() if loc == center and p not in delivered]
                    if delivery_items:
                        weight = sum(weights[p] * order_items[p] for p in delivery_items)
                        rate = cost_per_km(weight)
                        dist = distances.get((center, "L1"), float("inf"))
                        total_cost += rate * dist
                        delivered.update(delivery_items)

                    # Go to next center (L1 → next pickup)
                    if center != route[-1]:
                        next_center = route[route.index(center) + 1]
                        total_cost += distances.get(("L1", next_center), float("inf"))

                if total_cost < min_cost:
                    min_cost = total_cost

    return {"minimum_cost": round(min_cost)}
