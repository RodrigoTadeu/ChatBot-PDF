import mysql.connector

conexao = {
    "host": "localhost",
    "user": "root",
    "password": "3033",
    "database": "chatBot",
}


def connect():
    try:
        conn = mysql.connector.connect(**conexao)
        return conn
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL Database: {e}")
        return None


def create_table():
    conn = connect()
    if conn is None:
        print("Erro ao conectar ao banco de dados")
        return

    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS chatBot_session
                    (id INT AUTO_INCREMENT PRIMARY KEY, 
                    session_id VARCHAR(255), 
                    pdf_text TEXT
                )"""
    )

    conn.commit()
    conn.close()


def create_session(token):
    conn = connect()
    if conn is None:
        print("Erro ao conectar ao banco de dados")
        return

    c = conn.cursor()

    c.execute(
        "INSERT INTO chatBot_session (session_id, pdf_text) VALUES (%s, %s)",
        (token, ""),
    )

    conn.commit()
    conn.close()


def verify_pdf(token):
    conn = connect()
    if conn is None:
        print("Erro ao conectar ao banco de dados")
        return

    c = conn.cursor()

    c.execute("SELECT pdf_text FROM chatBot_session WHERE session_id = %s", (token,))
    row = c.fetchone()

    conn.close()
    return row


def insert_pdf(pdf, token):
    conn = connect()
    if conn is None:
        print("Erro ao conectar ao banco de dados")
        return

    c = conn.cursor()

    c.execute(
        "UPDATE chatBot_session SET pdf_text = %s WHERE session_id = %s", (pdf, token)
    )

    conn.commit()
    conn.close()


def select_pdf(token):
    conn = connect()
    if conn is None:
        print("Erro ao conectar ao banco de dados")
        return

    c = conn.cursor()

    c.execute("SELECT pdf_text FROM chatBot_session WHERE session_id=%s", (token,))
    select = c.fetchone()

    conn.close()
    return select


def delete_session(token):
    conn = connect()
    if conn is None:
        print("Erro ao conectar ao banco de dados")
        return

    c = conn.cursor(token)

    c.execute("DELETE FROM chatBot_session WHERE session_id = %s", (token,))
    conn.commit()

    rowcount = c.rowcount
    conn.close()
    return rowcount


def print_table():
    conn = connect()
    if conn is None:
        print("Erro ao conectar ao banco de dados")
        return

    c = conn.cursor()

    c.execute("SELECT * FROM chatBot_session")
    rows = c.fetchall()

    for row in rows:
        print(row)  # Imprimir cada linha da tabela

    conn.close()
