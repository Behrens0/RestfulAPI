from sqlalchemy import create_engine, and_
from dotenv import dotenv_values
from sqlalchemy.ext.automap import automap_base

config = {
    **dotenv_values(".env.shared"),
    **dotenv_values(".env.secret"),
}

host_port = config["COMBINED"]
passwd = config["DB_PASSWORD"]
user = config["DB_USER"]

SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{user}:{passwd}@{host_port}/mydb"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

Base = automap_base()
Base.prepare(engine, reflect="True")

Customer = Base.classes.customers
Commune = Base.classes.communes
Region = Base.classes.regions
Token = Base.classes.tokens






