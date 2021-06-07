### 一、创建钉钉扫码登陆
https://developers.dingtalk.com/document/app/scan-qr-code-to-log-on-to-third-party-websites

https://developers.dingtalk.com/document/app/scan-qr-code-to-login-isvapp
### 二、创建钉钉自建应用
https://developers.dingtalk.com/document/app/create-orgapp

### 三、执行数据迁移
- python manage.py makemigrations
- python manage.py migrate
- python manage.py createsuperuser --username guji --email gujiwork@outlook.com
- python manage.py runserver
### 四、修改apps/account/view/dingtalk.py
```
.env DING_LOGIN_EMAIL_SUFFIX = 'pigs.com'
 将邮箱修改为您公司钉钉绑定的邮箱
```
### 五、配置Api接口转发
```angular2html
yum install -y openresty

upstream api {
  server localhost:8000;
}
server {
    listen       80;
    server_name  _;
    root         /data/webapps/pigs-web;

    # Load configuration files for the default server block.
    location / {
      try_files $uri $uri/ /index.html;
      add_header Access-Control-Allow-Origin *;
      add_header Access-Control-Allow-Methods 'GET, POST, OPTIONS';
      add_header Access-Control-Allow-Headers 'DNT,X-Mx-ReqToken,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Authorization';
      add_header Cache-Control no-cache;
      add_header Cache-Control private;
      expires -1;
    }


    location /api {
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_pass http://api;
      add_header Access-Control-Allow-Origin *;
      add_header Access-Control-Allow-Methods 'GET, POST, OPTIONS';
      add_header Access-Control-Allow-Headers 'DNT,X-Mx-ReqToken,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Authorization';
      proxy_pass_header       Set-Cookie;
    }

    location /ws {
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_pass http://api;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection $connection_upgrade;
      proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /admin/ {
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_pass http://api/admin/;
    }

    location /static/ {
      proxy_redirect off;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_pass http://api/static/;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection $connection_upgrade;

    }
    access_log logs/pigs-access.log main;
    error_log logs/pigs-err.log;
}

```
### 六、导入权限表
```angular2html
1、导入rbac_role 角色表

2、导入rbac_menu 菜单表

3、导入rbac_permission 权限表

4、登录django后台为角色绑定权限和菜单，最后再把用户绑定到角色
```

##### 启动监控程序
```angular2html
修改metrics_proxy.yaml配置文件

./metrics_proxy proxy -c metrics_proxy.yaml # 启动程序

修改.env 文件 api_metrics_url=metrics_proxy port和 api_metrics_token=metrics_proxy token
```

#### Ansible 任务
```angular2html
yum install -y sshpass
```

#### Ansible 分发, 文件大小控制
```angular2html
在Nginx http{}中加入 client_max_body_size 20m;
```