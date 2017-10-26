docker-compose build
docker-compose up -d
docker-compose scale chrome=3
docker logs --follow crawlercluster_worker_1
docker-compose down


docker service logs crawlercluster_worker_1
docker-compose stop
docker-compose start


docker logs `docker ps | grep crawlercluster_worker_1 | cut -d' ' -f1`