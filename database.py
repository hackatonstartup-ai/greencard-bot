import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                receipt_photo TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                confirmation_number TEXT,
                
                passport_photo_path TEXT,
                last_name TEXT,
                first_name TEXT,
                middle_name TEXT,
                gender TEXT,
                birth_date TEXT,
                birth_city TEXT,
                birth_country TEXT,
                photo_path TEXT,
                
                address_line1 TEXT,
                address_line2 TEXT,
                city TEXT,
                district_state TEXT,
                postal_code TEXT,
                country TEXT,
                live_country TEXT,
                phone_number TEXT,
                email TEXT,
                education_level TEXT,
                marital_status TEXT,
                children_count INTEGER DEFAULT 0,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS spouses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL,
                last_name TEXT,
                first_name TEXT,
                middle_name TEXT,
                birth_date TEXT,
                gender TEXT,
                birth_city TEXT,
                birth_country TEXT,
                photo_path TEXT,
                FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS children (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL,
                child_index INTEGER NOT NULL,
                last_name TEXT,
                first_name TEXT,
                middle_name TEXT,
                birth_date TEXT,
                gender TEXT,
                birth_city TEXT,
                birth_country TEXT,
                photo_path TEXT,
                FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
            )
        """)
        # Check and migrate passport_photo_path if missing
        async with db.execute("PRAGMA table_info(applications)") as cursor:
            columns = [row[1] for row in await cursor.fetchall()]
            if "passport_photo_path" not in columns:
                await db.execute("ALTER TABLE applications ADD COLUMN passport_photo_path TEXT")
        
        await db.commit()

async def add_or_update_user(user_id: int, username: Optional[str], full_name: Optional[str], phone: Optional[str] = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, full_name, phone)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                full_name=excluded.full_name,
                phone=COALESCE(excluded.phone, users.phone)
        """, (user_id, username, full_name, phone))
        await db.commit()

async def create_payment(user_id: int, receipt_photo: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO payments (user_id, receipt_photo, status)
            VALUES (?, ?, 'pending')
        """, (user_id, receipt_photo))
        await db.commit()
        return cursor.lastrowid

async def get_payment(payment_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_latest_pending_payment(user_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM payments
            WHERE user_id = ? AND status = 'pending'
            ORDER BY id DESC LIMIT 1
            """,
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def resolve_payment(payment_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Find payment by id; if DB was wiped (Render ephemeral disk), recover via user_id."""
    payment = await get_payment(payment_id)
    if payment:
        return payment
    if not user_id:
        return None
    pending = await get_latest_pending_payment(user_id)
    if pending:
        return pending
    # Recreate a row so approve/reject can still proceed after a redeploy wipe
    new_id = await create_payment(user_id=user_id, receipt_photo="recovered_after_redeploy")
    return await get_payment(new_id)

async def update_payment_status(payment_id: int, status: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            UPDATE payments SET status = ? WHERE id = ?
        """, (status, payment_id))
        await db.commit()
        return cursor.rowcount > 0

async def has_approved_payment(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT id FROM payments WHERE user_id = ? AND status = 'approved' LIMIT 1
        """, (user_id,)) as cursor:
            return (await cursor.fetchone()) is not None

async def create_application(user_id: int, app_data: Dict[str, Any]) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO applications (
                user_id, passport_photo_path, last_name, first_name, middle_name,
                gender, birth_date, birth_city, birth_country, photo_path,
                address_line1, address_line2, city, district_state,
                postal_code, country, live_country, phone_number,
                email, education_level, marital_status, children_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            app_data.get("passport_photo_path"),
            app_data.get("last_name"),
            app_data.get("first_name"),
            app_data.get("middle_name"),
            app_data.get("gender"),
            app_data.get("birth_date"),
            app_data.get("birth_city"),
            app_data.get("birth_country"),
            app_data.get("photo_path"),
            app_data.get("address_line1"),
            app_data.get("address_line2"),
            app_data.get("city"),
            app_data.get("district_state"),
            app_data.get("postal_code"),
            app_data.get("country"),
            app_data.get("live_country"),
            app_data.get("phone_number"),
            app_data.get("email"),
            app_data.get("education_level"),
            app_data.get("marital_status"),
            app_data.get("children_count", 0)
        ))
        app_id = cursor.lastrowid

        # Insert spouse if present
        spouse = app_data.get("spouse")
        if spouse:
            await db.execute("""
                INSERT INTO spouses (
                    application_id, last_name, first_name, middle_name,
                    birth_date, gender, birth_city, birth_country, photo_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                app_id,
                spouse.get("last_name"),
                spouse.get("first_name"),
                spouse.get("middle_name"),
                spouse.get("birth_date"),
                spouse.get("gender"),
                spouse.get("birth_city"),
                spouse.get("birth_country"),
                spouse.get("photo_path")
            ))

        # Insert children if present
        children = app_data.get("children", [])
        for idx, child in enumerate(children, start=1):
            await db.execute("""
                INSERT INTO children (
                    application_id, child_index, last_name, first_name, middle_name,
                    birth_date, gender, birth_city, birth_country, photo_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                app_id,
                idx,
                child.get("last_name"),
                child.get("first_name"),
                child.get("middle_name"),
                child.get("birth_date"),
                child.get("gender"),
                child.get("birth_city"),
                child.get("birth_country"),
                child.get("photo_path")
            ))

        await db.commit()
        return app_id

async def get_application(app_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM applications WHERE id = ?", (app_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            app = dict(row)

        async with db.execute("SELECT * FROM spouses WHERE application_id = ?", (app_id,)) as cursor:
            spouse_row = await cursor.fetchone()
            app["spouse"] = dict(spouse_row) if spouse_row else None

        async with db.execute("SELECT * FROM children WHERE application_id = ? ORDER BY child_index", (app_id,)) as cursor:
            children_rows = await cursor.fetchall()
            app["children"] = [dict(r) for r in children_rows]

        return app

async def get_all_applications(limit: int = 500) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM applications ORDER BY id DESC LIMIT ?", (limit,)) as cursor:
            rows = await cursor.fetchall()
            apps = [dict(r) for r in rows]

        for app in apps:
            async with db.execute("SELECT * FROM spouses WHERE application_id = ?", (app["id"],)) as cursor:
                spouse_row = await cursor.fetchone()
                app["spouse"] = dict(spouse_row) if spouse_row else None

            async with db.execute("SELECT * FROM children WHERE application_id = ? ORDER BY child_index", (app["id"],)) as cursor:
                ch_rows = await cursor.fetchall()
                app["children"] = [dict(r) for r in ch_rows]

        return apps

async def update_confirmation_code(app_id: int, code: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            UPDATE applications 
            SET confirmation_number = ?, status = 'completed'
            WHERE id = ?
        """, (code, app_id))
        await db.commit()
        return cursor.rowcount > 0

async def get_stats() -> Dict[str, int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM applications") as c:
            total_apps = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM applications WHERE status = 'completed'") as c:
            completed_apps = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM applications WHERE status = 'pending'") as c:
            pending_apps = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            total_users = (await c.fetchone())[0]
            
        return {
            "total_apps": total_apps,
            "completed_apps": completed_apps,
            "pending_apps": pending_apps,
            "total_users": total_users
        }
