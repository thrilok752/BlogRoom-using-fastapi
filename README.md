# The BlogRoom

The BlogRoom is a FastAPI-based blogging platform that allows users to create, manage, and share blog posts. It features secure user authentication, profile management, image uploads, password recovery via email, PostgreSQL database integration, automated testing, Docker containerization, CI/CD pipelines, and Kubernetes deployment.

This project was built while learning FastAPI and further enhanced with database migrations, AWS S3 integration, Docker, CI/CD, and Kubernetes.

---

## Features

### Authentication

- User Registration
- User Login & Logout
- JWT Authentication
- Password Hashing using Argon2

### User Profiles

- Profile Management
- Profile Image Upload
- Profile Image Validation
- Profile Image Resizing
- Amazon S3 Storage

### Password Management

- Password Change
- Password Reset via Email
- Mailtrap Email Service

### Blog Management

- Create Blog Posts
- Update Blog Posts
- Delete Blog Posts
- View Individual Posts
- View Posts by Specific Users
- Pagination

### Database

- PostgreSQL
- SQLAlchemy
- Alembic Migrations

### Testing

- Pytest
- HTTPX
- S3 Mocking

### Code Quality

- Ruff
- uv

### Containerization

- Docker
- Docker Compose

### CI/CD

- GitHub Actions
- Jenkins CI
- Jenkins CD
- Docker Image Publishing

### Kubernetes

- Kubernetes Deployment
- ClusterIP Service
- NGINX Ingress
- Kubernetes Secrets
- Docker Registry Image Pull Secret
- Database Migration Job

---

## Technologies Used

### Backend

- Python
- FastAPI

### Database

- PostgreSQL
- SQLAlchemy
- Alembic

### Authentication

- JWT
- Argon2

### Frontend

- HTML
- CSS
- Jinja2

### Cloud Storage

- Amazon S3
- Boto3

### Email Service

- Mailtrap

### Testing

- Pytest
- HTTPX
- Moto

### Development Tools

- uv
- Ruff

### DevOps

- Docker
- Docker Compose
- GitHub Actions
- Jenkins
- Kubernetes
- NGINX

---

## Project Structure

```text
blogger/
│
├── app/
├── alembic/
├── k8s/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── Jenkinsfile.ci
├── Jenkinsfile.cd
├── pyproject.toml
├── alembic.ini
└── README.md
```

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd blogger
```

### 2. Install uv

```bash
pip install uv
```

### 3. Install Project Dependencies

```bash
uv sync
```

### 4. Configure Environment Variables

Create a `.env` file in the project root and configure the required environment variables for:

- Application
- PostgreSQL
- Amazon S3
- Mailtrap

---

## Running the Project

### Local Development

Start the FastAPI development server:

```bash
fastapi dev main.py
```

The application will be available at:

```text
http://127.0.0.1:8000
```

FastAPI API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

## Database Migrations

Alembic is used for database schema migrations.

Create a migration:

```bash
uv run alembic revision --autogenerate -m "migration message"
```

Apply migrations:

```bash
uv run alembic upgrade head
```

---

## Testing

Run the test suite using:

```bash
uv run pytest
```

---

## Docker

Build the Docker image:

```bash
docker build -t fastapi-app .
```

Run the application:

```bash
docker run -d --name fastapi-app --env-file .env -p 8080:8080 fastapi-app
```

---

## Docker Compose

The project also includes Docker Compose configuration for running the application using containers.

```bash
docker compose up --build
```

Stop the containers:

```bash
docker compose down
```

---

## CI/CD

The project includes CI/CD pipelines using:

- GitHub Actions
- Jenkins

The CI pipeline performs code quality checks and tests.

The Jenkins CD pipeline builds and publishes the Docker image and deploys the application to Kubernetes.

---

## Kubernetes Deployment

The application is deployed to Kubernetes using:

- Kubernetes Deployment
- ClusterIP Service
- NGINX Ingress
- Kubernetes Secrets
- Docker Registry Image Pull Secret
- Alembic Migration Job

Database migrations are executed in Kubernetes before the application deployment is completed.

---

## Deployment

The application was containerized using Docker and deployed using Kubernetes.

The deployment process includes:

- Docker Image Build
- Docker Image Publishing
- Database Migration
- Kubernetes Deployment
- Kubernetes Service
- NGINX Ingress
- Application Health Check

---

## Acknowledgements

This project was built while learning FastAPI and later extended with PostgreSQL, SQLAlchemy, Alembic, Amazon S3, Mailtrap, Docker, CI/CD pipelines, and Kubernetes deployment.

```
