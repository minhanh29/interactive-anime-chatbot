open -a iTerm.app ./1_run_docker.command

# Step 2: Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."

check_postgres() {
  docker compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1
}

until check_postgres; do
  echo "PostgreSQL is still starting up..."
  sleep 3
done

echo "PostgreSQL is up and running!"

# Step 3: Wait for Qdrant to be ready
echo "Waiting for Qdrant to be ready..."

check_qdrant() {
  curl -s http://localhost:6333 | grep "title" > /dev/null 2>&1
}

until check_qdrant; do
  echo "Qdrant is still starting up..."
  sleep 3
done

echo "Qdrant is up and running!"

# Step 4: Wait for RabbitMQ to be ready
echo "Waiting for RabbitMQ to be ready..."

check_rabbitmq() {
  curl -s -u guest:guest http://localhost:15672/api/healthchecks/node > /dev/null 2>&1
}

until check_rabbitmq; do
  echo "RabbitMQ is still starting up..."
  sleep 3
done

echo "RabbitMQ is up and running!"

open -a iTerm.app ./2_api.command

echo "Waiting for API to be ready..."

check_api() {
  curl -s http://localhost:8000/health | grep "\"status\":\"good\"" > /dev/null 2>&1
}

until check_api; do
  echo "API is still starting up..."
  sleep 3
done

echo "API is up and running!"

# open mutation service
open -a iTerm.app ./3_mutation_consumer.command

# open character
open -a iTerm.app ./4_character.command
