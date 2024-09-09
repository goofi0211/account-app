from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import inspect

# 确保数据库目录存在
basedir = os.path.abspath(os.path.dirname(__file__))
db_dir = os.path.join(basedir, 'db')

app = Flask(__name__)

# 配置數據庫 URI
# 本地開發時使用這個
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost/testdb'

# 部署到 Render 時使用這個
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://goofi:RIV7PyN8dqzrESy9bgLCxuYtcb1DHLBa@dpg-crffuitds78s73cmbg70-a/testdb_75h4'

# 如果 DATABASE_URL 以 postgres:// 開頭，需要替換為 postgresql://
if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)

app.config['SECRET_KEY'] = 'your_secret_key'

if not os.path.exists(db_dir):
    os.makedirs(db_dir)

print(db_dir)
# 初始化資料庫
db = SQLAlchemy(app)

# 定义資料模型
class Payment(db.Model):
    __tablename__ = 'payment'  # 明確指定表名
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    payable = db.Column(db.Float, default=0.0)
    paid = db.Column(db.Float, default=0.0)

def initialize_default_friends():
    default_friends = ['goofi', 'panini', 'danzon', 'lon', 'wilson', 'xN', 'konnie']
    for friend in default_friends:
        if not Payment.query.filter_by(name=friend).first():
            new_friend = Payment(name=friend)
            db.session.add(new_friend)
    db.session.commit()
    print("Default friends initialized")


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        if 'add_friend' in request.form:
            new_friend_name = request.form.get('new_friend_name')
            if new_friend_name:
                existing_friend = Payment.query.filter_by(name=new_friend_name).first()
                if not existing_friend:
                    new_friend = Payment(name=new_friend_name)
                    db.session.add(new_friend)
                    db.session.commit()
                    flash(f'成功添加新朋友：{new_friend_name}', 'success')
                else:
                    flash(f'朋友 {new_friend_name} 已存在', 'warning')
        elif 'submit' in request.form:
            payables_friends = request.form.getlist('payables_friend')
            payables_amount = request.form.get('payables_amount')
            if payables_friends and payables_amount:
                payables_amount = float(payables_amount)
                amount_per_friend = payables_amount / len(payables_friends)
                for friend_name in payables_friends:
                    friend = Payment.query.filter_by(name=friend_name).first()
                    if friend:
                        friend.payable += amount_per_friend
                db.session.commit()
                flash(f'成功分配金额：每人 {amount_per_friend:.2f}', 'success')
            else:
                flash('请选择朋友并输入金额', 'warning')
        elif 'clear' in request.form:
            Payment.query.update({Payment.payable: 0, Payment.paid: 0})
            db.session.commit()
            flash('所有记录已清除', 'success')
        elif 'pay' in request.form:
            friend_name = request.form.get('paid_friend')
            paid_amount = request.form.get('paid_amount')
            if friend_name and paid_amount:
                friend = Payment.query.filter_by(name=friend_name).first()
                if friend:
                    paid_amount = float(paid_amount)
                    friend.paid += paid_amount
                    if friend.paid > friend.payable:
                        flash(f'{friend_name} 已超额支付 {friend.paid - friend.payable:.2f}', 'warning')
                    db.session.commit()
                    flash(f'{friend_name} 已支付 {paid_amount:.2f}', 'success')
                else:
                    flash(f'未找到朋友：{friend_name}', 'warning')
            else:
                flash('请选择朋友并输入支付金额', 'warning')
        elif 'reset_database' in request.form:
            Payment.query.delete()
            db.session.commit()
            initialize_default_friends()
            flash('資料庫已重置，並添加了預設朋友', 'success')
        
        return redirect(url_for('home'))

    all_friends = Payment.query.all()
    return render_template("home.html", all_friends=all_friends)

def check_db_structure():
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"現有的表: {tables}")
        if 'payment' in tables:
            columns = [col['name'] for col in inspector.get_columns('payment')]
            print(f"payment 表的列: {columns}")
        else:
            print("payment 表不存在")
            return False
    return True

if __name__ == '__main__':
    print("程序開始執行")
    print("test1")
    
    with app.app_context():
        db.create_all()
        print("數據庫表創建成功")
        
        if not check_db_structure():
            print("payment 表不存在，創建表並初始化數據")
            initialize_default_friends()
        else:
            print("使用現有數據庫")
    
    print("準備運行 Flask 應用")
    app.run(debug=True)

# 在應用初始化之後，但在運行之前添加這段代碼
test_file_path = os.path.join(db_dir, 'test_file.txt')
try:
    with open(test_file_path, 'w') as f:
        f.write('Test')
    print(f"Successfully created test file at {test_file_path}")
    os.remove(test_file_path)
    print("Test file removed successfully")
except Exception as e:
    print(f"Error creating test file: {e}")

print(f"Database path: {app.config['SQLALCHEMY_DATABASE_URI']}")
print(f"Database directory: {db_dir}")

