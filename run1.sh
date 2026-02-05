#!/bin/bash

# 1. Clean up old containers to prevent conflicts
docker compose down --remove-orphans > /dev/null 2>&1

# 2. Run the scraper
# --attach scraper-app: Hides DB and Selenium logs (SILENCE!)
# --abort-on-container-exit: Stops everything when Python finishes
echo "[*] Starting Scraper..."
docker compose up --build --abort-on-container-exit --attach scraper-app

# 3. Clean up phantom images quietly
docker image prune -f > /dev/null 2>&1

# 4. THE DB QUERY FIX
# We verify data by restarting the DB container for a brief moment.
echo "------------------------------------------"
echo "[*] checking database..."

# Wake up the DB container in the background
docker compose start db > /dev/null 2>&1

# Wait 2 seconds for Postgres to be ready (Crucial!)
sleep 2

# Run the query using 'exec' (100% reliable connection)
docker compose exec -T db psql -U user -d jobs_db -c "SELECT id, title, company, seniority, link FROM jobs;"


# Shut it back down
docker compose stop db > /dev/null 2>&1
echo "------------------------------------------"