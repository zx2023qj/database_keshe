import os

class Config:
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:mysqlroot@192.168.92.188:3306/examsystem"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/question_bank")
    REDIS_URL = "redis://192.168.92.188:6379/0"
    # ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
    SECRET_KEY = 'zxzx'