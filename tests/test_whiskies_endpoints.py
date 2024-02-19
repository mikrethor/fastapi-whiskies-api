import asyncio
import logging
import os

import pytest
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from testcontainers.mongodb import MongoDbContainer

from whiskies_api.main import app
from whiskies_api.models.whisky import Whisky

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="class")
def mongo_container():
    logger.info("Starting MongoDB container...")
    with MongoDbContainer() as mongo:
        yield mongo


@pytest.fixture(scope="class", autouse=True)
def set_env_vars(mongo_container):
    os.environ['MONGO_CONNECTION_STRING'] = mongo_container.get_connection_url()
    yield
    del os.environ['MONGO_CONNECTION_STRING']


@pytest.fixture(scope="class")
def db_client(mongo_container):
    connection_string = mongo_container.get_connection_url()
    logger.info(f"MongoDB container... {connection_string}")
    db = get_database(connection_string)
    yield db


@pytest.fixture(scope="class")
def client(set_env_vars):
    with TestClient(app) as test_client:
        yield test_client


def get_database(connection_string):
    client = AsyncIOMotorClient(connection_string)
    return client.whiskies


whiskies = [
    {"bottle": "test1", "price": "109.90", "rating": "Rating", "region": "Islay"},
    {"bottle": "test2", "price": "109.90", "rating": "Rating", "region": "Islay"},
    {"bottle": "test3", "price": "109.90", "rating": "Rating", "region": "Islay"},
]


@pytest.fixture(scope="class")
def prepare_db(db_client):
    # To make the test pass, you need to insert the whiskies into the database and be sure it's stored
    loop = asyncio.get_event_loop()
    loop.run_until_complete(db_client["whiskies"].insert_many(whiskies))

    for item in whiskies:
        Whisky.model_validate(item)


def test_hello(client):
    response = client.get("/hello/")

    assert response.status_code == 200
    assert isinstance(response, str)
    assert response == "Hello Confoo!!!"


@pytest.mark.usefixtures("prepare_db")
def test_get_all_whiskies(client):
    response = client.get("/whiskies/")

    assert response.status_code == 200
    response_data = [Whisky.model_validate(whisky_data) for whisky_data in response.json()]
    expected_data = [Whisky.model_validate(whisky_data) for whisky_data in whiskies]
    assert isinstance(response_data, list)
    assert response_data == expected_data


@pytest.mark.usefixtures("prepare_db")
def test_get_a_whiskie(client):
    first_whisky_data = whiskies[0]  # Récupère le premier élément de la liste
    expected_whisky = Whisky.model_validate(first_whisky_data)  # Valide et crée une instance de Whisky
    response = client.get(f"/whiskies/{str(expected_whisky.id)}")

    assert response.status_code == 200
    response_data = [Whisky.parse_obj(response.json())][0]

    assert isinstance(response_data, Whisky)
    assert response_data == expected_whisky


@pytest.mark.usefixtures("prepare_db")
def test_create_whisky(client):
    new_whisky_data = {
        "bottle": "Nouveau Whisky",
        "price": "50.00",
        "rating": "8.5",
        "region": "Highland"
    }

    response = client.post("/whiskies/", json=new_whisky_data)

    assert response.status_code == 201

    created_whisky = Whisky.parse_obj(response.json())

    assert created_whisky.bottle == new_whisky_data["bottle"]
    assert created_whisky.price == new_whisky_data["price"]
    assert created_whisky.rating == new_whisky_data["rating"]
    assert created_whisky.region == new_whisky_data["region"]

    assert created_whisky.id is not None


@pytest.mark.usefixtures("prepare_db")
def test_delete_whisky(client):
    new_whisky_data = {
        "bottle": "Whisky to be deleted",
        "price": "50.00",
        "rating": "8.5",
        "region": "Highland"
    }

    response = client.post("/whiskies/", json=new_whisky_data)

    assert response.status_code == 201

    whisky_to_be_deleted = Whisky.parse_obj(response.json())

    _id = str(whisky_to_be_deleted.id)

    response = client.delete(f"/whiskies/{_id}")

    # Vérifier que le code de statut HTTP est 204
    assert response.status_code == 204


def test_hello(client):
    response = client.get("/hello")

    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, str)
    assert response_data == "Hello Confoo!!!"
