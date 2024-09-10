from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from model import Nasabah,Mutasi
from schema import user,UserInDB,UserLogin,Tabung,Tarik,Transfer
from sqlalchemy import or_
import logging
import random
from auth.auth_bearer import JWTBearer
from auth.auth_handler import sign_jwt, get_password_hash, verify_password, create_access_token,decode_refresh_token

def generate_no_rekening() -> str:
    """Menghasilkan nomor rekening unik dengan format 16 digit."""
    random_digits = random.randint(0, 99999999)
    formatted_digits = f"{random_digits:08d}"
    no_rekening = f"113{formatted_digits}"
    return no_rekening

def signup(data: user, session: Session):
    try:
        existing_nasabah = session.query(Nasabah).filter(
            or_(
                Nasabah.nik == data.nik,
                Nasabah.no_hp == data.no_hp
            )
        ).first()

        if existing_nasabah:
            logging.warning(f"NIK atau No HP sudah digunakan: NIK={data.nik}, No HP={data.no_hp}")
            return None, "NIK atau No HP sudah digunakan"
        
        hashed_password = get_password_hash(data.password)
        no_rekening = generate_no_rekening()

        new_nasabah = Nasabah(
            nama=data.nama,
            nik=data.nik,
            email=data.email, 
            no_hp=data.no_hp,
            no_rekening=no_rekening,
            password=hashed_password
        )

        session.add(new_nasabah)
        session.commit()
        logging.info(f"Nasabah berhasil dibuat: Nama={new_nasabah.nama}, No Rekening={new_nasabah.no_rekening}, No HP={new_nasabah.no_hp}")
        return new_nasabah, None

    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Kesalahan saat membuat nasabah: {str(e)}")
        return None, str(e)
    

def login(data: UserLogin, session: Session):
    try:
        # Mengambil nasabah berdasarkan nama pengguna (username)
        existing_nasabah = session.query(Nasabah).filter(
            Nasabah.nama == data.username  # Username disini adalah nama pengguna
        ).first()

        # Jika pengguna ditemukan dan password sesuai
        if existing_nasabah and verify_password(data.password, existing_nasabah.password):
            access_token = sign_jwt(
                user_id=str(existing_nasabah.id),
                nama=existing_nasabah.nama,  # Nama pengguna
                nik=existing_nasabah.nik,  # NIK pengguna
                no_hp=existing_nasabah.no_hp,  # Nomor HP pengguna
                email=existing_nasabah.email  # Email pengguna
            )['access_token']
            
            return {
                "access_token": access_token,
                "token_type": "bearer"
            }, None

        # Jika tidak ditemukan atau password salah
        if not existing_nasabah:
            logging.warning(f"Pengguna tidak ditemukan: {data.username}")
            return None, "Pengguna tidak ditemukan"
        else:
            logging.warning(f"Password salah untuk pengguna: {data.username}")
            return None, "Password salah"

    except SQLAlchemyError as e:
        logging.error(f"Kesalahan saat login: {str(e)}")
        return None, str(e)
    

def tabung(data: Tabung, session: Session):
    """Menambahkan saldo ke rekening nasabah dan mencatat mutasi."""
    try:
        # Validasi data
        if data.nominal <= 0:
            logging.warning(f"Nominal harus lebih besar dari nol: {data.nominal}")
            return None, "Nominal harus lebih besar dari nol"

        # Mengambil nasabah berdasarkan no_rekening
        nasabah = session.query(Nasabah).filter(Nasabah.no_rekening == data.no_rekening).first()

        if not nasabah:
            logging.warning(f"No Rekening tidak dikenali: {data.no_rekening}")
            return None, "No Rekening tidak dikenali"

        # Menambahkan saldo
        nasabah.saldo += data.nominal

        # Membuat data mutasi
        mutasi = Mutasi(
            no_rekening=nasabah.no_rekening,
            saldo=nasabah.saldo,  # Menyimpan saldo setelah transaksi
            jenis_transaksi="kredit",
            keterangan="Tabung"
        )

        # Menyimpan perubahan ke database
        session.add(mutasi)
        session.commit()

        logging.info(f"Tabungan berhasil: No Rekening={nasabah.no_rekening}, Saldo={nasabah.saldo}")
        return nasabah.saldo, None

    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Kesalahan saat menabung: {str(e)}")
        return None, str(e)
    
