# Makefile for Stock Backtest System Docker Management

.PHONY: help build up down restart logs ps clean rebuild dev prod reset-db

# Default target
.DEFAULT_GOAL := help

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Stock Backtest System - Docker Management$(NC)"
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2}'

build: ## Build all Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	docker-compose build

up: ## Start all services in background
	@echo "$(GREEN)Starting all services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started! Access at http://localhost$(NC)"

down: ## Stop all services
	@echo "$(RED)Stopping all services...$(NC)"
	docker-compose down

restart: ## Restart all services
	@echo "$(GREEN)Restarting all services...$(NC)"
	docker-compose restart

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs only
	docker-compose logs -f backend

logs-frontend: ## View frontend logs only
	docker-compose logs -f frontend

ps: ## Show status of all services
	docker-compose ps

shell-backend: ## Open shell in backend container
	docker-compose exec backend bash

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend sh

clean: ## Stop services and remove containers, networks
	@echo "$(RED)Cleaning up containers and networks...$(NC)"
	docker-compose down
	@echo "$(GREEN)Cleanup complete!$(NC)"

clean-all: ## Stop services and remove everything (including images)
	@echo "$(RED)Removing all containers, networks, and images...$(NC)"
	docker-compose down --rmi all --volumes
	@echo "$(GREEN)Complete cleanup done!$(NC)"

rebuild: ## Rebuild and restart all services
	@echo "$(GREEN)Rebuilding and restarting services...$(NC)"
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "$(GREEN)Rebuild complete! Access at http://localhost$(NC)"

dev: ## Start services with live reload (development mode)
	@echo "$(GREEN)Starting in development mode...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

prod: up ## Start services in production mode (alias for 'up')

health: ## Check health status of all services
	@echo "$(BLUE)Checking service health...$(NC)"
	@echo "Backend: " && curl -s http://localhost:4001/health | grep -q "ok" && echo "$(GREEN)OK$(NC)" || echo "$(RED)FAIL$(NC)"
	@echo "Frontend: " && curl -s http://localhost:4000/ > /dev/null && echo "$(GREEN)OK$(NC)" || echo "$(RED)FAIL$(NC)"

stats: ## Show resource usage statistics
	docker stats stock-backtest-backend stock-backtest-frontend

backup: ## Backup any persistent data
	@echo "$(GREEN)Creating backup...$(NC)"
	@mkdir -p backups
	@docker-compose exec backend tar czf /tmp/backup-$(shell date +%Y%m%d-%H%M%S).tar.gz /app/logs 2>/dev/null || true
	@echo "$(GREEN)Backup created!$(NC)"

update: ## Update code and restart services
	@echo "$(GREEN)Updating application...$(NC)"
	git pull origin main
	$(MAKE) rebuild
	@echo "$(GREEN)Update complete!$(NC)"

test-backend: ## Run backend tests
	docker-compose exec backend pytest

lint-backend: ## Run backend code linting
	docker-compose exec backend flake8 app/

format-backend: ## Format backend code
	docker-compose exec backend black app/

reset-db: ## Reset database (WARNING: deletes all data)
	@echo "$(RED)WARNING: This will delete all data in the database!$(NC)"
	@POSTGRES_HOST=localhost ./sql/init_db.sh

restart-backend: ## Restart backend service only
	@echo "$(GREEN)Restarting backend service...$(NC)"
	docker-compose restart backend

restart-frontend: ## Restart frontend service only
	@echo "$(GREEN)Restarting frontend service...$(NC)"
	docker-compose restart frontend
