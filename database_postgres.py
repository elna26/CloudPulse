
import getpass
import psycopg


def test_constraints():
    password = getpass.getpass("Enter PostgreSQL password: ")

    try:
        with psycopg.connect(
            host="localhost",
            port=5432,
            dbname="cloudpulse",
            user="postgres",
            password=password
        ) as connection:

            with connection.cursor() as cursor:

                # Test invalid priority
                try:
                    cursor.execute("""
                        INSERT INTO cloudpulse_jobs
                        (name, priority, status)
                        VALUES (%s, %s, %s);
                    """, ("Invalid priority job", 15, "pending"))

                except psycopg.errors.CheckViolation:
                    print("PASS: Invalid priority rejected!")
                    connection.rollback()

                # Test invalid status
                try:
                    cursor.execute("""
                        INSERT INTO cloudpulse_jobs
                        (name, priority, status)
                        VALUES (%s, %s, %s);
                    """, ("Invalid status job", 2, "unknown"))

                except psycopg.errors.CheckViolation:
                    print("PASS: Invalid status rejected!")
                    connection.rollback()

    except psycopg.Error as error:
        print("Database error:", error)


if __name__ == "__main__":
    test_constraints()
