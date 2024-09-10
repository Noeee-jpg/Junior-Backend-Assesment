from pydantic import BaseModel

class user(BaseModel):
    nik: str = "1234567890"
    nama: str = "apis"
    email: str = "apis@mail.com"
    no_hp: str = "085855557777"
    password: str = "apis123"

class UserLogin(BaseModel):
    username: str
    password: str
    
class UserInDB(BaseModel):
    username: str
    hashed_password: str

class Tabung(BaseModel):
    no_rekening: str
    nominal: float

class Tarik(BaseModel):
    no_rekening: str
    nominal: float

class Transfer(BaseModel):
    no_rekening_pengirim: str
    no_rekening_penerima: str
    nominal: float
