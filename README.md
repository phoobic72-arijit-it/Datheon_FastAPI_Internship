# Datheon FastAPI Internship

Backend development projects created by **Arijit Jana** as part of the **Datheon FastAPI Internship**.

This repository brings together four tasks covering REST APIs, user authentication, database persistence, background processing, and Docker.

## Internship Tasks

| Task | Project | Focus |
|------|---------|-------|
| 1 | [BookStore API](./Task_1_BookStore/) | CRUD operations, Pydantic validation, filtering, and API documentation |
| 2 | [User Authentication](./Task_2_User_Authentication/) | User registration, login, and token-based authentication |
| 3 | [Database Persistence](./Task_3_Database_Persistence/) | Database integration, data models, and persistent storage |
| 4 | [Background Tasks and Docker](./Task_4_Background_Tasks_Docker/) | Background processing, rate limiting, and container configuration |

## Technologies

- Python
- FastAPI
- Pydantic
- Uvicorn
- JWT authentication
- Database integration
- Docker and Docker Compose
- Git and GitHub

## Getting Started

Each task is a separate project with its own dependencies and setup instructions. Open the relevant task folder and follow its `README.md`.

### Example: Run Task 1 on macOS

Open a terminal in the repository folder and run:

```bash
cd Task_1_BookStore

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -r requirements.txt

python -m uvicorn main:app --reload
```

Once the server starts, open:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

Press **Control + C** in the terminal to stop the server.

For Tasks 2–4, check the individual READMEs for environment variables, database configuration, and background services before starting.

## Learning Outcomes

- Build and organize REST API endpoints.
- Validate request data using Pydantic schemas.
- Return appropriate HTTP responses and errors.
- Implement authentication and protected routes.
- Store and retrieve persistent data.
- Handle work through background processing.
- Configure containerized services with Docker.
- Document projects for setup and review.

## Author

**Arijit Jana**  
BCA Student | Aspiring Backend Developer

GitHub: [phoobic72-arijit-it](https://github.com/phoobic72-arijit-it)

## Acknowledgment

Developed as part of the **Datheon FastAPI Internship**.
