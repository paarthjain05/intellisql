import sqlite3

connection = sqlite3.connect("data.db")
cursor = connection.cursor()

table = '''
CREATE TABLE Students(name VARCHAR(30), class VARCHAR(10), marks INT, company VARCHAR(30))
'''
cursor.execute(table)

cursor.execute('''insert into Students values('Sijo', 'BTech', 75, 'JSW')''')
cursor.execute('''insert into Students values('Lijo', 'MTech', 69, 'TCS')''')
cursor.execute('''insert into Students values('Rijo', 'BSc', 79, 'WIPRO')''')
cursor.execute('''insert into Students values('Sibin', 'MSc', 89, 'INFOSYS')''')
cursor.execute('''insert into Students values('Isha', 'MCom', 99, 'Cyient')''')

print("the inserted records-")
df = cursor.execute('''select * from Students''')

for row in df:
    print(row)

connection.commit()
connection.close()