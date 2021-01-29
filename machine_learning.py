import mysql.connector
from sklearn import tree


#++++++++++++++++++++++++++++++++++++++++++++
#               DATABASE 
#++++++++++++++++++++++++++++++++++++++++++++
def open_connection():
    cnx = 0
    try:
        cnx = mysql.connector.connect(user='majid' , password='majid', 
                                host='127.0.0.1', 
                                database='python')
    except mysql.connector.Error as err:
        print(err)
        exit(1)

    return cnx

def close_connection(cnx):
    cnx.close()

def fetch_data_from_db(cnx):
    cursor = cnx.cursor()

    check_exist_query = 'select weight,storage,battery,brand,model,price from gooshishop;'
    cursor.execute( check_exist_query)

    data = []
    info = []
    for item in cursor:
        data.append(item[0:3])
        info.append(item[3:6])
    
    cursor.close()

    return data,info

#--------------- END DATABASE --------------





cnx = open_connection()

print('start fetch data from db ...')
x,y = fetch_data_from_db(cnx)
print('fetch_data_from_db count=', len(x))

print('start classification ...')
clf = tree.DecisionTreeClassifier()
clf = clf.fit(x, y)


#weight,storage,battery
weight  = int(input('please enter weight(gr): '))
storage = int(input('please enter storage(mb): '))
battery = int(input('please enter battery(ah): '))

question = [[weight, storage, battery]]

#question = [[226,512000,5200]]
answer   = clf.predict( question)
print("question is %s and answer is %s" %(question, answer))

close_connection(cnx)