from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
app.config['SECRET_KEY'] = 'your_secret_key'

# 确保数据库目录存在
basedir = os.path.abspath(os.path.dirname(__file__))
db_dir = os.path.join(basedir, 'db')
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

# 初始化資料庫
db = SQLAlchemy(app)

# 定义資料模型
class Payment(db.Model):
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

# 创建数据库表
with app.app_context():
    db.create_all()

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        initialize_default_friends()
    app.run(debug=True)