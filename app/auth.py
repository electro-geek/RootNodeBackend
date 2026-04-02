import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from . import models, database, config

# Initialize dynamic credentials from config
if config.settings.firebase_project_id:
    # Check if firebase is already initialized
    try:
        firebase_admin.get_app()
    except ValueError:
        cred_dict = {
            "type": "service_account",
            "project_id": config.settings.firebase_project_id,
            "private_key": config.settings.firebase_private_key,
            "client_email": config.settings.firebase_client_email,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)

async def get_current_user(
    authorization: str = Header(None), 
    db: Session = Depends(database.get_db)
) -> models.User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization Header. Must start with Bearer")

    id_token = authorization.split("Bearer ")[1]

    try:
        # Verify the ID token sent by the client
        decoded_token = firebase_auth.verify_id_token(id_token)
        uid = decoded_token["uid"]
        email = decoded_token.get("email")
        name = decoded_token.get("name")
        picture = decoded_token.get("picture")

        # Check if user exists in DB, if not create
        user = db.query(models.User).filter(models.User.firebase_uid == uid).first()
        if not user:
            # Maybe check if email already exists but linked to different UID?
            # For now, let's just create a new user
            user = models.User(
                firebase_uid=uid,
                email=email,
                display_name=name,
                photo_url=picture,
                tier="User"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")

async def get_optional_user(
    authorization: str = Header(None), 
    db: Session = Depends(database.get_db)
) -> models.User | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        return await get_current_user(authorization, db)
    except:
        return None
