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

def load_config(config_file: str = "config.properties") -> Config:
    config = configparser.ConfigParser()
    # Find the config file in the project root relative to this file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, config_file)
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file {config_path} not found")
    
    config.read(config_path)
    
    return Config(
        db_url=config.get("database", "db_url"),
        redis_url=config.get("redis", "redis_url"),
        broker_url=config.get("celery", "broker_url"),
        result_backend=config.get("celery", "result_backend"),
        docker_host=config.get("docker", "docker_host"),
        port=config.getint("app", "port"),
        admin_port=config.getint("app", "admin_port"),
        host=config.get("app", "host"),
        debug=config.getboolean("app", "debug")
    )

settings = load_config()
