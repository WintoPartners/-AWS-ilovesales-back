#!/bin/bash

# certbot 설치 (이미 설치되어 있지 않은 경우)
if ! command -v certbot &> /dev/null; then
    sudo dnf install -y certbot python3-certbot-nginx
fi

# nginx 설정 파일 생성
sudo bash -c 'cat << "EOF" > /etc/nginx/conf.d/proxy.conf
map $http_origin $cors_origin {
    default "";
    "https://www.ilovesales.site" "$http_origin";
    "https://ilovesales-site.imweb.me" "$http_origin";
}

server {
    listen 80;
    listen 443 ssl;
    server_name api.ilovesales.site;

    ssl_certificate /etc/letsencrypt/live/api.ilovesales.site/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.ilovesales.site/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # FastAPI의 CORS 헤더 제거
    proxy_hide_header "Access-Control-Allow-Origin";
    proxy_hide_header "Access-Control-Allow-Methods";
    proxy_hide_header "Access-Control-Allow-Headers";
    proxy_hide_header "Access-Control-Expose-Headers";
    proxy_hide_header "Access-Control-Max-Age";
    proxy_hide_header "Access-Control-Allow-Credentials";

    location / {
        if ($request_method = "OPTIONS") {
            add_header "Access-Control-Allow-Origin" $cors_origin always;
            add_header "Access-Control-Allow-Methods" "GET, POST, OPTIONS" always;
            add_header "Access-Control-Allow-Headers" "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;
            add_header "Access-Control-Allow-Credentials" "true" always;
            add_header "Access-Control-Max-Age" 1728000;
            add_header "Content-Type" "text/plain; charset=utf-8";
            add_header "Content-Length" 0;
            return 204;
        }

        add_header "Access-Control-Allow-Origin" $cors_origin always;
        add_header "Access-Control-Allow-Methods" "GET, POST, OPTIONS" always;
        add_header "Access-Control-Allow-Headers" "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;
        add_header "Access-Control-Allow-Credentials" "true" always;
        add_header "Access-Control-Expose-Headers" "Content-Length,Content-Range" always;

        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name api.ilovesales.site;
    return 301 https://$server_name$request_uri;
}
EOF'

# nginx types_hash 설정 파일 생성
sudo bash -c 'cat << "EOF" > /etc/nginx/conf.d/types_hash.conf
types_hash_max_size 2048;
types_hash_bucket_size 128;
EOF'

# SSL 인증서가 없는 경우 발급 시도
if [ ! -d "/etc/letsencrypt/live/api.ilovesales.site" ]; then
    sudo certbot --nginx -d api.ilovesales.site --non-interactive --agree-tos --email your-email@example.com
fi

# nginx 설정 테스트 및 재시작
sudo nginx -t && sudo systemctl restart nginx 