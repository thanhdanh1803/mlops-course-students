from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_model():
    mock_model = MagicMock()
    # real_model.predict(some_data)
    # def ...
    #   return [2.0]
    mock_model.predict.return_value = [2.0]
    return mock_model


@pytest.fixture
def mock_pandas():
    mock_pandas = MagicMock()
    mock_pandas.DataFrame.return_value = {"test": [1, 2, 3]}
    with patch("scripts.session_3.router.predict.pd", mock_pandas):  # type hint
        yield mock_pandas


@pytest.fixture
def mock_mlflow_server(mock_model):
    mock_mlflow_server = MagicMock()
    mock_mlflow_server.sklearn.load_model.return_value = mock_model
    with patch("scripts.session_3.router.predict.mlflow", mock_mlflow_server):
        yield mock_mlflow_server


def test_get_model(mock_mlflow_server, mock_model):
    from scripts.session_3.router.predict import get_model

    model = get_model()
    assert model == mock_model
    result = model.predict([1, 2, 3])
    assert result == [2.0]


def test_predict(mock_mlflow_server, mock_model, mock_pandas):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from scripts.session_3.router.predict import housing_router

    app = FastAPI()
    app.include_router(housing_router)
    client = TestClient(app)
    response = client.post(
        "/housing/predict",
        json={
            "average_area_income": 100000,
            "average_area_house_age": 10,
            "average_area_number_of_rooms": 3,
            "average_area_number_of_bedrooms": 2,
            "area_population": 100000,
        },
    )
    assert response.status_code == 200
    assert response.json() == {"predicted_price": 2.0}
    mock_pandas.DataFrame.assert_called_once_with(
        {
            "Avg. Area Income": [100000],
            "Avg. Area House Age": [10],
            "Avg. Area Number of Rooms": [3],
            "Avg. Area Number of Bedrooms": [2],
            "Area Population": [100000],
        }
    )
