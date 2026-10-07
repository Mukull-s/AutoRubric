import asyncio
import os
import getpass
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from autorubric.core.db import AsyncSessionLocal, User
from autorubric.core.security import get_password_hash
from sqlalchemy import select

async def main():
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    
    if not email:
        email = input("Admin Email: ")
    if not password:
        password = getpass.getpass("Admin Password: ")
        
    if not email or not password:
        print("Email and password are required")
        return
        
    email_lower = email.lower()
    
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.email == email_lower)
        user = (await session.execute(stmt)).scalar_one_or_none()
        
        if user:
            print(f"User {email_lower} already exists. Promoting to admin...")
            user.role = "admin"
            user.password_hash = get_password_hash(password)
        else:
            print(f"Creating admin user {email_lower}...")
            user = User(
                email=email_lower,
                password_hash=get_password_hash(password),
                role="admin",
                is_active=True
            )
            session.add(user)
            
        await session.commit()
        print("Admin user ready.")

if __name__ == "__main__":
    asyncio.run(main())
