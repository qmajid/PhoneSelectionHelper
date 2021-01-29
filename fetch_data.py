import mysql.connector
import re
import requests
from bs4 import BeautifulSoup
from time import sleep

#++++++++++++++++++++++++++++++++++++++++++++
#               DATABASE 
#++++++++++++++++++++++++++++++++++++++++++++
#باز کردن کانکشن
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

#چک تکراری نبودن رکورد قبل از درج در بانک اطلاعاتی
def check_duplicate_record(cnx, query_values):
    #print('check_duplicate_record ',query_values)

    cursor = cnx.cursor()

    check_exist_query = 'select count(*) from gooshishop where brand=%s and model=%s and weight=%s and storage=%s and battery=%s;'
    cursor.execute( check_exist_query, query_values[0:5])

    is_exist = False;
    for item in cursor:
        if int(item[0]) > 0 :
            is_exist = True

    cursor.close()
    return is_exist


#درج رکورد در جدول
def insert_to_db(cnx, query_values):
    print("insert_to_db: ",query_values)

    cursor = cnx.cursor()

    query_string =  "insert into gooshishop(brand,model,weight,storage,battery,price) "
    query_string += "values(%s,%s,%s,%s,%s,%s)"

    cursor.execute( query_string, query_values)
    cnx.commit()
    cursor.close()

#بستن کانکشن
def close_connection(cnx):
    cnx.close()




#++++++++++++++++++++++++++++++++++++++++++++
#               WEB SCRAPING 
#++++++++++++++++++++++++++++++++++++++++++++
def remove_space(text):
    output = re.sub(r'[\'\[\],]', r'', str(text))
    return output


#استخراج مقادیر عددی از رشته استخراج شده
def extract_value(input):
    print("extract_value ",input)
    input  = remove_space(input)
    output = re.findall(r'(\d+)', input)
    if len(output) == 0:
        return 0
    if len(output) > 1:
        output = output[0]
    output = remove_space(output)
    return output


#وارد شدن به صفحه مشخصات هر دستگاه برای خواندن اطلاعات آن
def get_to_specefic_page(link, brand, model, price):
    #print("get_to_specefic_page ",link, brand, model, price)
    try:
        r = requests.get(link)
    except:
        print("Can not fetch %s" %(link))
        return False

    if r.status_code != 200:
        print("invalid request ",r.status_code)
        return False
    
    #خواندن اطلاعات اختصاصی هر دستگاه از صفحه اختصاصی آن دستگاه
    soup = BeautifulSoup(r.text, 'html.parser')
    res  = soup.find_all('tr')

    weight = 0
    storage = 0
    battery = 0    
    for d in res:
        title = re.findall('<td\sclass=\"title\">(.+)</td>',           str(d))
        value = re.findall('<td\sclass=\"value\">\n<span>(.+)</span>', str(d))
        if len(title)==0 or len(value)==0:
            continue;

        #print("+++++++ ", title, value)
        title = remove_space(title)
        value = remove_space(value)
        

        if 'وزن' in str(title) :
            weight = int(extract_value(value))

        if 'حافظه داخلی' in str(title):
            storage = int(extract_value(value))
            if 'گیگابایت' in value:
                storage = storage*1000
            if 'ترابایت' in value:
                storage = 1000*1000

        if 'ظرفیت باتری' in str(title):
            battery = int(extract_value(value))


    if (weight>0 and storage>0 and battery>0):
        values = (brand, model, weight, storage, battery, price)
        if check_duplicate_record(cnx, values) == True:
            print('--- DUPLICATE RECORD ---', values)
        else:
            insert_to_db(cnx, values)
    
    return True


#رفتن به صفحه خلاصه اطلاعات گوشی ها
def goshi_shop(page_number):
    #simcard-single/simcard-dualsim/simcard-dualsimnosdcard/in-stock/
    site = 'https://www.gooshishop.com/'
    url  = site + 'category/mobile/orderby-pricedescending/page-'+str(page_number)

    try:
        r = requests.get(url)
    except requests.ConnectionError as err:
        print("Can not fetch %s" %(url))
        print("Error: ",err)
        return False

    if r.status_code != 200:
        print("invalid request")
        return False

    soup = BeautifulSoup(r.text, 'html.parser')
    res  = soup.find_all('div', {'class': 'item-inner'})

    index = 0
    find_tag = False
    for item in res:
        find_tag = True
        #print(item)
        #استخراج لینک اختصاصی هر گوشی
        link = re.findall(r'<a\shref=\"(.+)\">', str(item))
        if len(link) == 0:
            continue
        
        detail_page = site + str(link[0])

        #brand and specification split with '-'
        brand = re.findall(r'<h2 class=\"product-title\">\n<a href=\"/product/gsp.+\">\s*(\w+)\s(.*?)\s*-.*</a>', str(item))
        if len(brand) == 0:
            #dont exist '-' splitor between brand and specification
            brand = re.findall(r'<h2 class=\"product-title\">\n<a href=\"/product/gsp.+\">\s*(\w+)\s(.*)</a>', str(item))

        price = re.findall(r'<div class=\"product-price\">(.+)</div>'   , str(item))
        if len(price) > 0:
            price = str(price).replace('تومان', '').replace(',', '').strip()
            price = int(remove_space(price))
        else:
            price = 0

        print("brand ", brand, price, len(brand))
        # if len(brand) == 0:
        #     print(str(item))

        if len(brand)>0 and len(brand[0]) >=2 :
            if get_to_specefic_page(detail_page, brand[0][0], brand[0][1], price) == False:
                sleep(5)
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        #break
    return find_tag



#++++++++++++++++++++++++++++++++++++++++++++
#               START APP
#++++++++++++++++++++++++++++++++++++++++++++
cnx = open_connection()

for i in range(1, 200):
    print("--------------- PAGE ---------------", i)
    if goshi_shop(i) == False:
        break

close_connection(cnx)