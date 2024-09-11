from fastapi import FastAPI,HTTPException
import asyncio
from pydantic import BaseModel, EmailStr

app = FastAPI()

# http://127.0.0.1:8000/docs# UI

# CRUD Operation
# post -- Create
# get -- Read
# put -- Update
# delete -- Delete
class User(BaseModel):
    id: int
    name: str
    email: EmailStr  # 使用 EmailStr 進行 email 格式驗證

# 模擬數據庫 -> 可以換成數據庫連線:-> 變成其他形式
users_db = [{
  "id": 41000,
  "name": "Zeny",
  "email": "playboy@example.com"
},
{
  "id": 41001,
  "name": "Tony",
  "email": "fuckboy@example.com"
},
{
  "id": 41002,
  "name": "Tony",
  "email": "fuckboy@example.com"
}
]

@app.post("/users/")
async def create_user(user: User):
    # 確保用戶 ID 唯一
    for u in users_db:
        if u.id == user.id:
            raise HTTPException(status_code=400, detail="User ID already exists")
    users_db.append(user)
    return user

@app.get("/users/{user_id}")
async def read_user(user_id: int):
    for user in users_db:
        if user.get("id") == user_id:
            return f'user name of user_id: {user.get("id")} is {user.get("name")}'
    raise HTTPException(status_code=404, detail="User not found")

@app.put("/users/{user_id}")
async def update_user(user_id: int, updated_user: User):
    for i, user in enumerate(users_db):
        if user.get("id") == user_id:
            users_db[i] = updated_user
            return updated_user
    raise HTTPException(status_code=404, detail="User not found")

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    for i, user in enumerate(users_db):
        if user.id == user_id:
            del users_db[i]
            return {"detail": "User deleted"}
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/wait/")
async def wait_for_some_time():
    await asyncio.sleep(3)  # 模擬長時間運行的任務
    return {"message": "Finished waiting"}