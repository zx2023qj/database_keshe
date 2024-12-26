from flask import Flask, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
# from flask_pymongo import PyMongo
from redis import Redis
# from elasticsearch import Elasticsearch

db = SQLAlchemy()
migrate = Migrate()

def create_app():

    # init app
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    # init db and migrate
    db.init_app(app)
    migrate.init_app(app, db)
    
    # init redis
    global redis_client
    redis_client = Redis.from_url(app.config["REDIS_URL"])

    # check redis connection
    # is_connect = redis_client.ping()
    # if is_connect:
    #     print("Redis连接成功")
    # else:
    #     print("Redis连接失败")
    # es = Elasticsearch(app.config["ELASTICSEARCH_URL"])

    # init app routes
    from app.routes import init_routes
    # 注册蓝图
    init_routes(app)


    #reset_database(app)
    # 禁用浏览器的缓存
    @app.after_request
    def add_no_cache(response):
        response.cache_control.no_store = True
        return response

    # add initial admin
    with app.app_context():
        from app.models import User 
        existing_user = User.query.filter(User.username == 'admin').first()
        if existing_user:
            print("已经初始化admin!")
        else:
            from hashlib import sha256
            password = 'admin'
            hashed_password = sha256(password.encode()).hexdigest()
            new_user = User(username='admin', email='admin@admin', password=hashed_password, role='admin',ip = 'localhost')
            db.session.add(new_user)
            db.session.commit()
    return app

# reset database
def reset_database(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("数据库已重置")