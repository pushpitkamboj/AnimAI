# ============================================
# AnimAI - Developer Makefile
# ============================================

.PHONY: all format lint test tests test_watch integration_tests docker_tests help extended_tests
.PHONY: install dev worker-dev compose-up compose-down docker-build docker-run docker-stop deploy logs health clean

# Configuration
PROJECT_ID := anim-482714
REGION := us-central1
SERVICE_NAME := animai-api
IMAGE_NAME := animai
REPO_NAME := animai-repo
IMAGE_URL := $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(REPO_NAME)/$(IMAGE_NAME):latest

# Colors
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

# Default target executed when no arguments are given to make.
all: help

# Define a variable for the test file path.
TEST_FILE ?= tests/unit_tests/

# ============================================
# LOCAL DEVELOPMENT
# ============================================
install:
	@echo "$(GREEN)Installing dependencies...$(NC)"
	pip install -r requirements.txt

dev:
	@echo "$(GREEN)Starting local development server...$(NC)"
	PYTHONPATH=src uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

worker-dev:
	@echo "$(GREEN)Starting manim-worker locally...$(NC)"
	uvicorn app:app --app-dir manim-worker --reload --host 0.0.0.0 --port 8080

compose-up:
	@echo "$(GREEN)Starting API + manim-worker with Docker Compose...$(NC)"
	docker compose up --build

compose-down:
	@echo "$(YELLOW)Stopping Docker Compose stack...$(NC)"
	docker compose down

dev-port:
	@echo "$(GREEN)Starting on port $(PORT)...$(NC)"
	PYTHONPATH=src uvicorn src.api.main:app --reload --host 0.0.0.0 --port $(PORT)

# ============================================
# TESTING
# ============================================
test:
	python -m pytest $(TEST_FILE)

integration_tests:
	python -m pytest tests/integration_tests 

test_watch:
	python -m ptw --snapshot-update --now . -- -vv tests/unit_tests

test_profile:
	python -m pytest -vv tests/unit_tests/ --profile-svg

extended_tests:
	python -m pytest --only-extended $(TEST_FILE)

# ============================================
# LINTING AND FORMATTING
# ============================================

# Define a variable for Python and notebook files.
PYTHON_FILES=src/
MYPY_CACHE=.mypy_cache
lint format: PYTHON_FILES=.
lint_diff format_diff: PYTHON_FILES=$(shell git diff --name-only --diff-filter=d main | grep -E '\.py$$|\.ipynb$$')
lint_package: PYTHON_FILES=src
lint_tests: PYTHON_FILES=tests
lint_tests: MYPY_CACHE=.mypy_cache_test

lint lint_diff lint_package lint_tests:
	python -m ruff check .
	[ "$(PYTHON_FILES)" = "" ] || python -m ruff format $(PYTHON_FILES) --diff
	[ "$(PYTHON_FILES)" = "" ] || python -m ruff check --select I $(PYTHON_FILES)
	[ "$(PYTHON_FILES)" = "" ] || python -m mypy --strict $(PYTHON_FILES)
	[ "$(PYTHON_FILES)" = "" ] || mkdir -p $(MYPY_CACHE) && python -m mypy --strict $(PYTHON_FILES) --cache-dir $(MYPY_CACHE)

format format_diff:
	ruff format $(PYTHON_FILES)
	ruff check --select I --fix $(PYTHON_FILES)

spell_check:
	codespell --toml pyproject.toml

spell_fix:
	codespell --toml pyproject.toml -w

# ============================================
# DOCKER
# ============================================
docker-build:
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker build -t $(IMAGE_NAME) .
	docker tag $(IMAGE_NAME) $(IMAGE_URL)

docker-run:
	@echo "$(GREEN)Running Docker container...$(NC)"
	docker run -p 8000:8000 --env-file .env --name $(SERVICE_NAME) -d $(IMAGE_NAME)
	@echo "$(GREEN)Container running at http://localhost:8000$(NC)"

docker-stop:
	@echo "$(YELLOW)Stopping container...$(NC)"
	-docker stop $(SERVICE_NAME)
	-docker rm $(SERVICE_NAME)

docker-logs:
	docker logs -f $(SERVICE_NAME)

docker-shell:
	docker exec -it $(SERVICE_NAME) /bin/bash

docker-clean:
	@echo "$(YELLOW)Cleaning Docker images...$(NC)"
	-docker rmi $(IMAGE_NAME)
	-docker rmi $(IMAGE_URL)

# ============================================
# TERRAFORM
# ============================================
tf-init:
	@echo "$(GREEN)Initializing Terraform...$(NC)"
	cd terraform && terraform init

tf-plan:
	@echo "$(GREEN)Planning Terraform changes...$(NC)"
	cd terraform && terraform plan

tf-apply:
	@echo "$(GREEN)Applying Terraform changes...$(NC)"
	cd terraform && terraform apply -lock=false

tf-apply-auto:
	@echo "$(GREEN)Applying Terraform (auto-approve)...$(NC)"
	cd terraform && terraform apply -lock=false -auto-approve

tf-destroy:
	@echo "$(RED)Destroying infrastructure...$(NC)"
	cd terraform && terraform destroy -lock=false

tf-output:
	@cd terraform && terraform output

tf-unlock:
	@echo "$(YELLOW)Removing Terraform locks...$(NC)"
	cd terraform && rm -f .terraform.tfstate.lock.info terraform.tfstate.lock.info

