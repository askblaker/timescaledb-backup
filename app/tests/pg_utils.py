from app import main


def insert_demo_data():
    with main.get_psycopg2_conn() as pg_conn:
        with pg_conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE test_table(id integer, test integer);
                """
            )
            cur.execute(
                """
                INSERT INTO test_table(id, test) VALUES (1, 2);
                """
            )
            cur.execute(
                """
                SELECT * FROM test_table;
                """
            )


def delete_demo_data():
    with main.get_psycopg2_conn() as pg_conn:
        with pg_conn.cursor() as cur:
            cur.execute(
                """
                DROP TABLE test_table;
                """
            )
