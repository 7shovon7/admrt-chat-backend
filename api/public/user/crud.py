from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.database.models import User as UserModel
from api.public.user.schemas import UserCreate, UserRead, UserUpdate
from api.utils.logger import logger_config


logger = logger_config(__name__)


async def create_user_in_db(
    user: UserCreate,
    db: Session,
):
    try:
        user_to_db = UserModel(**user.model_dump())
        db.add(user_to_db)
        db.commit()
        db.refresh(user_to_db)
        # return UserRead(**user_to_db.as_dict())
        return user_to_db
    except IntegrityError:
        return None


async def get_user_from_db(
    user_id: str,
    db: Session,
):
    query_result = db.query(UserModel).filter(UserModel.id==user_id).first()
    if query_result:
        print(query_result.conversations)
        return UserRead(**query_result.as_dict())
    return None


async def update_user_info(
    user: UserUpdate,
    db: Session,
):
    q = db.query(UserModel).filter_by(id=user.id).first()
    if q is None:
        return await create_user_in_db(user, db)
    else:
        user_dict = q.as_dict()
        user_to_be_updated = UserUpdate(id=user_dict['id'])
        should_update = False
        for key, value in user_dict.items():
            if key != 'id' and value != getattr(user, key):
                should_update = True
                setattr(user_to_be_updated, key, getattr(user, key))
        if should_update:
            db.bulk_update_mappings(
                UserModel,
                [user_to_be_updated.model_dump().items()]
            )
            db.commit()
        return user
