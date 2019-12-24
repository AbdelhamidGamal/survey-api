from flask import Flask, request, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from database import Users, Survey, survey_schema
from flask_httpauth import HTTPBasicAuth


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://survey:anything@localhost/survey'
db = SQLAlchemy(app)
ma = Marshmallow(app)
auth = HTTPBasicAuth()



@app.route('/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})


@auth.verify_password
def verify_password(username_or_token, password):
    #Try to see if it's a token first
    user_id = Users.verify_auth_token(username_or_token)
    print(user_id)
    if user_id:
        user = db.session.query(Users).filter_by(id= user_id).one()
    else:
        user = db.session.query(Users).filter_by(username= username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@app.route('/api/users', methods = ['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400) # missing arguments
    if db.session.query(Users).filter_by(username = username).first() is not None:
        abort(400) # existing user
    user = Users(username = username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({ 'username': user.username }), 201

@app.route('/survey', methods=["GET","POST"])
@auth.login_required
def survey():
    if request.method == "GET":
        surveys = Survey.query.all()
        result = survey_schema.dump(surveys)
        return {"surveys": result}

    if request.method == "POST":
        data = request.get_json(force=True)
        survey = Survey()
        survey.name = data["name"]
        if data["description"]:
            survey.description = data["description"]
        survey.questions = data["questions"]
        survey.question = data["question"]
        survey.body = data["body"]
        if data["note"]:
            survey.note = data["note"]
        survey.start_date = data["start_date"]
        if data["end_date"]:
            survey.end_date = data["end_date"]
        db.session.add(survey)
        db.session.commit()
        return jsonify({"success": True}), 201



if __name__ == "__main__":
    app.debug = True
    app.run("0.0.0.0")
