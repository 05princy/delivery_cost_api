from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Dict
import uvicorn
import itertools

app = FastAPI()

# Define inventory of each center
inventory = {
    "C1": {"A", "B", "C", "G"},
    "C2": {"B", "C", "D", "E", "G", "H", "I"},
    "C3": {"C", "D", "E", "F", "G", "H", "I"}
}

# Define cost between locations (symmetric)
cost_matrix = {
    ("C1", "L1" ): 20,
    ("C2", "L1" ): 40,
    ("C3", "L1" ): 60,
    ("C1", "C2"): 30,
    ("C1", "C3"): 50,
    ("C2", "C3"): 20,
}

# Make cost matrix symmetric
def get_cost(a, b):
    if (a, b) in cost_matrix:
        return cost_matrix[(a, b)]
    if (b, a) in cost_matrix:
        return cost_matrix[(b, a)]
    return float('inf')

class OrderRequest(BaseModel):
    __root__: Dict[str, int]  # Dynamic keys for products

@app.post("/calculate-cost")
def calculate_cost(order: OrderRequest):
    order_data = order.__root__
    required_items = {k for k, v in order_data.items() if v > 0}

    # Find which centers have which required items
    centers_used = {center: required_items & items for center, items in inventory.items()}
    centers_with_items = {c for c, v in centers_used.items() if v}

    min_total_cost = float('inf')

    # Try each center as starting point
    for start_center in ["C1", "C2", "C3"]:
        if start_center not in centers_with_items:
            continue

        other_centers = list(centers_with_items - {start_center})

        for perm in itertools.permutations(other_centers):
            route = [start_center]
            route.extend(perm)

            total_cost = 0
            current = start_center

            for c in route:
                total_cost += get_cost(current, "L1")  # Drop to L1
                current = c

            total_cost += get_cost(current, "L1")  # Final delivery

            if total_cost < min_total_cost:
                min_total_cost = total_cost

    return {"minimum_cost": min_total_cost if min_total_cost != float('inf') else 0}

# For local testing
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
