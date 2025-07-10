import sqlite3
import csv
from main import *

def connect():
    # DATABASE_URL = os.environ['DATABASE_URL']

    # result = urlparse.urlparse(DATABASE_URL)
    con = sqlite3.connect("FurritDB.db")
    return con

conn = connect()
cursor = conn.cursor()
# with open('AwooFines.csv', 'r') as file:
#     reader = csv.reader(file, delimiter=',')
#     for row in reader:
#         fine = row[0]
#         ID = row[1]
#         username = row[2]
#         fname = row[3]
#         lname = row[4]
#
#         add_current_members(username, ID, fname, lname)
#
#         cursor.execute(f"""UPDATE USERS
#                             SET  awoo_fine = {fine}
#                             WHERE telegram_id = {ID}""")
#         conn.commit()
#
#         print(row)


with open('Quotes.csv', 'r', encoding='utf-8') as file:
    reader = csv.reader(file, delimiter=';')
    # print(reader)
    for row in reader:
        print(row)
        text = row[0]
        chatId = row[1]
        messageId = row[2]
        authoredBy = row[3]
        quotedBy = row[4]
        date = str(row[5])
        nsfw = row[6]

        # cursor.execute(f"""INSERT INTO quotes (Quote_Author,quote,date_issued,issued_by_id,Chat_ID,NSFW)
        #                 VALUES ({authoredBy},{text},{date},{quotedBy},{chatId},{nsfw})""")

        cursor.execute("""
            INSERT INTO quotes (Quote_Author, quote, date_issued, issued_by_id, Chat_ID, NSFW)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (authoredBy, text, date, quotedBy, chatId, nsfw))

        conn.commit()
