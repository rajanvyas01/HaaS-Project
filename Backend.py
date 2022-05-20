from flask import Flask, redirect, url_for, render_template, request, abort, make_response, jsonify, session
from pymongo import MongoClient, collection
from security import Security
import datetime
import jwt
from functools import wraps#global vars


app = Flask(__name__) 
app.config['SECRET_KEY'] = 'lkdsjflsdkjf3434987dhfdlsjfldksjj'
security = Security(app)
client = ''
client = MongoClient('mongodb+srv://admin:pass123@cluster0.ikzq2.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')


#function used for json web tokens. f is a function
def token_required(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        #pass token through query string 
        
        token = session['token']

        try:
            data = jwt.decode(token, app.config['SECRET_KEY']) #attempt to get token 
            if data['user'] != kwargs['name']:
                raise Exception('wrong name')
        except:
            return root() #redirect to login screen
        
        return f(*args,**kwargs) #return the actual function
    return decorated


#About page for the website
@app.route('/about/<string:name>', methods=['GET','POST'])
@token_required
def about(name):
    return render_template("about.html",user=name)

#processing for hardware set management
@app.route('/projects/<string:name>/<string:project>/hwsets/<string:set>/mod', methods=['GET','POST'])
@token_required
def modifySet(name,project,set):
    #get from database
    db = client['monolith']
    documentHWS = db['hw-sets'].find_one({'set_name':set}) 
    documentPJ = db['projects'].find_one({'projectID':project})
    sets_data = documentPJ['hw-sets']

    if documentHWS == None or documentPJ == None:
        abort(400, 'Record not found') 

    givenVal = int(request.form['myRange'])
    newAvailability = documentHWS['availability']  - (givenVal - sets_data.get(set,0))

    documentPJ['hw-sets'][set] = givenVal
    documentHWS['availability'] = newAvailability

    db['projects'].find_one_and_replace({'projectID':project},documentPJ, upsert=True)
    db['hw-sets'].find_one_and_replace({'set_name':set},documentHWS, upsert=True)

    #redirect to hw sets page  
    return redirect(url_for("hwsPage",name=name,project=project)) 
   

#route to the datasets page, allows the user to download pdf files
@app.route('/dataset/<string:name>')
@token_required
def datasetPage(name):
    return render_template("dataset.html",user = name)

#for sorting the projects page, utilizes query string
@app.route("/sort/projects/<string:name>/<string:status>") 
@token_required
def sortProjectsPage(name,status):
    print(request.url)
    sortMethod = request.args.get('sort') 
    val = "up"
    if sortMethod == "up":
        val = "down"
    elif sortMethod == "down":
        val = ""
    
    return redirect(url_for("projectsPage",name=name, status=status,sort=val))
@app.route('/my-proj/<string:name>/<string:status>')
@token_required
def myProjPage(name, status="blah"):
    db = client['monolith']

    project_names = []
    projectIDs = []
    descriptions = []

    for document in db['projects'].find():
        if name in document['members']:
            project_names.append(document['project_name'])
            projectIDs.append(document['projectID'])
            descriptions.append(document['description'])
    
    return render_template("my-proj.html", user = name, project_names = project_names, projectIDs = projectIDs, descriptions=descriptions, len = len(project_names), status=status)

@app.route('/joinProj/<string:name>', methods=['POST'])
@token_required
def joinProject(name):
    db = client['monolith']

    project_ID = request.form["joinProject_ID"]

    if db['projects'].find({"projectID":project_ID}).count() > 0:
        if db['projects'].find({'members': {'$in': [name]}, "projectID": project_ID}).count() > 0:
            return redirect(url_for("myProjPage", name=name, status='Already joined this project'))
        else:
            db['projects'].update(
                {'projectID': project_ID},
                {'$push': {'members': name}}
                )
            return redirect(url_for("myProjPage", name=name, status='Successfully joined project'))
    
    return redirect(url_for("myProjPage", name=name, status='No project with given project ID found, please try again'))

@app.route('/unsubProj/<string:name>', methods=['POST'])
@token_required
def unsubProject(name):
    db = client['monolith']

    project_ID = request.form["unsubProject_ID"]
    
    if db['projects'].find({"projectID":project_ID}).count() > 0:
        if db['projects'].find({'members': {'$in': [name]}, "projectID": project_ID}).count() > 0:
            db['projects'].update(
                {'projectID': project_ID},
                {'$pull': {'members': name}}
            )
            return redirect(url_for("myProjPage", name=name, status='Succesfully unsubscribed from project'))
        else:
            return redirect(url_for("myProjPage", name=name, status='You have not joined this project'))

    return redirect(url_for("myProjPage", name=name, status='No project with given project ID found, please try again'))

# view, create, and remove projects
@app.route('/projects/<string:name>/<string:status>')
@token_required
def projectsPage(name, status="blah"):
    db = client['monolith']
    
    #declare variables
    docs = [] #list of documents
    project_names = []
    projectIDs = []
    descriptions = []

    for document in db['projects'].find():
        docs.append(document)

    #handle how to sort the documents and display them
    sortMethod = request.args.get('sort')
    if sortMethod == "up":
        docs = sorted(docs,key=lambda x: x['project_name']) 
    elif sortMethod == "down":
        docs = sorted(docs,key=lambda x: x['project_name'], reverse=True) 
        
    #extract parameters
    for document in docs:
        project_names.append(document['project_name'])
        projectIDs.append(document['projectID'])
        descriptions.append(document['description'])



    return render_template("projects.html",user = name, project_names = project_names, projectIDs = projectIDs, descriptions=descriptions, len = len(project_names), status=status)

#attempt to create a project
@app.route('/createProjectAttempt/<string:name>', methods=['POST'])
@token_required
def createProjectAttempt(name):
    db = client['monolith']
    
    project_name = request.form['project_name'] 
    project_ID = request.form['project_ID']
    project_description = request.form['project_description']
    if not project_name:
        return redirect(url_for("projectsPage", name=name, status = 'Project name cannot be empty, please enter project name'))

    if not project_ID:
        return redirect(url_for("projectsPage", name=name, status = 'Project ID cannot be empty, please enter project ID'))

    if not project_description:
        return redirect(url_for("projectsPage", name=name, status = 'Project description cannot be empty, please enter project description'))

    # Check if project name exists
    if db['projects'].find({"project_name":project_name}).count() > 0:
        return redirect(url_for("projectsPage", name=name, status = 'Project with name already exists, please pick new name'))

    # Check if project ID exists
    if db['projects'].find({"projectID":project_ID}).count() > 0:
        return redirect(url_for("projectsPage", name=name, status = 'Project with ID already exists, please pick new ID'))

    #if project name and ID are unique, create new project and route to projectsPage
    members_list = []
    members_list.append(name)
    hw_sets = {'HWSet1':0, 'HWSet2':0}      
    db['projects'].insert_one({
        'description':project_description,
        'hw-sets':hw_sets,
        'project_name':project_name, 
        'projectID':project_ID,
        'members': members_list
    })
    return redirect(url_for("projectsPage",name=name, status="Project added"))


@app.route('/goToProject/<string:name>', methods=['POST'])
@token_required
def goToProjectAttempt(name):
    db = client['monolith']
    
    project_ID = request.form['goToProject_ID']

    # Check if project ID exists, then redirect to project page
    if db['projects'].find({"projectID":project_ID}).count() > 0:
        return redirect(url_for("hwsPage", name=name, project=project_ID))

    #if projectID does not exist, redirect back stating invalid
    return redirect(url_for("projectsPage", name=name, status = 'No project with given project ID found, please try again'))

# view hardware sets and add/release capacity from your project
@app.route('/projects/<string:name>/<string:project>/hwsets')
@token_required
def hwsPage(name,project):
    print(project)
    db = client['monolith']
    names = []
    capacities = []
    availabilites = []
    
    #get all data from hwsets
    for document in db['hw-sets'].find():
        names.append(document['set_name'])
        capacities.append(document['capacity'])
        availabilites.append(document['availability'])

    #project info
    projectDoc = db['projects'].find_one({'projectID':project})
    projectName = projectDoc['project_name']
    projectSets = projectDoc['hw-sets']
    desc = projectDoc['description']


    return render_template("hwsets.html",user = name, names = names, cap = capacities, avl = availabilites, len = len(names),project=project, projectName = projectName, desc=desc, projectSets = projectSets)


#allocating capacity from a hardware set
@app.route('/projects/<string:name>/<string:project>/hwsets/<string:set>')
@token_required
def manageSet(name,project,set):
    print(project)
    db = client['monolith']
    documentHWS = db['hw-sets'].find_one({'set_name':set})
    documentPJ = db['projects'].find_one({'projectID':project})
    
    if documentHWS == None or documentPJ == None:
        abort(400, 'Record not found') 

    cap = documentHWS['capacity']
    avail = documentHWS['availability']
    sets_data = documentPJ['hw-sets']

    curVal = sets_data.get(set,0) #if hardware set not in the database, return 0, else return amount checked out of set
    maxVal = avail + sets_data.get(set,0)

    return render_template("setManage.html",user = name, curVal = curVal, maxVal = maxVal, setName = set, project=project)



#delete an account and return to login
@app.route('/delAcc/<string:name>')
@token_required
def delAcc(name):
    db = client['monolith']
    idNeeded = -1
    
    for document in db['projects'].find():
        if name in document['members']:
            db['projects'].update(
                {'projectID': document['projectID']},
                {'$pull': {'members': name}}
            )

    for document in db['users'].find():
        if security.check_hash(name,document['user']):
            idNeeded = document['_id']
            userdoc = document
            break
    
    db['users'].delete_one({'_id':idNeeded})
    session['token'] = None
    return redirect(url_for("login",status = 'Welcome')) 


#processing for pressing submit button under login form
@app.route('/loginAttempt', methods=['POST'])
def loginAttempt():
    givenUsername = request.form['uname'] 
    givenPassword = request.form['password']

    #add encryption code, code to handle database and check validity
    db = client['monolith']

    #check if user exists
    existing_user = False
    userdoc = None



    for document in db['users'].find():
        if security.check_hash(givenUsername,document['user']):
            existing_user = True
            userdoc = document
            break

    if not existing_user:
        return redirect(url_for("login",status = 'User does not exist, please create a new account')) 
    
    #check password, use bcrypt
    if not security.check_hash(givenPassword,userdoc['pass']):
        return redirect(url_for("login",status = 'Invalid password')) 

    token = jwt.encode({'user':givenUsername, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY']) #token expires after 10 minutes
    session['token'] = token

    
    #if username/password is valid, route to home page
    return redirect(url_for("home",name=givenUsername)) 




#processing for creating a new user
@app.route('/newUser', methods=['POST'])
def newUser():
    givenUsername = request.form['new_uname'] 
    givenPassword = request.form['new_password']
    reenterPassword = request.form['rpassword']

    print(security.get_hashed(givenUsername))


    #handle blank username/password and incorrect re-entered password
    if(len(givenUsername) == 0 or len(givenPassword) == 0 or givenPassword != reenterPassword):
        return redirect(url_for("login",status = 'Username or Password entered incorrectly')) 

    #check if username already exists in the database, route back to login screen in that case
    db = client['monolith']

    #check for existing users
    for document in db['users'].find():
        if security.check_hash(givenUsername,document['user']):
            return redirect(url_for("login",status = 'Already existing user')) 
        

    #valid username/passwrod combo, add to the database after hashing with bcrypt
    hashed_un = security.get_hashed(givenUsername)
    hashed_pw = security.get_hashed(givenPassword)

    dateCreated = str(datetime.datetime.now()).split()[0]
    db['users'].insert_one({'user':hashed_un,'pass':hashed_pw,'date':dateCreated})

    token = jwt.encode({'user':givenUsername, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=20)}, app.config['SECRET_KEY']) #token expires after 10 minutes
    session['token'] = token

    
    #log user in with their new account
    return redirect(url_for("home",name=givenUsername)) 
    
#delete token
@app.route("/logout/<string:name>") 
@token_required
def logout(name):
    session['token'] = None
    return redirect(url_for("login",status = 'Welcome')) 


#redirect / to login
@app.route("/") 
def root():
    return redirect(url_for("login",status = 'Welcome')) 

#login page. status is used to indicate the message that appears below the MONOLITH text.
@app.route("/login/<string:status>") #landing page for website
def login(status):
    return render_template("login.html", validStatement = status)

#home page
@app.route("/home/<string:name>")
@token_required
def home(name):
    return render_template("home.html",user = name)

#my account page
@app.route("/myaccount/<string:name>")
def myaccount(name):
    db = client['monolith']
    userdoc = None
    
    for document in db['users'].find():
        if security.check_hash(name,document['user']):
            userdoc = document
            break
    
    if userdoc == None:
        abort(400, 'Record not found') 
    
    date = userdoc['date']

    return render_template("myaccount.html",user = name,date=date)



if __name__ == "__main__":
    app.run(debug=True)