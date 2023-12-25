from fastapi import FastAPI, HTTPException, Depends, Request, Response
import hashlib
import random
from datetime import timedelta
from db import *
from sqlalchemy.orm import Session
import logging
from baseModels import *
from fastapi.responses import JSONResponse
import re


def validate_email(email):  
    if re.match(r"[^@]+@[^@]+\.[^@]+", email):  
        return True  
    return False  

# Configuring logging to record incoming and outgoing requests
logging.basicConfig(filename='app.log', encoding='utf-8', level=logging.DEBUG)

app = FastAPI()

# Middleware to log incoming and outgoing requests. This function is called when any http request is made.
@app.middleware("http")
async def log_requests(request: Request, call_next):
    
    logging.info(f"Incoming {request.method} request from IP: {request.client.host}- Headers: {request.headers}")

    response: Response = await call_next(request)

    if config["APP_ENV"].lower() != "production":
        logging.info(f"Outgoing response to IP: {request.client.host} - Status Code: {response.status_code}")

    return response


def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

# Middleware to check API key for incoming requests. This function is called when any http request is made.
@app.middleware("http")
async def api_middleware(request: Request, call_next):
    api_key = request.headers.get("x-api-key")

    if api_key != config["API_KEY"]:  # Replace with your API key
        raise HTTPException(status_code=401, detail="Invalid API key") 

    response = await call_next(request)
    return response

#handles HTTP requests, to add a success false to the exception.
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "success": False}
    )


#middleware to validate user's token, without decorator because it is not applied to all endpoints
async def user_token_middleware(request: Request, db: Session = Depends(get_db)):
    
    token_key = request.headers.get("user-token")
    exisiting_token = db.query(Token).filter(Token.token == token_key).first()
    if exisiting_token == None:
        raise HTTPException(status_code=401, detail="Invalid user token")
    user = db.query(Customer).filter(Customer.email == exisiting_token.email).first()
    # status = check_user_status(exisiting_token, db)
    if exisiting_token.login_time + timedelta(hours=1) < datetime.utcnow():
        user.status = StatusEnum.Inactive
        db.commit()
    if user.status == StatusEnum.Inactive or user.status == StatusEnum.Trash:
        raise HTTPException(status_code=401, detail="Expired user token")

    
#creates a region
@app.post("/region")
def create_region(region: RegionCreate, db: Session = Depends(get_db)):
    db_region = Region(description=region.description, status="I")
    
    db.add(db_region)
    db.commit()
    db.refresh(db_region)
    return {"success" : True}
    
