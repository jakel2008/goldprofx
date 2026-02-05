from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///activations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# نموذج قاعدة البيانات لمفاتيح التفعيل
class Activation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    license_key = db.Column(db.String(100), unique=True, nullable=False)
    machine_id = db.Column(db.String(100), nullable=False)
    activated = db.Column(db.Boolean, default=False)
    expiry_date = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Activation {self.license_key}>'

# إنشاء قاعدة البيانات
with app.app_context():
    db.create_all()

# واجهة إدارة المفاتيح
admin = Admin(app, name='Activation Admin', template_mode='bootstrap3')
admin.add_view(ModelView(Activation, db.session))

@app.route('/activate', methods=['POST'])
def activate_license():
    data = request.json
    license_key = data.get('license_key')
    machine_id = data.get('machine_id')

    if license_key and machine_id:
        activation = Activation.query.filter_by(license_key=license_key).first()
        
        if activation and not activation.activated:
            activation.machine_id = machine_id
            activation.expiry_date = datetime.now() + timedelta(days=30)  # صلاحية 30 يوم
            activation.activated = True
            db.session.commit()
            return jsonify({'success': True, 'expiry_date': activation.expiry_date.strftime("%Y-%m-%d")}), 200
        elif activation and activation.activated:
            return jsonify({'success': False, 'message': 'License key already activated.'}), 400
        else:
            # إنشاء مفتاح جديد إذا لم يكن موجودًا
            new_activation = Activation(license_key=license_key, machine_id=machine_id, 
                                         expiry_date=datetime.now() + timedelta(days=30), activated=True)
            db.session.add(new_activation)
            db.session.commit()
            return jsonify({'success': True, 'expiry_date': new_activation.expiry_date.strftime("%Y-%m-%d")}), 200
    return jsonify({'success': False, 'message': 'Invalid data.'}), 400

@app.route('/verify', methods=['POST'])
def verify_license():
    data = request.json
    license_key = data.get('license_key')
    machine_id = data.get('machine_id')

    activation = Activation.query.filter_by(license_key=license_key).first()
    
    if activation:
        if activation.machine_id == machine_id:
            if datetime.now() < activation.expiry_date:
                return jsonify({'valid': True, 'expiry_date': activation.expiry_date.strftime("%Y-%m-%d")}), 200
            else:
                return jsonify({'valid': False, 'message': 'License key expired.'}), 400
    return jsonify({'valid': False, 'message': 'Invalid license key or machine ID.'}), 400

if __name__ == '__main__':
    app.run(debug=True)