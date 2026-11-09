from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class Car(BaseModel):
    id: int
    brand: str
    model: str
    available: bool


# Temporary car database
cars = [
    {"id": 1, "brand": "Toyota", "model": "Corolla", "available": True},
    {"id": 2, "brand": "BMW", "model": "Series 3", "available": True},
    {"id": 3, "brand": "Mercedes", "model": "Class A", "available": False}
]


@app.get("/")
def home():
    return {"message": "Welcome to Car Rental API!"}


@app.get("/cars")
def get_cars():
    return cars


@app.get("/cars/{car_id}")
def get_car(car_id: int):
    for car in cars:
        if car["id"] == car_id:
            return car

    raise HTTPException(status_code=404, detail="Car not found")


@app.post("/cars", status_code=201)
def create_car(car: Car):
    cars.append(car.model_dump())
    return car


@app.put("/cars/{car_id}")
def update_car(car_id: int, updated_car: Car):
    for index, car in enumerate(cars):
        if car["id"] == car_id:
            cars[index] = updated_car.model_dump()
            return updated_car

    raise HTTPException(status_code=404, detail="Car not found")


@app.delete("/cars/{car_id}")
def delete_car(car_id: int):
    for index, car in enumerate(cars):
        if car["id"] == car_id:
            cars.pop(index)
            return {"message": "Car deleted successfully"}

    raise HTTPException(status_code=404, detail="Car not found")
