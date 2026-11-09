import asyncio
import psycopg
from datetime import datetime, timedelta
from config import PG_DSN

async def connection():
    return await psycopg.AsyncConnection.connect(PG_DSN)

async def setup_database():
    async with await connection() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS public.users (
                unique_id SERIAL PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                latest_activity TIMESTAMP,
                user_id BIGINT UNIQUE,
                username VARCHAR(255),
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                referrer_id BIGINT,
                balance INT DEFAULT 0,
                total_balance INT DEFAULT 0,
                premium BOOLEAN DEFAULT false,
                expiration_date TIMESTAMP,
                notification BOOLEAN DEFAULT false,
                premium_expired BOOLEAN DEFAULT false,
                premium_start BOOLEAN DEFAULT false,
                access BOOLEAN DEFAULT false,
                admin BOOLEAN DEFAULT false,
                blocked BOOLEAN DEFAULT false,
                block_reason VARCHAR(255)
            );
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS public.subscriptions (
                unique_id SERIAL PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id BIGINT,
                item_name VARCHAR(255),
                ru_name VARCHAR(255),
                rank INT,
                price INT,
                count INT,
                is_less BOOLEAN
            );
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS public.top (
                ru_name varchar(255),
                tag varchar(255),
                min_rank int4,
                min_price_min_rank int4,
                max_rank int4,
                min_price_max_rank int4,
                not_rank int4
            );
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS public.newtop (
                ru_name varchar(255),
                tag varchar(255),
                min_rank int4,
                min_price_min_rank int4,
                max_rank int4,
                min_price_max_rank int4,
                not_rank int4
            );
        ''')

async def add_or_update_user(user_id, username, first_name, last_name, referrer_id):
    async with await connection() as conn:
        result = await conn.execute(
            "INSERT INTO public.users (user_id, username, first_name, last_name, referrer_id) "
            "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (user_id) DO NOTHING RETURNING user_id",
            (user_id, username, first_name, last_name, referrer_id),
        )
        created = await result.fetchone()
        if created is None:
            await conn.execute(
                "UPDATE public.users SET username = %s, first_name = %s, last_name = %s, "
                "latest_activity = NOW() WHERE user_id = %s",
                (username, first_name, last_name, user_id),
            )
        return created is None


async def increment_balance(user_id, amount):
    async with await connection() as conn:
        await conn.execute('''
                UPDATE public.users
                SET balance = balance + %s, total_balance = total_balance + %s
                WHERE user_id = %s
            ''', (amount, amount, user_id))

async def is_user_admin(user_id):
    async with await connection() as conn:
        result = await conn.execute("SELECT admin FROM public.users WHERE user_id = %s", (user_id,))
        row = await result.fetchone()
        return bool(row and row[0])

async def is_user_blocked(user_id):
    async with await connection() as conn:
        result = await conn.execute("SELECT blocked FROM public.users WHERE user_id = %s", (user_id,))
        row = await result.fetchone()
        return bool(row and row[0])

async def is_user_access(user_id):
    async with await connection() as conn:
        result = await conn.execute("SELECT access FROM public.users WHERE user_id = %s", (user_id,))
        row = await result.fetchone()
        return bool(row and row[0])

async def is_user_premium(user_id):
    async with await connection() as conn:
        result = await conn.execute('''
            SELECT premium
            FROM public.users
            WHERE user_id = %s
        ''', (user_id,))
        row = await result.fetchone()
        return bool(row and row[0])

async def get_user_balance(user_id):
    async with await connection() as conn:
        result = await conn.execute('''
            SELECT balance
            FROM public.users
            WHERE user_id = %s
        ''', (user_id,))
        row = await result.fetchone()
        return row[0]

async def get_total_balance(user_id):
    async with await connection() as conn:
        result = await conn.execute('''
            SELECT total_balance
            FROM public.users
            WHERE user_id = %s
        ''', (user_id,))
        row = await result.fetchone()
        return row[0]

async def get_number_of_invited_users(user_id):
    async with await connection() as conn:
        result = await conn.execute('''
            SELECT COUNT(*)
            FROM public.users
            WHERE referrer_id = %s
        ''', (user_id,))
        row = await result.fetchone()
        return row[0]

async def get_registration_date(user_id):
    async with await connection() as conn:
        result = await conn.execute('''
                SELECT created_at
                FROM public.users
                WHERE user_id = %s
            ''', (user_id,))
        row = await result.fetchone()
        date = row[0].strftime('%d.%m.%Y %H:%M')
        return date

async def expiration_date(user_id):
    async with await connection() as conn:
        result = await conn.execute('''
            SELECT expiration_date
            FROM public.users
            WHERE user_id = %s
        ''', (user_id,))
        expiration_date = await result.fetchone()
        if expiration_date[0] is not None:
            date = expiration_date[0].strftime('%d.%m.%Y %H:%M')
            return date
        else:
            return None

async def expiration_date2():
    async with await connection() as conn:
        result = await conn.execute('''
            SELECT user_id, expiration_date, notification, premium_expired, premium_start
            FROM public.users
        ''')
        row = await result.fetchall()
        return row

async def update_premium_status(user_id):
    async with await connection() as conn:
        await conn.execute('''
            UPDATE public.users
            SET premium = False, notification = False, premium_expired = True
            WHERE user_id = %s
        ''', (user_id,))

        await conn.execute('''
            DELETE FROM public.subscriptions
            WHERE user_id = %s
        ''', (user_id,))

        await asyncio.sleep(60)

        await conn.execute('''
            UPDATE public.users
            SET expiration_date = NULL, premium_expired = False
            WHERE user_id = %s
        ''', (user_id,))

async def update_notification_sent2(user_id):
    async with await connection() as conn:
        await conn.execute('''
            UPDATE public.users
            SET notification = True
            WHERE user_id = %s
        ''', (user_id,))

async def update_notification_sent3(user_id):
    async with await connection() as conn:
        await conn.execute('''
            UPDATE public.users
            SET premium_start = False
            WHERE user_id = %s
        ''', (user_id,))

async def search_users_by_query(query):
    async with await connection() as conn:
        result = await conn.execute('''
            SELECT unique_id, created_at, latest_activity, user_id, username, first_name, last_name, referrer_id, balance, total_balance, premium, expiration_date, access, admin, blocked, block_reason
            FROM public.users
            WHERE CAST(user_id AS TEXT) ILIKE %s OR username ILIKE %s
        ''', (f"%{query}%", f"%{query}%"))
        row = await result.fetchall()
        return row

async def unblock_user(user_id):
    async with await connection() as conn:
        await conn.execute('''
            UPDATE public.users
            SET blocked = False
            WHERE user_id = %s
        ''', (user_id,))

async def get_subscriptions(user_id):
    async with await connection() as conn:
        result = await conn.execute('''
            SELECT user_id, ru_name, rank, price, is_less
            FROM public.subscriptions
            WHERE user_id = %s
        ''', (user_id,))
        row = await result.fetchall()
        return row

async def get_subscription_id(user_id, ru_name, rank, price, is_less):
    async with await connection() as conn:
        result = await conn.execute('''
            SELECT unique_id
            FROM public.subscriptions
            WHERE user_id = %s AND ru_name = %s AND rank = %s AND price = %s AND is_less = %s
        ''', (user_id, ru_name, rank, price, is_less))
        row = await result.fetchone()
        return row

async def block_user(user_id, reason):
    async with await connection() as conn:
        await conn.execute('''
            UPDATE public.users
            SET blocked = true, block_reason = %s
            WHERE user_id = %s
        ''', (reason, user_id))

async def add_admin(user_id):
    async with await connection() as conn:
        await conn.execute('''
            UPDATE public.users
            SET admin = true
            WHERE user_id = %s
        ''', (user_id,))

async def remove_admin(user_id):
    async with await connection() as conn:
        await conn.execute('''
            UPDATE public.users
            SET admin = False
            WHERE user_id = %s
        ''', (user_id,))

async def add_access_bot(user_id):
    async with await connection() as conn:
        await conn.execute('''
            UPDATE public.users
            SET access = true
            WHERE user_id = %s
        ''', (user_id,))

async def remove_access_bot(user_id):
    async with await connection() as conn:
        await conn.execute('''
            UPDATE public.users
            SET access = False
            WHERE user_id = %s
        ''', (user_id,))

async def give_premium(user_id):
    async with await connection() as conn:
        await conn.execute('''
            UPDATE public.users
            SET premium = True,
                expiration_date = COALESCE(expiration_date + INTERVAL '30 days', CURRENT_TIMESTAMP + INTERVAL '30 days'),
                premium_expired = False,
                premium_start = True
            WHERE user_id = %s
        ''', (user_id,))

async def delete_from_database_user(user_id):
    async with await connection() as conn:
        await conn.execute('''
            DELETE FROM public.subscriptions
            WHERE user_id = %s
        ''', (user_id,))

        await conn.execute('''
            DELETE FROM public.users
            WHERE user_id = %s
        ''', (user_id,))

async def get_all_users():
    async with await connection() as conn:
            result = await conn.execute('''
                SELECT user_id
                FROM public.users
            ''')
            row = await result.fetchall()
            return row

async def remove_balance_for_sub_and_send_premium(balance, expiration_date, user_id):
    async with await connection() as conn:
        result = await conn.execute(
            "UPDATE public.users SET balance = balance - %s, premium = True, "
            "expiration_date = %s, premium_expired = False, premium_start = True "
            "WHERE user_id = %s AND balance >= %s AND premium = False RETURNING user_id",
            (balance, expiration_date, user_id, balance),
        )
        return await result.fetchone() is not None


async def get_stats():
    async with await connection() as conn:
            result = await conn.execute('''
                SELECT COUNT(*)
                FROM public.users
            ''')
            total_users = await result.fetchone()

            result = await conn.execute('''
                SELECT COUNT(*)
                FROM public.users
                WHERE premium
            ''')
            total_premium_users = await result.fetchone()

            result = await conn.execute('''
                SELECT COUNT(*)
                FROM public.users
                WHERE blocked
            ''')
            total_blocked_users = await result.fetchone()

            result = await conn.execute('''
                SELECT COUNT(*)
                FROM public.users
                WHERE latest_activity >= NOW() - INTERVAL '1 day'
            ''')
            active_24h = await result.fetchone()

            result = await conn.execute('''
                SELECT COUNT(*)
                FROM public.users
                WHERE latest_activity >= NOW() - INTERVAL '7 days'
            ''')
            active_7d = await result.fetchone()

            result = await conn.execute('''
                SELECT COUNT(*)
                FROM public.users
                WHERE latest_activity >= NOW() - INTERVAL '30 days'
            ''')
            active_30d = await result.fetchone()

            return total_users[0], total_premium_users[0], total_blocked_users[0], active_24h[0], active_7d[0], active_30d[0]

async def get_top_all():
    async with await connection() as conn:
        result = await conn.execute('''
            SELECT ru_name, min_rank, min_price_min_rank, max_rank, min_price_max_rank, not_rank
            FROM public.top
            WHERE tag != 'Коллекция'
            ORDER BY GREATEST(min_price_max_rank, min_price_min_rank, not_rank) DESC
            LIMIT 10
        ''')
        row = await result.fetchall()
        return row

async def get_top_mod():
    async with await connection() as conn:
        result = await conn.execute('''
            SELECT ru_name, min_rank, min_price_min_rank, max_rank, min_price_max_rank, not_rank
            FROM public.top
            WHERE tag = 'Мод'
            ORDER BY GREATEST(min_price_max_rank, min_price_min_rank, not_rank) DESC
            LIMIT 5
        ''')
        row = await result.fetchall()
        return row

async def get_top_prime():
    async with await connection() as conn:
        result = await conn.execute('''
            SELECT ru_name, not_rank
            FROM public.top
            WHERE tag = 'Прайм Warframe' or tag = 'Прайм Weapon'
            ORDER BY not_rank DESC
            LIMIT 5
        ''')
        row = await result.fetchall()
        return row

async def get_top_mist():
    async with await connection() as conn:
        result = await conn.execute('''
            SELECT ru_name, min_rank, min_price_min_rank, max_rank, min_price_max_rank
            FROM public.top
            WHERE tag = 'Мистификатор'
            ORDER BY min_price_max_rank DESC, min_price_min_rank DESC
            LIMIT 5
        ''')
        row = await result.fetchall()
        return row

async def get_top_collection():
    async with await connection() as conn:
        result = await conn.execute('''
            SELECT ru_name, min_rank, min_price_min_rank, max_rank, min_price_max_rank, not_rank
            FROM public.top
            WHERE tag = 'Коллекция'
            ORDER BY GREATEST(min_price_max_rank, min_price_min_rank, not_rank) DESC
            LIMIT 5
        ''')
        row = await result.fetchall()
        return row

async def insert_newtop(ru_name, tag, min_rank, min_price_min_rank, max_rank, min_price_max_rank, not_rank):
    async with await connection() as conn:
        await conn.execute('''
            INSERT INTO public.newtop (ru_name, tag, min_rank, min_price_min_rank, max_rank, min_price_max_rank, not_rank)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (ru_name, tag, min_rank, min_price_min_rank, max_rank, min_price_max_rank, not_rank))

