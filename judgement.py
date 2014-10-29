from flask import Flask, render_template, redirect, request, flash, session, g
import model

app = Flask(__name__)
app.secret_key = "ABC"


@app.before_request
def check_login():
    user_id = session.get('user_id')
    if user_id:
        g.user = model.session.query(model.User).get(user_id)
    else:
        g.user = None

@app.route("/")
def index():
    return render_template("index.html")
    # user_list = model.session.query(model.User).limit(5).all()
    # return render_template("user_list.html", users=user_list)

@app.route("/login_form")
def login_form():
    return render_template("login.html")

@app.route("/signup_form")
def signup_form():
    return render_template("signup_form.html")

@app.route("/signup", methods=["POST"])
def user_signup():
    email = request.form.get("email")
    password = request.form.get("password")
    age = request.form.get("age")
    zipcode = request.form.get("zipcode")

    # check for email
    u = model.session.query(model.User).filter(model.User.email==email).first()

    # if exists, ask if they want to login
    if u:
        flash("User already exists! LOGIN DAMMIT")
        return redirect("/signup_form")
    # if doesn't exist, add user info to database as new user
    else:
        u = model.User()
        u.email = email
        u.password = password
        u.age = age
        u.zipcode = zipcode
        model.session.add(u)
        model.session.commit()
        
        session["user_email"] = u.email
        session["user_id"] = str(u.id)
        print session
        flash("Successfully signed up!")


    return redirect("/")

@app.route("/login", methods=["POST"])
def user_login():
    email = request.form.get("email")
    password = request.form.get("password")
    u = model.session.query(model.User).filter_by(email = email).filter_by(password = password).first()
    if u:
        flash("Login successful")
        session["user_email"] = u.email
        session["user_id"] = str(u.id)
        print session
        return redirect("/")
    else:
        flash("Email/password not valid, please try again.")
        return redirect("/login_form")

@app.route("/logout")
def user_logout():
    session["user_email"] = None
    session["user_id"] = None
    flash("Logout successful")
    print session
    return redirect("/")

@app.route("/get_user_list")
def get_user_list():
    user_list = model.session.query(model.User).limit(10).all()
    extra_user = model.session.query(model.User).filter_by(id=944).first()

    user_list.append(extra_user)
    extra_user = model.session.query(model.User).filter_by(id=945).first()
    user_list.append(extra_user)

    return render_template("user_list.html", users=user_list)

@app.route("/display_user_info")
def display_user_info():
    user = request.args.get("user")
    user_ratings = model.session.query(model.Rating).filter_by(user_id = user).all()

    return render_template("user_info.html", user_ratings = user_ratings, user = user)

@app.route("/get_movie_list")
def get_movie_list():
    movie_list = model.session.query(model.Movie).limit(20).all()
   
    return render_template("movie_list.html", movies=movie_list)

@app.route("/movie/<int:id>")
def view_movie(id):
    movie = model.session.query(model.Movie).get(id)
    ratings = movie.ratings
    rating_nums = []
    user_rating = None
    for r in ratings:
        if r.user_id == g.user.id:
            user_rating = r.rating
        rating_nums.append(r.rating)
    avg_rating = round(float(sum(rating_nums))/len(rating_nums), 1)

    # Prediction code: only predict if the user hasn't rated it
    # user = model.session.query(User).get(session["user_id"])
    prediction = None
    if not user_rating:
        prediction = g.user.predict_rating(movie)
    # End prediction

    # so we can pass to movie_list, which requires a list
    movies = [movie]

    return render_template("movie_list.html", movies=movies, average=avg_rating, user_rating=user_rating, 
        prediction=prediction)

@app.route("/update_movie_rating", methods=["POST"])
def update_movie_rating():
    # user_id in session
    movie_id = request.args.get("movie")
    rating = request.form.get("rating")
    if not rating.isdigit():
        flash("Please a number 1-5")
        return redirect("/get_movie_list")
    user_id = session["user_id"]
    # print movie_id
    # print rating
    rating_record = model.session.query(model.Rating).filter_by(user_id = user_id).filter_by(movie_id = movie_id).first()
    
    if rating_record:
        rating_record.rating = rating
        flash("Your rating has been updated.")
    else:
        r = model.Rating()
        r.user_id = user_id
        r.movie_id = movie_id
        r.rating = rating
        model.session.add(r)
        flash("Your rating has been added.")

    model.session.commit()

    url = "/display_user_info?user=%s" % user_id
    return redirect(url)






if __name__ == "__main__":
    app.run(debug = True)