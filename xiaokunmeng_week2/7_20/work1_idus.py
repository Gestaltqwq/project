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
print("查操作")
cursor.execute("SELECT * FROM paper")
print(cursor.fetchall())

print("增操作")
sql = "INSERT INTO paper (student_id, title, file_name, file_path, submit_time, status, version, create_time, update_time) VALUES (%s, %s, %s, %s, NOW(), %s, 1, NOW(), NOW())"
data = (5, "毕业论文", "docx", "D:\\code\\2026\\graduation-management-system\\backend-python\\uploads\\papers\\5_docx", "PLAGIARISM_PASSED")
cursor.execute(sql, data)
conn.commit()
print(f"插入成功，记录id:{cursor.lastrowid}")
print("影响的行数：", cursor.rowcount)
cursor.execute("SELECT * FROM paper WHERE student_id = %s",(5,))
print("插入后查到的：", cursor.fetchall())

print("改操作")
sql = "UPDATE paper SET title = %s WHERE student_id = %s"
cursor.execute(sql, ("改后名称",5))
conn.commit()
cursor.execute("SELECT * FROM paper WHERE student_id = %s",(5,))
print("修改后查到的：", cursor.fetchall())

print("删操作")
sql = "DELETE FROM paper WHERE student_id = %s"
cursor.execute(sql, (5,))
conn.commit()
cursor.execute("SELECT * FROM paper WHERE student_id = %s",(5,))
print("删除后查到的：", cursor.fetchall())
cursor.close()
conn.close()