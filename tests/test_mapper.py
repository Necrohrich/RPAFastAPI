# tests/test_mapper.py
import uuid
from dataclasses import dataclass

from pydantic import BaseModel
from app.domain.entities.user import User
from app.domain.enums.platform_role_enum import PlatformRoleEnum
from app.infrastructure.models import UserModel
from app.utils.mapper import Mapper

class UserDTO(BaseModel):
    id: uuid.UUID
    login: str
    primary_email: str
    password_hash: str
    platform_role: PlatformRoleEnum

@dataclass
class SmallEntity:
    id: int
    login: str

def test_model_to_entity():
    test_id = uuid.uuid4()

    model = UserModel(id=test_id, login="John", primary_email="john@test.com", password_hash="ffffffff",
                      platform_role = PlatformRoleEnum.SUPPORT)

    #entity = Mapper.model_to_entity(model, User)
    entity = Mapper.model_to_entity(model, SmallEntity)

    assert entity.id == test_id
    assert entity.login == "John"
    # assert entity.primary_email == "john@test.com"
    # assert entity.password_hash == "ffffffff"
    # assert entity.platform_role == PlatformRoleEnum.SUPPORT

def test_dto_to_entity():
    test_id = uuid.uuid4()

    dto = UserDTO(id=test_id, login="Bob", primary_email="bob@test.com", password_hash="ffffffff",
                  platform_role=PlatformRoleEnum.SUPPORT)

    entity = Mapper.dto_to_entity(dto, User)

    assert entity.id == test_id
    assert entity.login == "Bob"
    assert entity.primary_email == "bob@test.com"
    assert entity.platform_role == PlatformRoleEnum.SUPPORT

def test_entity_to_model():
    test_id = uuid.uuid4()

    entity = User(id=test_id, login="Alice", primary_email="alice@test.com", password_hash="ffffffff")

    model = Mapper.entity_to_model(entity, UserModel)

    assert model.id == test_id
    assert model.login == "Alice"
    assert model.primary_email == "alice@test.com"
    assert model.password_hash == "ffffffff"

def test_entity_to_dto():
    test_id = uuid.uuid4()

    entity = User(id=test_id, login="Kate", primary_email="kate@test.com", password_hash="ffffffff",
                  platform_role=PlatformRoleEnum.SUPPORT)

    dto = Mapper.entity_to_dto(entity, UserDTO)

    assert dto.id == test_id
    assert dto.login == "Kate"
    assert dto.primary_email == "kate@test.com"
    assert dto.password_hash == "ffffffff"

def test_dict_to_entity():
    data = {"id": 5, "login": "Tom", "primary_email": "tom@test.com",  "password_hash":"ffffffff"}
    entity = Mapper.model_to_entity(data, User)

    assert entity.id == 5