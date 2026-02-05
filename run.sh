docker compose up --build --abort-on-container-exit

docker image prune

docker compose run --rm db psql -U user -d jobs_db -c "SELECT id, title, company, seniority FROM jobs ORDER BY id DESC LIMIT 1;"