# ============================================
# GCP DEPLOYMENT
# ============================================
gcp-auth:
	@echo "$(GREEN)Authenticating with GCP...$(NC)"
	gcloud auth login
	gcloud auth application-default login
	gcloud auth configure-docker $(REGION)-docker.pkg.dev

push:
	@echo "$(GREEN)Pushing image to Artifact Registry...$(NC)"
	docker push $(IMAGE_URL)

update:
	@echo "$(GREEN)Updating Cloud Run service...$(NC)"
	gcloud run services update $(SERVICE_NAME) \
		--region=$(REGION) \
		--image=$(IMAGE_URL)

deploy: docker-build push update
	@echo "$(GREEN)Deployment complete!$(NC)"
	@make url

deploy-full: docker-build push tf-apply
	@echo "$(GREEN)Full deployment complete!$(NC)"
	@make url

url:
	@echo "$(GREEN)Service URL:$(NC)"
	@cd terraform && terraform output -raw service_url

# ============================================
# MONITORING & LOGS
# ============================================
logs:
	gcloud run services logs read $(SERVICE_NAME) --region=$(REGION) --limit=100

logs-follow:
	gcloud run services logs tail $(SERVICE_NAME) --region=$(REGION)

describe:
	gcloud run services describe $(SERVICE_NAME) --region=$(REGION)

# ============================================
# API TESTING
# ============================================
health:
	@SERVICE_URL=$$(cd terraform && terraform output -raw service_url 2>/dev/null) && \
	echo "$(GREEN)Testing: $$SERVICE_URL/health$(NC)" && \
	curl -s $$SERVICE_URL/health | jq .

test-run:
	@SERVICE_URL=$$(cd terraform && terraform output -raw service_url 2>/dev/null) && \
	echo "$(GREEN)Testing: $$SERVICE_URL/run$(NC)" && \
	curl -s -X POST $$SERVICE_URL/run \
		-H "Content-Type: application/json" \
		-d '{"prompt": "create a simple bouncing ball animation"}' | jq .

test-local:
	@echo "$(GREEN)Testing local health endpoint...$(NC)"
	curl -s http://localhost:8000/health | jq .

test-local-run:
	@echo "$(GREEN)Testing local /run endpoint...$(NC)"
	curl -s -X POST http://localhost:8000/run \
		-H "Content-Type: application/json" \
		-d '{"prompt": "create a bouncing ball"}' | jq .

benchmark:
	@echo "$(GREEN)Running load test (10 requests, 2 concurrent)...$(NC)"
	@SERVICE_URL=$$(cd terraform && terraform output -raw service_url 2>/dev/null) && \
	hey -n 10 -c 2 $$SERVICE_URL/health

# ============================================
# CLEANUP
# ============================================
clean:
	@echo "$(YELLOW)Cleaning local artifacts...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache 2>/dev/null || true

clean-all: clean docker-clean
	@echo "$(GREEN)All cleaned!$(NC)"

# ============================================
# HELP
# ============================================

help:
	@echo ''
	@echo '$(GREEN)AnimAI - Available Commands$(NC)'
	@echo ''
	@echo '$(YELLOW)Local Development:$(NC)'
	@echo '  make install       - Install Python dependencies'
	@echo '  make dev           - Run API locally with hot-reload'
	@echo '  make worker-dev    - Run manim-worker locally with hot-reload'
	@echo '  make compose-up    - Run API and worker together via Docker Compose'
	@echo ''
	@echo '$(YELLOW)Docker:$(NC)'
	@echo '  make docker-build  - Build Docker image'
	@echo '  make docker-run    - Run Docker container locally'
	@echo '  make docker-stop   - Stop running container'
	@echo '  make docker-logs   - View container logs'
	@echo ''
	@echo '$(YELLOW)Terraform/GCP:$(NC)'
	@echo '  make tf-init       - Initialize Terraform'
	@echo '  make tf-plan       - Plan Terraform changes'
	@echo '  make tf-apply      - Apply Terraform changes'
	@echo '  make tf-destroy    - Destroy all infrastructure'
	@echo '  make tf-unlock     - Remove stale Terraform locks'
	@echo ''
	@echo '$(YELLOW)Deployment:$(NC)'
	@echo '  make deploy        - Full deploy (build + push + update)'
	@echo '  make push          - Push image to Artifact Registry'
	@echo '  make update        - Update Cloud Run service'
	@echo '  make url           - Get service URL'
	@echo ''
	@echo '$(YELLOW)Monitoring:$(NC)'
	@echo '  make logs          - View Cloud Run logs'
	@echo '  make logs-follow   - Stream Cloud Run logs'
	@echo '  make describe      - Describe Cloud Run service'
	@echo ''
	@echo '$(YELLOW)Testing:$(NC)'
	@echo '  make health        - Test health endpoint (deployed)'
	@echo '  make test-run      - Test /run endpoint (deployed)'
	@echo '  make test-local    - Test local health endpoint'
	@echo '  make benchmark     - Run load test with hey'
	@echo '  make test          - Run unit tests'
	@echo '  make lint          - Run linters'
	@echo '  make format        - Run code formatters'
	@echo ''
	@echo '$(YELLOW)Cleanup:$(NC)'
	@echo '  make clean         - Clean local artifacts'
	@echo '  make clean-all     - Clean everything including Docker'
