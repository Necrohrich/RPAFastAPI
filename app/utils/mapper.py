# app/utils/mapper.py
from dataclasses import is_dataclass, asdict
from pydantic import BaseModel
from typing import TypeVar, Type, Any, Dict
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import NoInspectionAvailable

TEntity = TypeVar("TEntity")
TModel = TypeVar("TModel")

class Mapper:
    @staticmethod
    def _model_columns_as_dict(model_obj: Any) -> Dict[str, Any]:
        """
        Возвращает словарь column_name -> value для SQLAlchemy экземпляра.
        Если объект не SQLAlchemy-mapped, падает назад на vars().
        """
        try:
            insp = sa_inspect(model_obj)
            # column_attrs содержит атрибуты, соответствующие столбцам (no relationships)
            cols = [attr.key for attr in insp.mapper.column_attrs]
            return {k: getattr(model_obj, k) for k in cols if hasattr(model_obj, k)}
        except NoInspectionAvailable:
            # not a SQLAlchemy mapped object — fallback
            if isinstance(model_obj, dict):
                return dict(model_obj)
            # vars() безопаснее, чем __dict__ (работает с __slots__ иногда)
            return {k: getattr(model_obj, k) for k in vars(model_obj)}

    @staticmethod
    def model_to_entity(model: Any, entity_cls: Type[TEntity]) -> TEntity:
        """
        Принимает SQLAlchemy экземпляр *или* dict-like и возвращает entity_cls(...) отфильтрованный.
        Поддерживает dataclass, pydantic и обычный класс (аннотированный __init__).
        """
        data = Mapper._model_columns_as_dict(model)

        # dataclass (entity_cls — класс dataclass)
        if is_dataclass(entity_cls):
            fields = set(entity_cls.__dataclass_fields__.keys())
            filtered = {k: v for k, v in data.items() if k in fields}
            return entity_cls(**filtered)  # type: ignore[arg-type]

        # Pydantic model as entity
        if isinstance(entity_cls, type) and issubclass(entity_cls, BaseModel):
            return entity_cls(**data)  # type: ignore[arg-type]

        # обычный класс: берём аннотации __init__
        init_anns = getattr(entity_cls.__init__, "__annotations__", {})
        fields = set(init_anns.keys()) - {"return"}
        filtered = {k: v for k, v in data.items() if k in fields}
        return entity_cls(**filtered)  # type: ignore[arg-type]

    @staticmethod
    def _entity_to_dict(entity: Any) -> Dict[str, Any]:
        """Универсально получить dict из dataclass | pydantic | обычного объекта."""
        if is_dataclass(entity) and not isinstance(entity, type):
            return asdict(entity)
        if isinstance(entity, BaseModel):
            return entity.model_dump()
        return {k: getattr(entity, k) for k in vars(entity) if not k.startswith("_")}

    @staticmethod
    def entity_to_model(entity: Any, model_cls: Type[TModel]) -> TModel:
        """
        Конвертирует Entity -> SQLAlchemy модель instance (model_cls(**kwargs)),
        фильтруя только реальные столбцы target model.
        """
        entity_dict = Mapper._entity_to_dict(entity)

        # получаем имена колонок модели
        try:
            cols = {c.key for c in sa_inspect(model_cls).mapper.column_attrs}
        except NoInspectionAvailable:
            # model_cls не mapped class — пытаемся взять __init__ аннотации
            cols = set(getattr(model_cls.__init__, "__annotations__", {}).keys()) - {"return"}

        filtered = {k: v for k, v in entity_dict.items() if k in cols}
        return model_cls(**filtered)  # type: ignore[arg-type]

    @staticmethod
    def entity_to_dto(entity: Any, dto_cls: Type[BaseModel]) -> BaseModel:
        data = Mapper._entity_to_dict(entity)
        return dto_cls(**data)

    @staticmethod
    def _dump_to_dict(obj: Any) -> Dict[str, Any]:
        """Возвращает dict из pydantic-объекта, dict-like или других совместимых объектов."""
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        # obj может быть обычным dict
        if isinstance(obj, dict):
            return dict(obj)
        # obj может иметь model_dump (pydantic v2 compatible)
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        # falls back to pydantic v1 .dict() only if present
        if hasattr(obj, "dict"):
            # minimal use of deprecated API — only when nothing else available
            return obj.dict()
        raise TypeError("dto must be BaseModel or dict-like")

    @staticmethod
    def dto_to_entity(dto: BaseModel | Dict[str, Any], entity_cls: Type[TEntity]) -> TEntity:
        """
        dto может быть pydantic BaseModel или dict.
        """
        data = Mapper._dump_to_dict(dto)
        # model_to_entity теперь поддерживает dict input
        return Mapper.model_to_entity(data, entity_cls)