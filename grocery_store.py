from flask import Flask, request, jsonify, render_template, session
from abc import ABC
import requests
import json
import datetime

app = Flask(__name__)
app.secret_key = '123456' #necessary to use flask session library

class Store(ABC):
    def __init__(self):
        self.goods = []
        self.employees = []
        self.customers = []
        self.sales = []

    def add_good(self, good):
        self.goods.append(good)

    def remove_good(self, good):
        for g in self.goods:
            if g['name'] == good['name']:
                self.goods.remove(g)

    def to_json(self):
        data = {
            "goods": [{'name': g['name'], 'quantity': g['quantity'], 'price': g['price']} for g in self.goods],
            "employees": [{'id': e['id'], 'name': e['username'], 'password': e['password'], 'salary': e['salary']} for e in self.employees],
            "customers": [{'id': c['id'], 'name': c['name'], 'loyalty_points': c['loyalty_points'], 'orders': c['loyalty_points']} for c in self.customers],
            "sales": [sale.to_dict() for sale in self.sales] #unable to serialize sales like others for some reason, I suspect its because it was the only originally empty list
        }
        return json.dumps(data)

class Person(ABC):
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def _get_id(self):
        return self.id

    def _get_name(self):
        return self.name

class Employee(Person):
    def __init__(self, id, name, password, salary):
        super().__init__(id, name)
        self.password = password
        self.salary = salary

    def _get_salary(self):
        return self.salary

class Customer(Person):
    def __init__(self, id, name, points):
        super().__init__(id, name)
        self.points = points

    def get_points(self):
        return self.points

class Good:
    def __init__(self, name, quantity, price):
        self.name = name
        self.quantity = quantity
        self.price = price

    def get_name(self):
        return self.name

    def get_price(self):
        return self.price

class Sale:
    def __init__(self, date, customer, items):
        self.date = date
        self.customer = customer
        self.items = items

    def to_dict(self):
        return {
            "date": self.date.strftime("%Y-%m-%d"),  #convert datetime to string due to serialization error
            "customer": self.customer,
            "items": self.items
        }
    
    def get_date(self):
        return self.date

    def get_customer(self):
        return self.customer

    def get_items(self):
        return self.items

grocery_store = Store()

@app.route('/')
def home():
    response = requests.get("http://127.0.0.1:5000/get_goods")
    if response.status_code == 200:
        items = response.json()['goods']
        return render_template('home.html', items=items)
    else:
        return "Error fetching items from the server."
    
@app.route('/get_goods', methods=['GET'])
def display_goods():
    with open('./info.json', 'r') as file:
        data = json.load(file)
    goods = data['goods']
    return jsonify({'goods': goods}), 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', errors="{'message': ''}")
    
    elif request.method == 'POST':
        with open('info.json', 'r') as file:
            data = json.load(file)
            employees = [Employee(employee['id'], employee['username'], employee['password'], employee['salary']) for employee in data['employees']]
        
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('login.html', errors={'message': 'Missing username or password'})

        for employee in employees:
            if employee.name == username and employee.password == password:
                return render_template('employee_home.html', employee=employee)

        return render_template('login.html', errors={'message': 'Invalid username or password'})

@app.route('/add_good', methods=['GET', 'POST']) #protect this route
def add_good():
    if request.method == 'GET':
        return render_template('manage_goods.html')

    elif request.method == 'POST':
        name = request.form.get('name')
        quantity = int(request.form.get('quantity'))  
        price = float(request.form.get('price'))

        good = Good(name, quantity, price)  

        grocery_store.add_good(good)
        
        with open('info.json', 'r') as file:
            data = json.load(file)
            data['goods'].append(good.__dict__)

        with open('info.json', 'w') as file:
            json.dump(data, file)

        return jsonify({'message': 'Good added successfully'}), 200

