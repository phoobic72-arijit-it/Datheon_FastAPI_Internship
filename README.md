# Datheon FastAPI Internship

FastAPI internship projects by **Arijit Jana**. Task 1 implements a BookStore REST API with CRUD operations, Pydantic validation, query filtering, and automatically generated OpenAPI documentation.

## Task 1: BookStore REST API

Manage books containing an automatically generated ID, title, author, price, and stock quantity.

### Features

- List books and retrieve one by ID.
- Create, update, and delete books.
- Generate IDs automatically when creating books.
- Filter books by maximum price.
- Validate inputs and handle missing books.
- Test endpoints through interactive Swagger documentation.

### Technology

Python 3.10+, FastAPI, Pydantic v2, and Uvicorn.

### Installation

**Prerequisites:** Python 3.10 or newer, pip, and a terminal. The commands below are for macOS/Linux.

1. Download or clone this repository from GitHub.
2. Open a terminal in the task folder containing `main.py`. All commands below must be run from that folder.
3. Check your Python version:

```bash
python3 --version
```

4. Create a virtual environment if one does not already exist:

```bash
python3 -m venv .venv
```

5. Activate the environment and install the application dependencies:

```bash
source .venv/bin/activate
python -m pip install fastapi "pydantic>=2,<3" uvicorn
```

### Run locally

Start the development server from the same task folder:

```bash
python -m uvicorn main:app --reload
```

`main:app` selects the `app` object defined in `main.py`. Keep the terminal running while testing. Stop with **Control + C**. The `--reload` option is for local development and restarts the application after source changes.

### API documentation

After starting the server locally:

- [Swagger UI](http://127.0.0.1:8000/docs)
- [OpenAPI JSON schema](http://127.0.0.1:8000/openapi.json)

These addresses refer to the server running on your own computer.

### Endpoints

| Method | Endpoint | Purpose | Success |
| --- | --- | --- | --- |
| GET | `/books` | List books, optionally filtered by `max_price` | 200 |
| GET | `/books/{book_id}` | Retrieve one book | 200 |
| POST | `/books` | Create a book | 201 |
| PUT | `/books/{book_id}` | Replace all four editable fields | 200 |
| DELETE | `/books/{book_id}` | Delete a book; empty response body | 204 |

Missing books return **404**. Invalid request data returns **422**.

### Example request body

Use this body for POST or PUT:

```json
{
  "title": "Backend Development",
  "author": "Avik",
  "price": 799,
  "stock": 16
}
```

POST generates an ID on the server. PUT takes the existing ID from the URL. Do not include `id` in either body. All four editable fields are required.

### Validation

| Input | Rule |
| --- | --- |
| Title and author | Required text; outer spaces are removed; blank values are rejected |
| Price | Finite JSON number greater than zero |
| Stock | Nonnegative JSON integer |
| Additional body fields | Rejected |
| Maximum price filter | Optional finite number greater than zero |

Example: `GET /books?max_price=500` returns books priced at or below 500. No matches returns an empty list with status 200.

### Architecture

The BookStore task uses a single-file application in `main.py`. Its sections separate application setup, input validation, book storage, helper functions, and HTTP endpoints. These are logical responsibilities within one file.

| Component | Implementation | Responsibility |
| --- | --- | --- |
| Server | Uvicorn | Runs the application and receives HTTP requests |
| Application and routes | `app = FastAPI()` and route decorators | Match a request's HTTP method and path to its endpoint function |
| Request validation | Pydantic `BookInput`, `Field`, and `ConfigDict` | Check POST/PUT bodies before book data is changed |
| Business logic | Search, add, update, and delete helper functions | Perform the requested book operation |
| Storage | The `books` list of dictionaries and an ID counter | Keep book records and assign IDs within the running process |
| Responses and documentation | FastAPI, `HTTPException`, and `Response` | Return JSON data or an empty deletion response, report errors, and generate OpenAPI/Swagger docs |

**Example request lifecycle: creating a book**

1. A client or Swagger UI sends a JSON body to `POST /books`.
2. FastAPI selects the POST endpoint and validates the body with `BookInput`.
3. Invalid input produces a 422 response before the endpoint body runs.
4. For valid input, the endpoint converts the model to a dictionary, assigns the next ID, advances the counter, and calls the add helper.
5. The helper appends the dictionary to `books`.
6. The endpoint returns the created record as JSON with status 201.

GET routes read the collection or search by ID. PUT uses the ID in the URL to update an existing book. DELETE removes the matching dictionary. A missing requested book produces 404; successful deletion produces 204 with no body.

Endpoints use `async def`. Their short, in-memory operations do not require `await`. An asynchronous database could be integrated later by awaiting its I/O operations.

### Manual testing

In Swagger UI, select an endpoint, click **Try it out**, enter inputs, and click **Execute**.

1. POST a valid book and copy its returned ID.
2. GET all books and GET that ID to confirm creation.
3. PUT that ID with all four fields and a changed price.
4. GET that ID again to confirm the update.
5. GET books with a maximum-price filter.
6. Submit a blank title, negative price, fractional stock, or missing author; expect 422.
7. DELETE the created ID; expect 204 with an empty body.
8. GET or DELETE the removed ID again; expect 404.

### Storage limitation

Books and the ID counter are stored in memory and reset when the application restarts, including reloads after source edits. Complete a test sequence without editing the source between requests.

## Author

**Arijit Jana** — BCA student learning backend development with Python and FastAPI.

