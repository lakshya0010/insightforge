import requests
import os

API_BASE = os.getenv("API_URL", "http://localhost:8000/api/v1")

def register(name:str, email:str, password: str) ->dict:
    response = requests.post(
        f"{API_BASE}/auth/register",
        json={"name":name, "email":email, "password":password}
    )
    return response.json()

def login(email:str, password:str)->dict:
    response = requests.post(
        f"{API_BASE}/auth/login",
        json={"email":email, "password":password}
    )
    return response.json()

def get_me(token:str) -> dict:
    response = requests.get(
        f"{API_BASE}/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

def get_statements(token:str) -> dict:
    response = requests.get(
        f"{API_BASE}/statements",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

def upload_statement(token:str, file_bytes:bytes, filename:str)->dict:
    response = requests.post(
        f"{API_BASE}/statements/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, file_bytes, "text/csv")}
    )
    return response.json()

def get_statement_detail(token:str, statement_id:int)->dict:
    response = requests.get(
        f"{API_BASE}/statements/{statement_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

