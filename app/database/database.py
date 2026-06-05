import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


def _get_sqlite_path():
    if getattr(sys, 'frozen', False):
        # Ejecutable compilado — usar carpeta de datos del usuario
        # %APPDATA%\SARA_POS en Windows, ~/Library/Application Support/SARA_POS en Mac
        if sys.platform == "win32":
            base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "SARA_POS")
        elif sys.platform == "darwin":
            base = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "SARA_POS")
        else:
            base = os.path.join(os.path.expanduser("~"), ".sara_pos")

        # Crear la carpeta si no existe
        os.makedirs(base, exist_ok=True)
    else:
        # Desarrollo — usar raíz del proyecto
        base = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
    return os.path.join(base, "database.db")


def _get_db_config():
    if getattr(sys, 'frozen', False):
        if sys.platform == "win32":
            base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "SARA_POS")
        elif sys.platform == "darwin":
            base = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "SARA_POS")
        else:
            base = os.path.join(os.path.expanduser("~"), ".sara_pos")
        os.makedirs(base, exist_ok=True)
    else:
        base = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )

    config_path = os.path.join(base, "db_config.ini")

    config = {
        "mode": "sqlite",
        "host": "localhost",
        "port": "5432",
        "database": "sara_pos",
        "user": "sara",
        "password": "",
    }

    if not os.path.exists(config_path):
        return config

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip().lower()
                    value = value.strip()
                    if key in config:
                        config[key] = value
    except Exception:
        pass

    return config


def _build_engine(config):
    if config["mode"] == "postgresql":
        url = (
            f"postgresql+psycopg2://{config['user']}:{config['password']}"
            f"@{config['host']}:{config['port']}/{config['database']}"
        )
        return create_engine(
            url,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
    else:
        sqlite_path = _get_sqlite_path()
        url = f"sqlite:///{sqlite_path}"
        return create_engine(url, echo=False)


_config = _get_db_config()
engine = _build_engine(_config)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

DATABASE_MODE = _config["mode"]


def get_db_mode():
    return DATABASE_MODE


def reload_engine(new_config):
    global engine, SessionLocal, DATABASE_MODE, _config

    _save_db_config(new_config)

    engine = _build_engine(new_config)
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    DATABASE_MODE = new_config["mode"]
    _config = new_config

    Base.metadata.create_all(bind=engine)


def _save_db_config(config):
    if getattr(sys, 'frozen', False):
        if sys.platform == "win32":
            base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "SARA_POS")
        elif sys.platform == "darwin":
            base = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "SARA_POS")
        else:
            base = os.path.join(os.path.expanduser("~"), ".sara_pos")
        os.makedirs(base, exist_ok=True)
    else:
        base = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )

    config_path = os.path.join(base, "db_config.ini")

    lines = [
        "# Configuración de base de datos SARA+\n",
        "# mode: sqlite | postgresql\n",
        f"mode={config['mode']}\n",
        f"host={config['host']}\n",
        f"port={config['port']}\n",
        f"database={config['database']}\n",
        f"user={config['user']}\n",
        f"password={config['password']}\n",
    ]

    with open(config_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def test_connection(config):
    try:
        test_engine = _build_engine(config)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        test_engine.dispose()
        return True, "Conexión exitosa"
    except Exception as e:
        return False, str(e)