async def transfer_data_between_top():
    async with await connection() as conn:
        await conn.execute('TRUNCATE TABLE public.top;')

        await conn.execute('''
            INSERT INTO public.top (ru_name, tag, min_rank, min_price_min_rank, max_rank, min_price_max_rank, not_rank)
            SELECT ru_name, tag, min_rank, min_price_min_rank, max_rank, min_price_max_rank, not_rank
            FROM public.newtop;
        ''')

        await conn.execute('TRUNCATE TABLE public.newtop;')


async def new_subscription(user_id, item_name, ru_name, rank, price, count, is_less):
    async with await connection() as conn:
            principal = await conn.execute(
                "SELECT premium FROM public.users WHERE user_id = %s FOR UPDATE", (user_id,)
            )
            access = await principal.fetchone()
            if access is None or not access[0]:
                return False
            result = await conn.execute('''
                SELECT COUNT(*) FROM public.subscriptions
                WHERE user_id = %s
            ''', (user_id,))
            subscription_count = await result.fetchone()

            if subscription_count[0] >= 4:
                return False

            await conn.execute('''
                INSERT INTO public.subscriptions (user_id, item_name, ru_name, rank, price, count, is_less)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (user_id, item_name, ru_name, rank, price, count, is_less))
            return True

async def get_all_subscriptions():
    async with await connection() as conn:
            result = await conn.execute('''
                SELECT unique_id, created_at, user_id, item_name, ru_name, rank, price, count, is_less
                FROM public.subscriptions
            ''')
            row = await result.fetchall()
            return row

async def get_subscription_details(subscription_id, user_id):
    async with await connection() as conn:
            result = await conn.execute('''
                SELECT user_id, ru_name, rank, price, is_less
                FROM public.subscriptions
                WHERE unique_id = %s AND user_id = %s
            ''', (subscription_id, user_id))
            row = await result.fetchone()
            return row

async def remove_subscriptions(user_id, ru_name, rank, price, is_less):
    async with await connection() as conn:
            await conn.execute('''
                DELETE FROM public.subscriptions
                WHERE user_id = %s AND ru_name = %s AND rank = %s AND price = %s AND is_less = %s
            ''', (user_id, ru_name, rank, price, is_less))