#middleware to validate a region exists
async def middleware_commune(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    id_reg = body["id_reg"]
    if not isinstance(id_reg, int):
        raise HTTPException(status_code=400, detail="id_reg must be an integer")
    existing_region = db.query(Region).filter(Region.id_reg == id_reg).first()

    if not existing_region:
        raise HTTPException(status_code=400, detail="La region no esta registrada")

#creates a commune, depends on middleware_commune to be executed.
@app.post("/commune", dependencies=[Depends(middleware_commune)])
def create_commune(commune: CommuneCreate, db: Session = Depends(get_db)):
    db_commune = Commune(id_reg=commune.id_reg, description=commune.description, status="I")
    db.add(db_commune)
    db.commit()
    db.refresh(db_commune)
    
    return {"success" : True}

#middleware to validate customer passed on the request body
async def middleware_registration(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    customer = CustomerCreate(**body)

    existing_customer = db.query(Customer).filter(Customer.email == customer.email).first()
    existing_region = db.query(Region).filter(Region.id_reg == customer.id_reg).first()
    existing_commune = db.query(Commune).filter(Commune.id_com == customer.id_com).first()
    existing_entry = db.query(Customer).filter(
        Customer.id_reg == customer.id_reg,
        Customer.id_com == customer.id_com,
        Customer.dni == customer.dni
    ).first()
    

    if existing_entry:
        raise HTTPException(status_code=400, detail="The combination of region, commune, and dni already exists")

    if not existing_region:
        raise HTTPException(status_code=400, detail="The region is not registered")
    else:
        if existing_commune:
            if not existing_commune.id_reg == customer.id_reg:
                
                raise HTTPException(status_code=400, detail="The commune and region do not match")
        else:
            raise HTTPException(status_code=400, detail="The commune is not registered")
    
    if not validate_email(customer.email):
        raise HTTPException(status_code=400, detail="Please enter a valid email")
    
    if existing_customer:
        raise HTTPException(status_code=400, detail="The email provided is already registered")

    request.state.customer = customer 
        
# endpoint to create a new customer, depends on middleware_registration
@app.post("/register", dependencies=[Depends(middleware_registration)])
def register(request: Request ,db: Session = Depends(get_db)):
    customer = request.state.customer  

    db_customer = Customer(
        dni=customer.dni, id_reg=customer.id_reg, id_com=customer.id_com, email=customer.email,
        name=customer.name, last_name=customer.last_name, address=customer.address,
        date_reg=customer.date_registry, status=StatusEnum.Inactive
    )

    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    
    return {"success": True}
    
#middleware to validate the email provided in request body
async def middleware_login(request: Request, db: Session = Depends(get_db)):
        body = await request.json()
        email = body.get('email')
        
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided in request body")

        user = db.query(Customer).filter(Customer.email == email).first()
        token = db.query(Token).filter(Token.token == user.email).first()
        
        if user.status == StatusEnum.Trash:
            raise HTTPException(status_code=400, detail="The email doesn't exist")
        if not user:
            raise HTTPException(status_code=400, detail="Invalid email")
        if token:
            raise HTTPException(status_code=400, detail="Token already exists")
        request.state.user = user  

# endpoint for user login.Creates a session for the user in the form of a token
@app.post("/login", dependencies=[Depends(middleware_login)])
def login(request: Request ,db: Session = Depends(get_db)):
    
    user = request.state.user 
    
    user.status = "A"
    user_region = db.query(Region).filter(Region.id_reg == user.id_reg).first()
    user_region.status = "A"
    user_commune = db.query(Commune).filter(Commune.id_com == user.id_com).first()
    user_commune.status = "A"
    
    login_time = datetime.utcnow()
    token, random_number = generate_token(user.email, login_time)
    
    new_token = Token(email=user.email, token=token, login_time=login_time, random_value=random_number)

    db.add(new_token)
    db.commit()
        
    return {"success": True}

# checks an user status, taking a token as a parameter
def check_user_status(token: Token, db: Session):
    user_to_check =  db.query(Customer).filter(Customer.email == token.email).first()
    user_status = user_to_check.status
    if user_status == StatusEnum.Trash:
        return StatusEnum.Trash
    user_status = StatusEnum.Active
    
    if token.login_time + timedelta(hours=1) < datetime.utcnow():
        user_status = StatusEnum.Inactive
        
    
    user_to_check.status = user_status
    db.commit()
    
    return user_status

# validates an email passed through the request body
async def middleware_delete(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    email = body['email']
    
    user = db.query(Customer).filter(Customer.email == email).first()
    token_check = db.query(Token).filter(Token.email == email).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if token_check is None:
        user.status = StatusEnum.Inactive
        request.state.user = user

        return True
    user_to_delete_status = check_user_status(token_check, db)

    if user_to_delete_status == StatusEnum.Trash:
        raise HTTPException(status_code=400, detail="Registro no existe")


    request.state.user = user

# endpoint to logically eliminate a user from the system, needs a login token and a validation middleware to be executed
@app.delete("/delete_data", dependencies=[Depends(user_token_middleware), Depends(middleware_delete)])
def delete_data(request: Request ,db: Session = Depends(get_db)):
    user = request.state.user

    if user.status == StatusEnum.Inactive or user.status == StatusEnum.Active:
        
        region_to_check = db.query(Customer).filter(and_(
    Customer.id_reg == user.id_reg,
    Customer.status != StatusEnum.Trash,
    Customer.status != StatusEnum.Inactive
)).all()
    
        commune_to_check =  db.query(Customer).filter(and_(
    Customer.id_com == user.id_com,
    Customer.status != StatusEnum.Trash,
    Customer.status != StatusEnum.Inactive
)).all()
        if not len(region_to_check) > 1:
            region_to_check2 =  db.query(Region).filter(Region.id_reg == user.id_reg).first()
            region_to_check2.status = StatusEnum.Inactive
        if not len(commune_to_check) > 1:
            commune_to_check2 =  db.query(Commune).filter(Commune.id_com == user.id_com).first()
            commune_to_check2.status = StatusEnum.Inactive
        user.status = StatusEnum.Trash
        db.commit()

        return {"success": True}
    
    
# generates a random SHA1 token using an email, a login_time and a random number
def generate_token(email: str, login_time: datetime):
    random_number = random.randint(200, 500)
    token = f"{email}-{login_time}-{random_number}"
    h = hashlib.new("SHA1")
    h.update(token.encode())
    token_hash = h.hexdigest()
    
    return token_hash, random_number
    
#middleware to validate an email or dni passed in the request body, so as to later get the customers info
async def middleware_get_customer(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    email = body['email_true']
    dni_email_to_get = body['dni_email']
    
    if email is None or dni_email_to_get is None:
        raise HTTPException(status_code=404, detail="Request body not found")
    if email == "true":
        email_bool = True
    
    if not isinstance(email_bool, bool):
        raise HTTPException(status_code=400, detail="Email_true should be a boolean value")
    if not isinstance(dni_email_to_get, str):
        raise HTTPException(status_code=400, detail="dni or email should be a string")
    
    if email_bool == True:
        
        user = db.query(Customer).filter(Customer.email == dni_email_to_get).first()
    else:
        user = db.query(Customer).filter(Customer.dni == dni_email_to_get).first()

    
    
    if user is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    if user.status != StatusEnum.Active:
        raise HTTPException(status_code=403, detail="Customer is inactive or deleted")
    

    request.state.user = user

#gets info about a user, needs a user token to be executed
@app.get("/get_customer", dependencies=[Depends(user_token_middleware), Depends(middleware_get_customer)])
def get_customer(request: Request):
    user = request.state.user
    response_data = {
        "name": user.name,
        "last_name": user.last_name,
        "address": user.address if user.address else None,
        "region": user.id_reg,
        "commune": user.id_com
    }

    return response_data, {"success": True}
        