@app.route('/remove_good', methods=['POST']) #figure out bug
def remove_good():
    if request.method == 'POST':
        name = request.form.get('name')
        quantity = int(request.form.get('quantity'))
        price = float(request.form.get('price'))
        
        good = Good(name, quantity, price)
        with open('./info.json', 'r') as file:
            data = json.load(file)
            grocery_store.goods = data['goods']

        found = False
        for g in grocery_store.goods:
            if g['name'] == good.name:
                found = True
                grocery_store.remove_good(g)
                break
        
        if not found:
            return jsonify({'message': 'Good not found'}), 404
     
        #updating the info.json file with the modified data
        with open('info.json', 'r') as file:
            data = json.load(file)
            data['goods'] = [{'name': g['name'], 'quantity': g['quantity'], 'price': g['price']} for g in grocery_store.goods]

        #writing the updated data back to the file
        with open('info.json', 'w') as file:
            json.dump(data, file, indent=4)
        
        return jsonify({'message': 'Good removed successfully'}), 200

    
@app.route('/display_customers')
def display_customers():
    response = requests.get("http://127.0.0.1:5000/get_customers")
    if response.status_code == 200:
        customers = response.json()['customers']
        return render_template('customers.html', customers=customers)
    else:
        return "Error fetching items from the server."

@app.route('/get_customers', methods=['GET'])
def get_customers():
    with open('./info.json', 'r') as file:
        data = json.load(file)
    customers = data['customers']
    return jsonify({'customers': customers}), 200

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    items = []

    for key, value in request.form.items():
        if key == 'item_name':
            item_name = value
        elif key == 'item_price':
            item_price = value
        elif key == 'quantity':
            quantity = int(value)
            items.append({'name': item_name, 'quantity': quantity, 'price': item_price})

    # Storing the cart data in session
    session['cart'] = {
        'items': items
    }
    return render_template('cart.html', items=session['items'])

@app.route('/view_cart', methods=['GET'])
def view_cart():
    cart = session.get('cart')
    if not cart:
        return render_template('checkout.html', message='Your cart is empty.')

    items = cart.get('items', [])
    return render_template('cart.html', items=items)

@app.route('/make_purchase', methods=['POST'])
def make_purchase():
    cart = session.get('cart')

    if not cart:
        return render_template('cart.html', message='Cart is empty'), 400

    customer_name = request.form.get('customer_name')
    customer_points = 0
    items = cart['items']

    #retrieving customer from the store
    customer = None
    with open('./info.json', 'r') as file:
        data = json.load(file)
    grocery_store.customers = data['customers']
    grocery_store.goods = data['goods']
    for c in grocery_store.customers:
        if c['name'] == customer_name:
            customer = c
            break

    if customer is None:
        return render_template('checkout.html', message='Customer not found'), 404

    total_amount = 0
    for item in items:
        found = False
        for good in grocery_store.goods:
            if good['name'] == item['name']:
                found = True
                total_amount += good['price'] * item['quantity']
                good['quantity'] -= item['quantity']
                break
        if not found:
            return render_template('checkout.html', message=f"Item '{item['name']}' not found in the store"), 404

    #updating customer's loyalty points based on the purchase amount
    customer_points += total_amount 

    sale = Sale(datetime.datetime.now(), customer_name, items)
    print(sale.customer)
    grocery_store.sales.append(sale)

    #updating customer's information in the store
    for c in grocery_store.customers:
        if c['name'] == customer_name:
            c['loyalty_points'] += customer_points
            c['orders'].append({'order_id': id(sale), 'total_amount': total_amount})
            break

    
    #updating the info.json file with the modified data
        with open('info.json', 'r') as file:
            data = json.load(file)
            data['goods'] = [{'name': g['name'], 'quantity': g['quantity'], 'price': g['price']} for g in grocery_store.goods]
            data['customers'] = [{'id': c['id'], 'name': c['name'], 'loyalty_points': c['loyalty_points'], 'orders': c['orders']} for c in grocery_store.customers]
            data['sales'] = [sale.to_dict() for sale in grocery_store.sales]

        #writing the updated data back to the file
        with open('info.json', 'w') as file:
            json.dump(data, file, indent=4)

    #serializing and saving the updated store data
    response = requests.get("http://127.0.0.1:5000/serialize_store")
    if response.status_code == 200:
        print("Store serialized and saved successfully")
    else:
        print("Failed to serialize and save the store")

    #cart cleared from the session after purchase
    session.pop('cart', None)

    return render_template('checkout.html', message='Purchase made successfully', loyalty_points=customer_points)


@app.route('/serialize_store', methods=['GET'])
def serialize_store():
    return grocery_store.to_json()


if __name__ == '__main__':
    app.run(debug=True)
