"""Deterministic sample API for trying TraceForge locally."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="TraceForge Demo Store API", version="1.0.0")
PRODUCTS = [
    {"id": 1, "name": "Mechanical Keyboard", "price": 79.0, "in_stock": True},
    {"id": 2, "name": "USB-C Hub", "price": 39.5, "in_stock": True},
    {"id": 3, "name": "Monitor Stand", "price": 29.0, "in_stock": False},
]
class OrderInput(BaseModel):
    product_id: int
    quantity: int = Field(default=1, gt=0, le=100)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/products")
def list_products():
    return {"count": len(PRODUCTS), "items": PRODUCTS}

@app.get("/products/{product_id}")
def get_product(product_id: int):
    for product in PRODUCTS:
        if product["id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")

@app.post("/orders", status_code=201)
def create_order(order: OrderInput):
    product = next((p for p in PRODUCTS if p["id"] == order.product_id), None)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if not product["in_stock"]:
        raise HTTPException(status_code=409, detail="Product is out of stock")
    return {"order_id": "order-demo-001", "product_id": order.product_id,
            "quantity": order.quantity,
            "total": round(float(product["price"]) * order.quantity, 2),
            "status": "created"}
