from gino import Gino
from starlette.applications import Starlette
from starlette.responses import JSONResponse

from starlette_gino.middleware import DatabaseMiddleware

db = Gino()
app = Starlette(debug=True)
app.add_middleware(DatabaseMiddleware, db=db, database_url='postgresql://test:test@localhost/test')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    fullname = db.Column(db.String)

    def __str__(self):
        return "%s - %s" % (self.id, self.name)


class Address(db.Model):
    __tablename__ = 'addresses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(None, db.ForeignKey('users.id'))
    email_address = db.Column(db.String, nullable=False)


@app.route('/')
def root(request):
    return JSONResponse({'location': 'root'})


@app.route('/users', methods=['GET', 'POST'])
async def users(request):
    if request.method == 'GET':
        users = await User.query.gino.all()
        print(users)
        result = []
        for user in users:
            result.append({'id': user.id, 'name': user.name})
        return JSONResponse({'status': 'success', 'message': result})

    if request.method == 'POST':
        body = await request.json()
        result = await User.create(**body)
        print(result)
        return JSONResponse({'status': 'success', 'message': 'Data Saved'})
