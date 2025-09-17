#cloud-config
package_update: true
packages:
  - docker.io
  - docker-compose
runcmd:
  - systemctl enable docker
  - systemctl start docker
  - usermod -aG docker ubuntu || true
  - mkdir -p /opt/event-finder
  - |
    cat > /opt/event-finder/docker-compose.yml <<'YAML'
    version: "3.9"
    services:
      api:
        image: ${api_image}
        environment:
          - EVENTFINDER_DATABASE_PATH=/data/event_finder.db
        volumes:
          - /opt/event-finder/data:/data
        expose:
          - "8001"
      web:
        image: ${web_image}
        expose:
          - "80"
      proxy:
        image: nginx:alpine
        ports:
          - "80:80"
        depends_on:
          - api
          - web
        volumes:
          - /opt/event-finder/nginx.conf:/etc/nginx/nginx.conf:ro
    YAML
  - |
    cat > /opt/event-finder/nginx.conf <<'NGINX'
    worker_processes auto;
    events { worker_connections 1024; }
    http {
      sendfile on;
      server {
        listen 80;
        # Serve static site from web container
        location / {
          proxy_pass http://web;
        }
        # Proxy API under same origin to avoid CORS
        location /api {
          proxy_set_header Host $host;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
          proxy_pass http://api:8001/api;
        }
        # Health endpoint
        location = /health { return 200 'ok'; add_header Content-Type text/plain; }
      }
    }
    NGINX
  - docker compose -f /opt/event-finder/docker-compose.yml up -d

