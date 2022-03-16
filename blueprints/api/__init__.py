from quart import Blueprint, render_template, abort, request, redirect
from sqlalchemy import create_engine, text
from quart_discord import requires_authorization

from secrets.secrets import Secrets


blueprint = Blueprint("api", __name__)

engine = create_engine(
    f"mysql+pymysql://{Secrets.dbuname}:{Secrets.dbpassword}@{Secrets.dbhost}/{Secrets.database}", echo=True, future=True)


@blueprint.route('/')
async def index():
    return await render_template("imagine.html", route="open api")


@requires_authorization
@blueprint.post('/<server>')
async def operationFunc(server):
    form_data = await request.form
    operation = form_data.get('operation')
    value = form_data.get('value')
    with engine.connect() as conn:
        rslt = conn.execute(
            text(f"SELECT * FROM set{server} WHERE setting = '{operation}'"))
        settings = rslt.all()
        if len(settings) != 1:
            return abort(400)

        conn.execute(
            text(
                f"REPLACE INTO set{server} (setting,value) VALUES ('{operation}', '{value}')")
        )
        conn.commit()
        return redirect(f"/{server}/dashboard")
