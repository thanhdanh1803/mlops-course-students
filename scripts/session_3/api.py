import os
from enum import Enum

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from scripts.session_3.router import predict, utils

app = FastAPI()
app.include_router(predict.housing_router)
app.include_router(utils.utils_router)


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
    port = os.getenv("HOST_PORT", 8080)
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)
