from typing import Annotated, Union
from fastapi import Cookie, HTTPException, Query, WebSocket, status, WebSocketException
import httpx


HEADER_KEY = 'Authorization'


async def get_user(token: str):
    try:
        async with httpx.AsyncClient() as client:
            print('hi')
            resp = await client.get(
                url="http://localhost:8000/auth/users/me/",
                headers={
                    HEADER_KEY: 'JWT ' + token
                }
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        print(e)
    return None


# async def approve_jwt_token(api_key_query: str = Security(api_key_query)):
#     if not api_key_query:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Blank token",
#         )
#     else:
#         return await get_user(api_key_query)


async def approve_jwt_token(
        token: Annotated[Union[str, None], Query()] = None,
        session: Annotated[Union[str, None], Cookie()] = None,
):
    if token:
        return await get_user(token)
    elif session:
        return await get_user(session)
    else:
        return None


async def approve_jwt_token_for_http(
        token: Annotated[Union[str, None], Query()] = None,
        session: Annotated[Union[str, None], Cookie()] = None,
):
    approved_token = await approve_jwt_token(token=token, session=session)
    if approved_token and approved_token.get('id'):
        return str(approved_token.get('id'))
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials!"
        )


async def approve_jwt_token_for_ws(
        websocket: WebSocket,
        token: Annotated[Union[str, None], Query()] = None,
        session: Annotated[Union[str, None], Cookie()] = None,
):
    approved_token = await approve_jwt_token(token=token, session=session)
    if approved_token:
        return approved_token
    else:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
        )

# basic_auth = HTTPBasic(auto_error=False)


# def authent(
#     credentials: HTTPBasicCredentials = Depends(basic_auth),
# ):
#     if check_basic_auth_creds(credentials):
#         return True

#     raise HTTPException(status_code=403, detail="invalid user/password provided")


# def check_basic_auth_creds(
#     credentials: HTTPBasicCredentials = Depends(basic_auth),
# ):
#     correct_username = secrets.compare_digest(
#         credentials.username, settings.API_USERNAME
#     )
#     correct_password = secrets.compare_digest(
#         credentials.password, settings.API_PASSWORD
#     )

#     if correct_username and correct_password:
#         return True

#     return False
