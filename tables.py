from post import Postgres


sql = Postgres()


sql.create_table('users', """
    user_id bigint,
    login varchar,
    email varchar,
    password varchar,
    currencies varchar,
    logined bigint
""")
