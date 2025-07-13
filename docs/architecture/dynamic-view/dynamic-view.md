# Dynamic view

![Sequence Diagram](/docs/architecture/dynamic-view/sequence.png)

The above sequence diagram shows what happens when a user books a match:

1. User clicks “Book Match” in the frontend.
2. Frontend sends a POST to FastAPI, which first calls the Auth service to validate the token.
3. Upon success, FastAPI writes a new record to PostgreSQL and returns the created match ID.
4. Frontend confirms booking to the user.

**Measured execution time in production**: _127 ms_ 
