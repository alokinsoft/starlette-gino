import gino
import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from starlette_gino.middleware import DatabaseMiddleware
from .models import db, User

database_url = 'postgresql://test:test@localhost/test'


@pytest.fixture(autouse=True)
async def create_database():
    engine = await gino.create_engine('postgresql://test:test@localhost/test')
    try:
        print("creating Database")
        await db.gino.create_all(engine)
        yield
    finally:
        await db.gino.drop_all(engine)
        await engine.close()


app = Starlette()
app.add_middleware(DatabaseMiddleware, db=db, database_url=database_url)


@app.route('/users', methods=['GET', 'POST'])
async def users(request):
    if request.method == 'GET':
        users = await User.query.gino.all()
        result = []
        for user in users:
            result.append({'id': user.id, 'name': user.name})
        return JSONResponse({'status': 'success', 'message': result})

    if request.method == 'POST':
        body = await request.json()
        result = await User.create(**body)
        return JSONResponse({'status': 'success', 'message': 'Data Saved'})


@pytest.mark.asyncio
async def test_hello():
    print("Hello World")


def test_middleware():
    client = TestClient(app)
    with client:
        response = client.get("/users")
        assert response.status_code == 200
        print(response.json())
        assert response.json() == {'status': 'success', 'message': []}

        response = client.post("/users", json={'name': "Hello", "fullname": "Hello World"})
        assert response.status_code == 200
        print(response.json())
        assert response.json() == {'status': 'success', 'message': 'Data Saved'}

        response = client.get("/users")
        assert response.status_code == 200
        print(response.json())
        assert response.json() == {'status': 'success', 'message': [{'id': 1, 'name': 'Hello'}]}
