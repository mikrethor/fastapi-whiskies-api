import logging
import os
from typing import List

import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException

from motor.motor_asyncio import AsyncIOMotorClient
from starlette import status


from whiskies_api.models.whisky import (
    Whisky, PyObjectId, )

app = FastAPI(title="Whiskies API", version="0.1.0")

# Configuring logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def connect_to_mongo():
    global client
    client = AsyncIOMotorClient(os.getenv('MONGO_CONNECTION_STRING', 'mongodb://localhost:27017/'))
    app.mongodb = client['whiskies']


async def close_mongo_connection():
    client.close()


# fast API - handling events
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()


@app.get("/hello", response_model=str)
async def get_test():
    logger.info("Calling get_test()...")
    return "Hello Confoo!!!"


@app.get("/whiskies/", response_model=List[Whisky])
async def get_all_whiskies():
    logger.info("Calling get_all_whiskies()...")
    whiskies = await app.mongodb["whiskies"].find().to_list(None)
    return whiskies


@app.get("/whiskies/{whisky_id}", response_model=Whisky)
async def get_whisky(whisky_id: str):
    logger.info(f"Calling get_whisky() for ID: {whisky_id}")
    try:
        # Convertir la chaîne en ObjectId pour la requête MongoDB
        obj_id = PyObjectId(whisky_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid MongoDB ObjectId") from e

    whisky = await app.mongodb["whiskies"].find_one({"_id": obj_id})
    if whisky:
        return whisky
    raise HTTPException(status_code=404, detail="Whisky not found")




@app.post("/whiskies/", response_model=Whisky, status_code=status.HTTP_201_CREATED)
async def create_whisky(whisky: Whisky):
    logger.info(f"Creating new whisky: {whisky}")

    # Vous pourriez vouloir vérifier l'unicité sur un autre champ, comme `bottle`
    existing_whisky = await app.mongodb["whiskies"].find_one({"bottle": whisky.bottle})
    if existing_whisky:
        raise HTTPException(status_code=400, detail="Whisky with this bottle name already exists")

    # Insérer le nouveau whisky; MongoDB assignera un nouvel `id` si non fourni
    new_whisky = await app.mongodb["whiskies"].insert_one(whisky.dict(exclude={"id"}))

    # Récupérer l'`id` généré par MongoDB et l'assigner à l'instance du modèle
    whisky.id = new_whisky.inserted_id

    return whisky


@app.delete("/whiskies/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_whisky(id: str):
    logger.info(f"Calling delete_whisky(id)... : {id}")

    try:
        # Convertir la chaîne en ObjectId pour la requête MongoDB
        obj_id = PyObjectId(id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid MongoDB ObjectId") from e

    delete_result = await app.mongodb["whiskies"].delete_one({"_id": obj_id})

    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Whisky not found")

    return {"message": "Whisky deleted successfully"}


def start():
    """Launched with `poetry run start` at root level"""
    uvicorn.run("whiskies_api.main:app", host="0.0.0.0", port=8000, reload=True)