def tarik(data: Tarik, session: Session):
    """Menarik dana dari rekening nasabah."""
    try:
        # Mengambil nasabah berdasarkan no_rekening
        nasabah = session.query(Nasabah).filter(Nasabah.no_rekening == data.no_rekening).first()

        if not nasabah:
            logging.warning(f"No Rekening tidak dikenali: {data.no_rekening}")
            return None, "No Rekening tidak dikenali"

        if nasabah.saldo < data.nominal:
            logging.warning(f"Saldo tidak cukup: No Rekening={nasabah.no_rekening}, Saldo={nasabah.saldo}, Nominal={data.nominal}")
            return None, "Saldo tidak cukup"

        # Mengurangi saldo nasabah
        nasabah.saldo -= data.nominal
        
        # Membuat data mutasi
        mutasi = Mutasi(
            no_rekening=nasabah.no_rekening,
            saldo=nasabah.saldo,  # Menyimpan saldo setelah transaksi
            jenis_transaksi="debit",
            keterangan="Tarik"
        )
        
        # Menyimpan perubahan ke database
        session.add(mutasi)
        session.commit()

        logging.info(f"Penarikan berhasil: No Rekening={nasabah.no_rekening}, Saldo={nasabah.saldo}")
        return nasabah.saldo, None

    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Kesalahan saat menarik dana: {str(e)}")
        return None, str(e)

def transfer(data: Transfer, session: Session):
    """Mentrasfer dana antar rekening."""
    try:
        pengirim = session.query(Nasabah).filter(Nasabah.no_rekening == data.no_rekening_pengirim).first()
        penerima = session.query(Nasabah).filter(Nasabah.no_rekening == data.no_rekening_penerima).first()

        if not pengirim:
            logging.warning(f"No Rekening pengirim tidak dikenali: {data.no_rekening_pengirim}")
            return None, "No Rekening pengirim tidak dikenali"

        if not penerima:
            logging.warning(f"No Rekening penerima tidak dikenali: {data.no_rekening_penerima}")
            return None, "No Rekening penerima tidak dikenali"

        if pengirim.saldo < data.nominal:
            logging.warning(f"Saldo pengirim tidak cukup: No Rekening={pengirim.no_rekening}, Saldo={pengirim.saldo}, Nominal={data.nominal}")
            return None, "Saldo pengirim tidak cukup"

        # Update saldo
        pengirim.saldo -= data.nominal
        penerima.saldo += data.nominal

        # Menyimpan data mutasi untuk pengirim
        mutasi_pengirim = Mutasi(
            no_rekening=pengirim.no_rekening,
            saldo=pengirim.saldo,  # Updated saldo after the transaction
            jenis_transaksi="debit",  # Jenis transaksi "debit"
            keterangan=f"Transfer ke {data.no_rekening_penerima}"
        )
        session.add(mutasi_pengirim)
        
        # Menyimpan data mutasi untuk penerima
        mutasi_penerima = Mutasi(
            no_rekening=penerima.no_rekening,
            saldo=penerima.saldo,  # Updated saldo after the transaction
            jenis_transaksi="kredit",  # Jenis transaksi "kredit"
            keterangan=f"Transfer dari {data.no_rekening_pengirim}"
        )
        session.add(mutasi_penerima)

        # Commit transaksi ke database
        session.commit()

        logging.info(f"Transfer berhasil: Dari No Rekening={pengirim.no_rekening} ke No Rekening={penerima.no_rekening}, Saldo Pengirim={pengirim.saldo}, Saldo Penerima={penerima.saldo}")
        return {
            "saldo_pengirim": pengirim.saldo,
            "saldo_penerima": penerima.saldo
        }, None

    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Kesalahan saat transfer: {str(e)}")
        return None, str(e)

def ceksaldo(no_rekening: str, session: Session):
    """Cek saldo rekening nasabah berdasarkan no_rekening."""
    try:
        # Query nasabah based on no_rekening
        nasabah = session.query(Nasabah).filter(Nasabah.no_rekening == no_rekening).first()
        
        if not nasabah:
            return None, "No Rekening tidak dikenali"
        
        return nasabah.saldo, None

    except SQLAlchemyError as e:
        session.rollback()
        return None, f"Kesalahan saat mengecek saldo: {str(e)}"

def cek_mutasi(no_rekening: str, session: Session):
    """Mengecek mutasi berdasarkan nomor rekening."""
    try:
        # Query untuk mendapatkan semua mutasi berdasarkan nomor rekening
        mutasi_records = session.query(Mutasi).filter(Mutasi.no_rekening == no_rekening).all()

        if not mutasi_records:
            logging.warning(f"Tidak ada mutasi untuk No Rekening: {no_rekening}")
            return [], "Tidak ada mutasi untuk No Rekening ini"

        # Konversi hasil query ke format yang dapat digunakan
        mutasi_list = [
            {
                "id": mutasi.id,
                "no_rekening": mutasi.no_rekening,
                "jenis_transaksi": mutasi.jenis_transaksi,
                "tanggal_transaksi": mutasi.tanggal_transaksi.isoformat() if mutasi.tanggal_transaksi else None,
                "nominal": mutasi.saldo,
                "saldo": mutasi.saldo,
                "keterangan": mutasi.keterangan
            }
            for mutasi in mutasi_records
        ]

        logging.info(f"Mutasi ditemukan untuk No Rekening={no_rekening}")
        return mutasi_list, None

    except SQLAlchemyError as e:
        logging.error(f"Kesalahan saat mengecek mutasi: {str(e)}")
        return None, str(e)
