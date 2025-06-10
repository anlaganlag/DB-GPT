**Docker容器日志**

docker logs db-gpt-webserver-1 --tail 50
docker logs db-gpt-webserver-1 -f  # 实时查看

**容器内部日志**

docker exec -it db-gpt-webserver-1 ls /app/logs/
docker exec -it db-gpt-webserver-1 tail -f /app/logs/dbgpt.log