from typing import Annotated

from fastapi import FastAPI, Depends, Query, HTTPException
from sqlmodel import SQLModel, Field, Session, create_engine, select

# Define secrets model


class Secret(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    text: str = Field()
    author_name: str = Field(index=True)


URL = 'sqlite:///database.db'
engine = create_engine(URL, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()


@app.on_event('startup')
def start_app():
    create_db_and_tables()


@app.get('/secrets/')
def read_secrets(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=10)] = 10
) -> list[Secret]:
    secrets = session.exec(select(Secret).offset(offset).limit(limit))
    return secrets


@app.get('/secrets/{secret_id}')
def read_secret(secret_id: int, session: SessionDep) -> Secret:
    secret = session.get(Secret, secret_id)
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")
    return secret


@app.post('/secrets/')
def add_secret(secret: Secret, session: SessionDep) -> Secret:
    session.add(secret)
    session.commit()
    session.refresh(secret)
    return secret
