from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from config import SessionLocal
import crud
from schema import user,UserLogin,Tabung,Tarik,Transfer
from model import Nasabah
from auth.auth_bearer import JWTBearer
from auth.auth_handler import sign_jwt, get_password_hash, verify_password, create_access_token,decode_refresh_token

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/daftar")
async def daftar(data: user, db: Session = Depends(get_db)):
    """Endpoint untuk mendaftar nasabah baru."""
    try:
        nasabah, error = crud.signup(data, db)

        if error:
            raise HTTPException(status_code=400, detail=error)
        
        return JSONResponse(content={"no_rekening": nasabah.no_rekening}, status_code=200)

    except HTTPException as http_exc:
        return JSONResponse(content={"remark": http_exc.detail}, status_code=http_exc.status_code)

    except Exception as e:
        return JSONResponse(content={"remark": str(e)}, status_code=400)
    
@router.post("/login")
async def login(data:UserLogin, db: Session = Depends(get_db)):
    """Endpoint untuk login nasabah dan mendapatkan token JWT."""
    try:
        # Menggunakan fungsi login dari crud.py
        user, error = crud.login(data, db)
        
        if error:
            raise HTTPException(status_code=400, detail=error)
        
        # Jika login berhasil, kembalikan token
        return JSONResponse(content=user, status_code=200)
    
    except HTTPException as http_exc:
        return JSONResponse(content={"remark": http_exc.detail}, status_code=http_exc.status_code)

    except Exception as e:
        return JSONResponse(content={"remark": str(e)}, status_code=400)
    

@router.post("/tabung", dependencies=[Depends(JWTBearer())])
async def tabung(data: Tabung, db: Session = Depends(get_db)):
    """Endpoint untuk menabung ke rekening nasabah."""
    try:
        saldo, error = crud.tabung(data, db)  # Pastikan memanggil fungsi crud.tabung()

        if error:
            raise HTTPException(status_code=400, detail=error)
        
        return JSONResponse(content={"saldo": saldo}, status_code=200)

    except HTTPException as http_exc:
        return JSONResponse(content={"remark": http_exc.detail}, status_code=http_exc.status_code)

    except Exception as e:
        return JSONResponse(content={"remark": str(e)}, status_code=400)


@router.post("/tarik", dependencies=[Depends(JWTBearer())])
async def tarik(data: Tarik, db: Session = Depends(get_db)):
    """Endpoint untuk menabung ke rekening nasabah."""
    try:
        saldo, error = crud.tarik(data, db)  # Pastikan memanggil fungsi crud.tabung()

        if error:
            raise HTTPException(status_code=400, detail=error)
        
        return JSONResponse(content={"saldo": saldo}, status_code=200)

    except HTTPException as http_exc:
        return JSONResponse(content={"remark": http_exc.detail}, status_code=http_exc.status_code)

    except Exception as e:
        return JSONResponse(content={"remark": str(e)}, status_code=400)

@router.post("/transfer", dependencies=[Depends(JWTBearer())])
async def transfer(data: Transfer, db: Session = Depends(get_db)):
    """Endpoint untuk menabung ke rekening nasabah."""
    try:
        saldo, error = crud.transfer(data, db)  # Pastikan memanggil fungsi crud.tabung()

        if error:
            raise HTTPException(status_code=400, detail=error)
        
        return JSONResponse(content={"saldo": saldo}, status_code=200)

    except HTTPException as http_exc:
        return JSONResponse(content={"remark": http_exc.detail}, status_code=http_exc.status_code)

    except Exception as e:
        return JSONResponse(content={"remark": str(e)}, status_code=400)

@router.get("/ceksaldo", dependencies=[Depends(JWTBearer())])
async def ceksaldo(no_rekening: str, db: Session = Depends(get_db)):
    """Endpoint untuk mengecek saldo rekening nasabah."""
    try:
        # Query nasabah based on no_rekening
        nasabah = db.query(Nasabah).filter(Nasabah.no_rekening == no_rekening).first()

        if not nasabah:
            # Account not found
            raise HTTPException(status_code=404, detail="No Rekening tidak dikenali")

        # Return the balance
        return JSONResponse(content={"saldo": nasabah.saldo}, status_code=200)

    except HTTPException as http_exc:
        return JSONResponse(content={"remark": http_exc.detail}, status_code=http_exc.status_code)

    except Exception as e:
        # Handle unexpected errors
        return JSONResponse(content={"remark": str(e)}, status_code=500)

@router.get("/cekmutasi", dependencies=[Depends(JWTBearer())])
async def mutasi(no_rekening: str, db: Session = Depends(get_db)):
    """Endpoint untuk mengecek mutasi berdasarkan nomor rekening."""
    try:
        mutasi_list, error = crud.cek_mutasi(no_rekening, db)

        if error:
            raise HTTPException(status_code=400, detail=error)

        return JSONResponse(content={"mutasi": mutasi_list}, status_code=200)

    except HTTPException as http_exc:
        return JSONResponse(content={"remark": http_exc.detail}, status_code=http_exc.status_code)

    except Exception as e:
        return JSONResponse(content={"remark": str(e)}, status_code=400)
