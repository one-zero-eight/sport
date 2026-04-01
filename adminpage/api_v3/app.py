from fastapi import FastAPI
from fastapi_swagger import patch_fastapi
from starlette.middleware.cors import CORSMiddleware

import api_v3.docs as docs


app = FastAPI(
    title=docs.TITLE,
    summary=docs.SUMMARY,
    description=docs.DESCRIPTION,
    version=docs.VERSION,
    contact=docs.CONTACT_INFO,
    license_info=docs.LICENSE_INFO,
    openapi_tags=docs.TAGS_INFO,
    servers=[
        {'url': "/api/v3", 'description': 'Current'},
        {'url': "https://sport.innopolis.university/api/v3", 'description': 'Production'},
        {'url': "https://stage.sport.innopolis.university/api/v3", 'description': 'Staging'},
    ],
    root_path="/api/v3",
    root_path_in_servers=False,
    generate_unique_id_function=docs.generate_unique_operation_id,
    docs_url=None,
    redoc_url=None,
    swagger_ui_oauth2_redirect_url=None,
)

patch_fastapi(app)

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api_v3.routers.users import router as users_router  # noqa: E402
from api_v3.routers.students import router as students_router  # noqa: E402
from api_v3.routers.info import router as info_router  # noqa: E402
from api_v3.routers.semesters import router as semesters_router  # noqa: E402
from api_v3.routers.groups import router as groups_router  # noqa: E402
from api_v3.routers.trainings import router as trainings_router  # noqa: E402
from api_v3.routers.schedule import router as schedule_router  # noqa: E402
from api_v3.routers.attendance import router as attendance_router  # noqa: E402
from api_v3.routers.fitness_test import router as fitness_test_router  # noqa: E402
from api_v3.routers.self_sport import router as self_sport_router  # noqa: E402
from api_v3.routers.references import router as reference_router  # noqa: E402

app.include_router(users_router)
app.include_router(students_router)
app.include_router(groups_router)
app.include_router(trainings_router)
app.include_router(schedule_router)
app.include_router(attendance_router)
app.include_router(self_sport_router)
app.include_router(fitness_test_router)
app.include_router(reference_router)
app.include_router(semesters_router)
app.include_router(info_router)
