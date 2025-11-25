import mysql.connector

def connectionBD():
    print("ENTRO A LA CONEXION")
    try:
        connection = mysql.connector.connect(
            host="mariadb",      # <-- CAMBIO IMPORTANTE
            port=3306,
            user="basquet",           
            passwd="123cuatro",
            database="proyectog4",
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            raise_on_warnings=True
        )
        if connection.is_connected():
            print("Conexión exitosa a la BD")
            return connection

    except mysql.connector.Error as error:
        print(f"No se pudo conectar: {error}")
