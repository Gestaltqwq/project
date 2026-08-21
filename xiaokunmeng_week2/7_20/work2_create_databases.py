import pymysql

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="123456",
    database="graduation_management",
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True
)


cursor = conn.cursor()
sql = "DROP DATABASE IF EXISTS TEST_DATABASE"
cursor.execute(sql)
sql = "CREATE DATABASE IF NOT EXISTS TEST_DATABASE"
cursor.execute(sql)
sql = "SHOW DATABASES"
cursor.execute(sql)
print(cursor.fetchall())
print("数据库创建成功")
cursor.close()
conn.close()