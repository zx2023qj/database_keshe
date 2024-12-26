#### 部署流程

由于在windows忘记用虚拟环境了，所以requirements.txt里面的库可能不是很全

```
python3 run.py
(报错的话缺哪个库就安装哪个，如果没报错就停止然后直接下面的数据库初始化，当然mysql里面要先建好数据库)
flask db init
flask db migrate -m "Initial"
flask db upgrade
再执行
python3 run.py
浏览器访问127.0.0.1:5000，你要是有兴趣开内网也可以自己开（
```

相关文章：https://zx2023qj.github.io/2024/12/19/%E6%95%B0%E6%8D%AE%E5%BA%93%E5%AE%9E%E9%AA%8C-%E8%AF%BE%E8%AE%BE/
