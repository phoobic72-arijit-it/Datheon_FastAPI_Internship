from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field, ConfigDict

app = FastAPI()

books = []
next_book_id = 1


class BookInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid"
    )

    title: str = Field(min_length=1)
    author: str = Field(min_length=1)
    price: float = Field(
        gt=0,
        strict=True,
        allow_inf_nan=False
    )
    stock: int = Field(ge=0, strict=True)


# 2. Display books in the terminal when explicitly called

def Display_books(show_books):

    if not show_books:
        print("No Books Available!")
    else:
        for book in show_books:
            for key, value in book.items():
                print(key, ":", value)
            print()


# 3. book has to find

def find_book(locate_books, target_id):
    for book in locate_books:
        if book["id"] == target_id:
            return book

    return None


# 4. book has to update

def add_book(NewBooks):
    books.append(NewBooks)
    return NewBooks


# 5. book has to update

def Update_Books(UpdateBooks):
    existing_books = find_book(books, UpdateBooks["id"])

    if existing_books is None:
        return None

    existing_books["title"] = UpdateBooks["title"]
    existing_books["author"] = UpdateBooks["author"]
    existing_books["price"] = UpdateBooks["price"]
    existing_books["stock"] = UpdateBooks["stock"]

    return existing_books


# 5. book has to delete

def deleted_Books(target_id):
    existing_books = find_book(books, target_id)

    if existing_books is None:
        return None

    books.remove(existing_books)

    return existing_books


# 7. API: will return all books

#GET-
@app.get("/books", summary="Show all books")
async def get_all_books():
    return books


# 8. API: will return one book at a time

#GET-
@app.get("/books/{book_id}", summary="Show one book")
async def get_book(book_id: int):
    result = find_book(books, book_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    return result


#POST-
@app.post("/books", status_code=201, summary="Create a book")
async def create_book(book: BookInput):
    global next_book_id

    new_book = book.model_dump()
    new_book["id"] = next_book_id
    next_book_id += 1

    result = add_book(new_book)

    return result


#PUT-
@app.put("/books/{book_id}", summary="Replace a book")
async def replace_data(book_id: int, book: BookInput):
    replacement = book.model_dump()
    replacement["id"] = book_id

    result = Update_Books(replacement)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Book Not Found"
        )

    return result


#DELETE-
@app.delete(
    "/books/{book_id}",
    status_code=204,
    summary="Delete a book"
)
async def delete_data(book_id: int):
    result = deleted_Books(book_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Book Not Found"
        )

    return Response(status_code=204)