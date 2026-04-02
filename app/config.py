import configparser
import os
from pydantic import BaseModel

class Config(BaseModel):
    db_url: str
    redis_url: str
    broker_url: str
    result_backend: str
    docker_host: str
    port: int
    admin_port: int
    host: str
    debug: bool
    firebase_project_id: str = ""
    firebase_private_key: str = ""
    firebase_client_email: str = ""

def load_config(config_file: str = "config.properties") -> Config:
    config = configparser.ConfigParser()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, config_file)
    
    if os.path.exists(config_path):
        config.read(config_path)
    
    def get_val(section, key, default=None):
        # Env var check (FIREBASE_PROJECT_ID, DB_URL, etc)
        env_val = os.getenv(key.upper()) or os.getenv(f"{section.upper()}_{key.upper()}")
        if env_val:
            return env_val
        if config.has_option(section, key):
            return config.get(section, key)
        return default

    def get_int(section, key, default=0):
        val = get_val(section, key)
        return int(val) if val else default

    def get_bool(section, key, default=False):
        val = get_val(section, key)
        if isinstance(val, bool): return val
        return val.lower() in ("true", "1", "yes") if val else default

    # For private key, handle escaped newlines if coming from environment
    private_key = get_val("firebase", "firebase_private_key", "")
    if private_key:
        private_key = private_key.replace("\\n", "\n")

    return Config(
        db_url=get_val("database", "db_url", "postgresql://user:password@localhost:5432/rootnode"),
        redis_url=get_val("redis", "redis_url", "redis://localhost:6379/0"),
        broker_url=get_val("celery", "broker_url", "redis://localhost:6379/0"),
        result_backend=get_val("celery", "result_backend", "redis://localhost:6379/0"),
        docker_host=get_val("docker", "docker_host", "unix:///var/run/docker.sock"),
        port=get_int("app", "port", 8000),
        admin_port=get_int("app", "admin_port", 8001),
        host=get_val("app", "host", "0.0.0.0"),
        debug=get_bool("app", "debug", True),
        firebase_project_id=get_val("firebase", "firebase_project_id", ""),
        firebase_private_key=private_key,
        firebase_client_email=get_val("firebase", "firebase_client_email", "")
    )

settings = load_config()
