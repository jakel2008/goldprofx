from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField
from wtforms.validators import DataRequired, Email
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# نموذج قاعدة البيانات
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    activation_key = db.Column(db.String(100), unique=True)

    def __repr__(self):
        return f'<User {self.username}>'

# نموذج تسجيل المستخدم
class RegistrationForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired()])
    email = StringField('البريد الإلكتروني', validators=[DataRequired()])
    payment_amount = DecimalField('مبلغ الدفع', validators=[DataRequired()])
    submit = SubmitField('تسجيل')

@app.route('/', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        payment_amount = form.payment_amount.data

        # قم بمعالجة الدفع هنا (استخدام Stripe أو PayPal)

        # توليد رقم التفعيل
        activation_key = str(uuid.uuid4())

        # إضافة المستخدم إلى قاعدة البيانات
        new_user = User(username=username, email=email, activation_key=activation_key)
        db.session.add(new_user)
        db.session.commit()

        flash('تم التسجيل بنجاح! رقم التفعيل هو: ' + activation_key)
        return redirect(url_for('register'))

    return render_template('register.html', form=form)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # إنشاء قاعدة البيانات
    app.run(debug=True)