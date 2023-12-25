from pydantic import BaseModel, constr, ValidationError
from datetime import datetime
from enums import StatusEnum
from typing import Optional, Union

class CustomerCreate(BaseModel):
    name: constr(max_length=45, strict=True)
    email: constr(max_length=120, strict=True)
    dni: constr(max_length=45, strict=True)
    last_name: constr(max_length=45, strict=True)
    address: Optional[Union[constr(max_length=45), None]] = None
    date_registry: datetime = datetime.utcnow()
    id_com: int
    id_reg: int
    status: Optional[Union[StatusEnum, None]] = StatusEnum.Inactive   
class RegionCreate(BaseModel):
    description: constr(max_length=90, strict=True)
    

class CommuneCreate(BaseModel):
    id_reg: int
    description: constr(max_length=90, strict=True)
    
class TokenCreate(BaseModel):
    id_tok: int
    token: constr(max_length=90, strict=True)
    login_time: datetime
    email: constr(max_length=120, strict=True)
    random_value: int