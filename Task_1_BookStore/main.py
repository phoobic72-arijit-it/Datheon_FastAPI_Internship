from typing import Optional

from fastapi import FastAPI, HTTPException, Path, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field


app = FastAPI(
    title="BookStore API",
    description="Manage books with validated CRUD operations and query filtering.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Temporary storage: books are lost when the server restarts.
books = []
next_book_id = 1


# 1. Pydantic schemas for requests and responses

class BookInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    title: str = Field(min_length=1, max_length=200, examples=["Python Basics"])
    author: str = Field(min_length=1, max_length=100, examples=["Arijit Jana"])
    price: float = Field(gt=0, strict=True, allow_inf_nan=False, examples=[349.0])
    stock: int = Field(ge=0, strict=True, examples=[14])


class BookOutput(BookInput):
    id: int = Field(gt=0, examples=[1])


class ErrorResponse(BaseModel):
    detail: str


not_found_response = {
    404: {"model": ErrorResponse, "description": "Book not found"}
}


# 2. Display books in the terminal when explicitly called

def Display_books(show_books):
    if not show_books:
        print("No Books Available!")
    else:
        for book in show_books:
            for key, value in book.items():
                print(key, ":", value)
            print()


# 3. Find a book

def find_book(locate_books, target_id):
    for book in locate_books:
        if book["id"] == target_id:
            return book
    return None


# 4. Add a book

def add_book(NewBooks):
    books.append(NewBooks)
    return NewBooks


# 5. Update a book

def Update_Books(UpdateBooks):
    existing_books = find_book(books, UpdateBooks["id"])
    if existing_books is None:
        return None

    existing_books.update(UpdateBooks)
    return existing_books


# 6. Delete a book

def deleted_Books(target_id):
    existing_books = find_book(books, target_id)
    if existing_books is None:
        return None

    books.remove(existing_books)
    return existing_books


# 7. GET: Return all books or filter them using query parameters

@app.get(
    "/books",
    response_model=list[BookOutput],
    summary="Show or filter books",
    tags=["Books"],
)
async def get_all_books(
    title: Optional[str] = Query(
        None, min_length=1, max_length=200, pattern=r"\S",
        description="Case-insensitive partial title match.",
    ),
    author: Optional[str] = Query(
        None, min_length=1, max_length=100, pattern=r"\S",
        description="Case-insensitive partial author match.",
    ),
    min_price: Optional[float] = Query(
        None, ge=0, allow_inf_nan=False,
        description="Minimum price, inclusive.",
    ),
    max_price: Optional[float] = Query(
        None, ge=0, allow_inf_nan=False,
        description="Maximum price, inclusive.",
    ),
    in_stock: Optional[bool] = Query(
        None, description="true: stock > 0; false: stock = 0.",
    ),
):
    """Combine any filters. Return an empty list when no books match."""
    if min_price is not None and max_price is not None:
        if min_price > max_price:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="min_price must be less than or equal to max_price",
            )

    filtered_books = books

    if title is not None:
        filtered_books = [
            book for book in filtered_books
            if title.strip().casefold() in book["title"].casefold()
        ]

    if author is not None:
        filtered_books = [
            book for book in filtered_books
            if author.strip().casefold() in book["author"].casefold()
        ]

    if min_price is not None:
        filtered_books = [
            book for book in filtered_books if book["price"] >= min_price
        ]

    if max_price is not None:
        filtered_books = [
            book for book in filtered_books if book["price"] <= max_price
        ]

    if in_stock is not None:
        filtered_books = [
            book for book in filtered_books
            if (book["stock"] > 0) == in_stock
        ]

    return filtered_books


# 8. GET: Return one book

@app.get(
    "/books/{book_id}",
    response_model=BookOutput,
    responses=not_found_response,
    summary="Show one book",
    tags=["Books"],
)
async def get_book(book_id: int = Path(..., gt=0)):
    result = find_book(books, book_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return result


# 9. POST: Create a book with a server-generated ID

@app.post(
    "/books",
    response_model=BookOutput,
    status_code=status.HTTP_201_CREATED,
    summary="Create a book",
    tags=["Books"],
)
async def create_book(book: BookInput, response: Response):
    global next_book_id

    new_book = book.model_dump()
    new_book["id"] = next_book_id
    next_book_id += 1

    result = add_book(new_book)
    response.headers["Location"] = f"/books/{new_book['id']}"
    return result


# 10. PUT: Replace all editable fields while keeping the same ID

@app.put(
    "/books/{book_id}",
    response_model=BookOutput,
    responses=not_found_response,
    summary="Replace a book",
    tags=["Books"],
)
async def replace_data(book: BookInput, book_id: int = Path(..., gt=0)):
    replacement = book.model_dump()
    replacement["id"] = book_id

    result = Update_Books(replacement)
    if result is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return result


# 11. DELETE: Remove a book and return no response body

@app.delete(
    "/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=not_found_response,
    summary="Delete a book",
    tags=["Books"],
)
async def delete_data(book_id: int = Path(..., gt=0)):
    result = deleted_Books(book_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
