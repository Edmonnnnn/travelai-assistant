.PHONY: up down logs ps

ROOT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
ENV_FILE := $(ROOT_DIR).env
COMPOSE := $(ROOT_DIR)infra/docker-compose.yml

up:
	@if [ ! -f "$(ENV_FILE)" ]; then \
		echo "❌ .env not found. Copy .env.example → .env"; exit 1; \
	fi
	docker compose --env-file "$(ENV_FILE)" -f "$(COMPOSE)" up --build -d
	@echo "⏳ Waiting for healthchecks..."
	@check_url() { \
	  if command -v curl >/dev/null 2>&1; then \
	    curl -fsS "$$1" >/dev/null 2>&1; \
	  elif command -v wget >/dev/null 2>&1; then \
	    wget -qO- "$$1" >/dev/null 2>&1; \
	  else \
	    echo "ERROR: curl or wget required for health checks"; \
	    exit 1; \
	  fi; \
	}; \
	start=$$(date +%s); \
	while true; do \
	  if check_url "http://127.0.0.1:8810/health" && check_url "http://127.0.0.1:3000/api/health"; then \
	    break; \
	  fi; \
	  now=$$(date +%s); \
	  if [ $$((now - start)) -ge 120 ]; then \
	    echo "ERROR: Timed out waiting for healthchecks"; \
	    docker compose -f "$(COMPOSE)" ps; \
	    echo "Hint: docker compose -f \"$(COMPOSE)\" logs --tail=200 backend frontend"; \
	    exit 1; \
	  fi; \
	  sleep 2; \
	done
	@docker compose -f "$(COMPOSE)" ps
	@echo ""
	@echo "Frontend: http://localhost:$${FRONTEND_PORT}"
	@echo "Backend:  http://localhost:$${BACKEND_PORT}"
	@echo "Health:   http://localhost:$${BACKEND_PORT}/health"

down:
	docker compose -f "$(COMPOSE)" down

logs:
	docker compose -f "$(COMPOSE)" logs -f

ps:
	docker compose -f "$(COMPOSE)" ps
