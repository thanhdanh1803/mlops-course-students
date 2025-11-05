from enum import Enum

import joblib
import pandas as pd
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

# from scripts.session_3.router import predict, utils

app = FastAPI()
# app.include_router(predict.housing_router)
# app.include_router(utils.utils_router)


@app.get("/")
def root():
    return {"message": "Hello, FastAPI!"}


class Method(str, Enum):
    add = "add"
    subtract = "subtract"
    multiply = "multiply"
    divide = "divide"


class CalculateRequest(BaseModel):
    method: Method
    num1: float
    num2: float


class CalculateResponse(BaseModel):
    result: float


class HousingPredictionRequest(BaseModel):
    average_area_income: float
    average_area_house_age: float
    average_area_number_of_rooms: float
    average_area_number_of_bedrooms: float
    area_population: float


class HousingPredictionResponse(BaseModel):
    predicted_price: float


model = joblib.load("./housing_linear.joblib")


@app.post("/predict")
def predict(request: HousingPredictionRequest) -> HousingPredictionResponse:
    input_data = {
        "Avg. Area Income": [request.average_area_income],
        "Avg. Area House Age": [request.average_area_house_age],
        "Avg. Area Number of Rooms": [request.average_area_number_of_rooms],
        "Avg. Area Number of Bedrooms": [request.average_area_number_of_bedrooms],
        "Area Population": [request.area_population],
    }
    df = pd.DataFrame(input_data)
    predictions = model.predict(df)
    return HousingPredictionResponse(predicted_price=predictions[0])


@app.post("/calculate", response_model=CalculateResponse)
def calculate(request: CalculateRequest) -> CalculateResponse:
    if request.method == Method.add:
        result = request.num1 + request.num2
    elif request.method == Method.subtract:
        result = request.num1 - request.num2
    elif request.method == Method.multiply:
        result = request.num1 * request.num2
    elif request.method == Method.divide:
        result = request.num1 / request.num2
    else:
        raise ValueError(f"Invalid method: {request.method}")
    return CalculateResponse(result=result)


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=3000, reload=True)
