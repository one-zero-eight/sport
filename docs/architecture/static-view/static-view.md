# Static view

![Component Diagram](/docs/architecture/static-view/component.png) 

We organize our code into three main layers — **React frontend**, **FastAPI backend**, and **PostgreSQL** — each in its own module.
- **Coupling**:
    - Frontend ↔ API: loose coupling via HTTP/REST or GraphQL, so you can swap out backend implementations without touching UI code.
    - API ↔ DB: well-defined repository layer isolates SQL queries, minimizing ripple effects from schema changes.
-  **Cohesion**:
    - Each module has a single responsibility (UI, business logic, data storage), which simplifies both development and testing.
- **Maintainability**:
    - Clear separation of concerns and modular structure make it easy to onboard new developers, write unit tests per component, and refactor services independently.  
