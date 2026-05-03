import subprocess
from datetime import date
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response

from app.config import settings
from app.dependencies import get_current_user

router = APIRouter(prefix="/backup", tags=["backup"])


def _db_params():
    url = settings.database_url.replace("mysql+pymysql://", "mysql://")
    p = urlparse(url)
    return {
        "host": p.hostname or "db",
        "port": str(p.port or 3306),
        "user": p.username or "overbudget",
        "password": p.password or "",
        "database": p.path.lstrip("/"),
    }


@router.get("")
def download_backup(_: str = Depends(get_current_user)):
    if not settings.gpg_passphrase:
        raise HTTPException(500, "GPG_PASSPHRASE nicht konfiguriert")

    db = _db_params()
    dump_cmd = [
        "mysqldump",
        f"-h{db['host']}", f"-P{db['port']}",
        f"-u{db['user']}", f"-p{db['password']}",
        "--single-transaction", "--routines", "--triggers",
        db["database"],
    ]
    gpg_cmd = [
        "gpg", "--symmetric", "--batch",
        "--passphrase", settings.gpg_passphrase,
        "--cipher-algo", "AES256",
        "--compress-algo", "zlib",
        "-o", "-",
    ]

    dump = subprocess.Popen(dump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    gpg = subprocess.Popen(gpg_cmd, stdin=dump.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dump.stdout.close()
    data, gpg_err = gpg.communicate()

    if dump.wait() != 0 or gpg.returncode != 0:
        raise HTTPException(500, f"Backup fehlgeschlagen: {gpg_err.decode()}")

    filename = f"overbudget-{date.today()}.sql.gpg"
    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/restore")
async def restore_backup(file: UploadFile = File(...), _: str = Depends(get_current_user)):
    if not settings.gpg_passphrase:
        raise HTTPException(500, "GPG_PASSPHRASE nicht konfiguriert")

    content = await file.read()
    db = _db_params()

    gpg_cmd = ["gpg", "--decrypt", "--batch", "--passphrase", settings.gpg_passphrase]
    gpg = subprocess.run(gpg_cmd, input=content, capture_output=True)
    if gpg.returncode != 0:
        raise HTTPException(422, "Entschlüsselung fehlgeschlagen — falsches Passwort?")

    mysql_cmd = [
        "mysql",
        f"-h{db['host']}", f"-P{db['port']}",
        f"-u{db['user']}", f"-p{db['password']}",
        db["database"],
    ]
    mysql = subprocess.run(mysql_cmd, input=gpg.stdout, capture_output=True)
    if mysql.returncode != 0:
        raise HTTPException(500, f"Restore fehlgeschlagen: {mysql.stderr.decode()}")

    return {"ok": True}
