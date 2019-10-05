from starlette.applications import Starlette
from starlette.responses import JSONResponse

from starlette_gino.middleware import DatabaseMiddleware
from .models import db, User

app = Starlette(debug=True)
app.add_middleware(DatabaseMiddleware, db=db, database_url='postgresql://test:test@localhost/test')


@app.route('/')
def root(request):
    return JSONResponse({'location': 'root'})


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
        await User.create(**body)
        return JSONResponse({'status': 'success', 'message': 'Data Saved'})
