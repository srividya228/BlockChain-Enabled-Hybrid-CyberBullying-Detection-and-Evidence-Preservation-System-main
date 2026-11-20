from flask import Flask, render_template, request, redirect, session
import sqlite3, pickle, os
from werkzeug.utils import secure_filename
import hashlib
from web3 import Web3   # ADDED

app = Flask(__name__)
app.secret_key = "instasafe_secret"

# LOAD ML MODEL
model = pickle.load(open('bullying_model.pkl','rb'))
vectorizer = pickle.load(open('vectorizer.pkl','rb'))

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- BLOCKCHAIN CONNECTION ----------------

ganache_url = "http://127.0.0.1:7545"
web3 = Web3(Web3.HTTPProvider(ganache_url))

# contract address from Remix deployment
contract_address = "0x86cA07C6D491Ad7A535c26c5e35442f3e26e8497"

# ABI
abi =[
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "_username",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "_comment",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "_hash",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "_logicalAddress",
				"type": "string"
			}
		],
		"name": "storeEvidence",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "evidenceCount",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "evidences",
		"outputs": [
			{
				"internalType": "string",
				"name": "username",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "comment",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "hashValue",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "logicalAddress",
				"type": "string"
			},
			{
				"internalType": "uint256",
				"name": "timestamp",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_id",
				"type": "uint256"
			}
		],
		"name": "getEvidence",
		"outputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			},
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
]

# connect contract
contract = web3.eth.contract(address=contract_address, abi=abi)

# Ganache account
account = web3.eth.accounts[0]


# ---------------- AUTH ----------------

@app.route('/')
def home_redirect():
    return redirect('/login')


@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        conn = get_db()   # ✅ MUST BE HERE

        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        try:
            conn.execute(
                "INSERT INTO users (username,email,phone,password,vulgar_count,blocked) VALUES (?,?,?,?,0,0)",
                (username, email, phone, password)
            )
            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return "Username OR Email OR Phone already exists!"

        conn.close()
        return redirect('/login')

    return render_template('register.html')


@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (request.form['username'],request.form['password'])
        ).fetchone()

        conn.close()

        if user:

            if user["blocked"] == 1:
                return render_template("blocked.html")

            session['user'] = user["username"]
            return redirect('/home')

        return "Invalid login credentials"

    return render_template('login.html')


# ---------------- BLOCKCHAIN VIEW ----------------

@app.route('/blockchain')
def blockchain():

    evidence_list = []

    count = contract.functions.evidenceCount().call()

    for i in range(1, count+1):

        e = contract.functions.getEvidence(i).call()

        evidence_list.append({
            "hash": e[0],
            "timestamp": e[1]
        })

    return render_template("blockchain.html", blockchain=evidence_list)


# ---------------- HOME ----------------

@app.route('/home')
def home():

    if 'user' not in session:
        return redirect('/login')

    conn = get_db()

    posts = conn.execute(
        "SELECT * FROM posts ORDER BY id DESC"
    ).fetchall()

    comments = conn.execute(
    "SELECT * FROM comments ",
      # temporarily test with 1
).fetchall()
    conn.close()

    return render_template(
        'home.html',
        posts=posts,
        comments=comments,
        user=session['user']
    )


# ---------------- ADD POST ----------------

@app.route('/add_post', methods=['POST'])
def add_post():

    if 'user' not in session:
        return redirect('/login')

    caption = request.form['caption']
    file = request.files['image']

    filename = secure_filename(file.filename)
    file.save(os.path.join('static', filename))

    vec = vectorizer.transform([caption])
    prediction = model.predict(vec)[0]

    result = "Bullying" if prediction == 1 else "Safe"

    conn = get_db()

    conn.execute(
        "INSERT INTO posts (username,caption,image,result,likes) VALUES (?,?,?,?,0)",
        (session['user'], caption, filename, result)
    )

    conn.commit()
    conn.close()

    return redirect('/home')


# ---------------- LIKE ----------------

@app.route('/like/<int:id>')
def like(id):

    if 'user' not in session:
        return redirect('/login')

    conn = get_db()

    conn.execute(
        "UPDATE posts SET likes = likes + 1 WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/home')


# ---------------- REELS ----------------

@app.route('/reels')
def reels():

    if 'user' not in session:
        return redirect('/login')

    conn = get_db()

    reels = conn.execute(
        "SELECT * FROM reels ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        'reels.html',
        reels=reels,
        user=session['user']
    )


# ---------------- ADD REEL ----------------

@app.route('/add_reel', methods=['POST'])
def add_reel():

    if 'user' not in session:
        return redirect('/login')

    file = request.files['video']
    filename = secure_filename(file.filename)

    file.save(os.path.join('static', filename))

    conn = get_db()

    conn.execute(
        "INSERT INTO reels (username,video) VALUES (?,?)",
        (session['user'], filename)
    )

    conn.commit()
    conn.close()

    return redirect('/reels')


# ---------------- CHAT ----------------

@app.route('/chat', methods=['GET','POST'])
def chat():

    if 'user' not in session:
        return redirect('/login')

    conn = get_db()

    if request.method == 'POST':

        conn.execute(
            "INSERT INTO messages (username,message) VALUES (?,?)",
            (session['user'], request.form['message'])
        )

        conn.commit()

    messages = conn.execute(
        "SELECT * FROM messages ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        'chat.html',
        messages=messages,
        user=session['user']
    )


# ---------------- PROFILE ----------------

@app.route('/profile')
def profile():

    if 'user' not in session:
        return redirect('/login')

    conn = get_db()

    posts = conn.execute(
        "SELECT * FROM posts WHERE username=?",
        (session['user'],)
    ).fetchall()

    conn.close()

    return render_template(
        'profile.html',
        posts=posts,
        user=session['user']
    )


# ---------------- WARNING PAGE ----------------

@app.route('/warning')
def warning():
    return render_template("warning.html")


# ---------------- COMMENT SYSTEM ----------------

@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):

    if 'user' not in session:
        return redirect('/login')

    comment = request.form['comment'].lower()
    user = session['user']

    conn = get_db()

    vec = vectorizer.transform([comment])
    prediction = model.predict(vec)[0]

    vulgar_words = ["stupid","idiot","useless","nasty","worst","hate","loser","you are so stupid",
"nobody likes you",
"you are useless",
"you are such an idiot",
"you are the worst",
"you are a loser",
"everyone hates you",
"you are so dumb",
"you are pathetic",
"you are disgusting",
"you are worthless",
"you are annoying",
"you are a failure",
"you are so ugly",
"you are embarrassing",
"you are trash",
"you are the dumbest person",
"you are so annoying",
"you are nothing",
"you are ridiculous",
"you are a joke",
"you are a waste",
"you are hopeless",
"you are terrible",
"you are a disaster",
"you are so fake",
"you are the worst person",
"you are so bad",
"you are useless at everything",
"you are stupid and annoying",
"you are a complete idiot",
"you are a nobody",
"you are so embarrassing",
"you are always wrong",
"you are so dumb and slow",
"you are an absolute failure",
"you are so irritating",
"you are so pathetic",
"you are such a loser",
"you are a joke to everyone",
"you are totally useless",
"you are a terrible person",
"you are so weak",
"you are the biggest loser",
"you are a waste of time",
"you are so clueless",
"you are horrible",
"you are so bad at everything",
"you are a disgrace",
"you are completely useless",
"you are so embarrassing to watch",
"you are so annoying to everyone",
"you are a total mess",
"you are so fake and annoying",
"you are the worst ever",
"you are nothing special",
"you are a joke to society",
"you are so lame",
"you are the most annoying person",
"you are the dumbest ever",
"you are such a failure",
"you are always messing things up",
"you are a useless person",
"you are such a waste",
"you are terrible at everything",
"you are the worst friend",
"you are a complete mess",
"you are always annoying people",
"you are a pathetic person",
"you are such a disappointment",
"you are not good at anything",
"you are the worst human",
"you are so annoying and dumb",
"you are always embarrassing yourself",
"you are a terrible example",
"you are the worst teammate",
"you are just annoying",
"you are such a clown",
"you are always ruining things",
"you are so embarrassing online",
"you are a fake person",
"you are the worst player",
"you are a bad person",
"you are so irritating to watch",
"you are a useless teammate",
"you are so slow and dumb",
"you are such a problem",
"you are the worst in the group",
"you are so embarrassing in public",
"you are always messing up",
"you are a total loser",
"you are the most useless person",
"you are so cringe",
"you are terrible at this",
"you are a walking joke",
"you are the worst ever seen",
"you are completely pathetic",
"you are such an embarrassment",
"you are not worth anything","you are so annoying",
"you are completely useless",
"you are such a failure",
"you are the worst person ever",
"you are really dumb",
"you are so pathetic",
"you are the biggest idiot",
"you are a total embarrassment",
"you are horrible at everything",
"you are a waste of space",
"you are so boring",
"you are the worst player",
"you are extremely annoying",
"you are a terrible friend",
"you are the worst teammate",
"you are such a clown",
"you are always messing things up",
"you are a complete disaster",
"you are not smart at all",
"you are the dumbest here",
"you are very irritating",
"you are the worst in this group",
"you are such a joke",
"you are not good enough",
"you are terrible at this",
"you are always wrong",
"you are so lazy",
"you are useless in this team",
"you are the worst student",
"you are a total mess",
"you are just annoying everyone",
"you are completely hopeless",
"you are such a disappointment",
"you are always embarrassing yourself",
"you are the most annoying person",
"you are a useless teammate",
"you are the worst worker",
"you are very irritating to watch",
"you are always causing problems",
"you are the weakest here",
"you are such a problem",
"you are the worst leader",
"you are always ruining everything",
"you are not worth listening to",
"you are such a bad example",
"you are the worst performer",
"you are a fake person",
"you are always acting stupid",
"you are extremely useless",
"you are the most pathetic person",
"you are completely ridiculous",
"you are so embarrassing",
"you are such a loser",
"you are the worst friend ever",
"you are a terrible teammate",
"you are always acting dumb",
"you are the worst in class",
"you are a waste of time",
"you are so annoying to everyone",
"you are the most useless here",
"you are terrible at your job",
"you are always making mistakes",
"you are so irritating",
"you are the worst partner",
"you are so stupid sometimes",
"you are always failing",
"you are the biggest problem",
"you are so bad at this",
"you are just a joke",
"you are completely useless here",
"you are a horrible teammate",
"you are always embarrassing the team",
"you are the worst example",
"you are a terrible influence",
"you are very annoying",
"you are such a bad player",
"you are the worst person here",
"you are a weak player",
"you are a useless worker",
"you are the biggest disappointment",
"you are extremely annoying",
"you are a complete joke",
"you are the worst member",
"you are always annoying people",
"you are terrible at everything",
"you are not smart",
"you are the worst competitor",
"you are a failure in everything",
"you are always acting foolish",
"you are the worst candidate",
"you are not capable of anything",
"you are always ruining the mood",
"you are such a useless person",
"you are extremely embarrassing",
"you are the worst performer here",
"you are just a burden",
"you are a terrible student",
"you are always messing up work",
"you are a weak performer",
"you are the most annoying teammate",
"you are the worst participant",
"you are such a bad person",
"you are very unpleasant",
"you are the worst example of a player",
"you are always failing at tasks",
"you are completely incompetent",
"you are such a weak person",
"you are the worst in the room",
"you are a terrible worker",
"you are the worst in the project",
"you are always making things worse",
"you are such an embarrassment",
"you are the worst teammate ever",
"you are always messing things up",
"you are completely ridiculous",
"you are a terrible competitor",
"you are always the problem",
"you are the worst player here",
"you are a bad teammate",
"you are very useless",
"you are the weakest person here",
"you are always embarrassing everyone",
"you are a terrible partner",
"you are always being annoying",
"you are the worst contributor",
"you are extremely incompetent",
"you are such a terrible person",
"you are always acting foolish",
"you are the worst worker here",
"you are the most annoying person here",
"you are always disappointing everyone",
"you are such a bad teammate",
"you are extremely irritating",
"you are the worst member here",
"you are a terrible example",
"you are always causing trouble",
"you are such a useless teammate",
"you are the worst competitor here",
"you are always making things worse",
"you are completely annoying",
"you are the worst partner here",
"you are always embarrassing the group",
"you are such a weak performer",
"you are the worst student here",
"you are always failing tasks",
"you are a terrible participant",
"you are extremely bad at this",
"you are always ruining the work",
"you are the worst helper",
"you are always causing issues",
"you are the most useless teammate",
"you are such an irritating person",
"you are the worst player ever",
"you are always embarrassing the team",
"you are such a bad performer",
"you are extremely annoying to everyone",
"you are the worst contributor here",
"you are always disappointing the team",
"you are such a terrible teammate",
"you are the worst performer ever",
"you are always ruining things",
"you are such a useless member",
"you are the worst participant here",
"you are extremely embarrassing",
"you are always messing up tasks",
"you are the most useless player",
"you are such a terrible worker",
"you are always embarrassing yourself",
"you are the worst worker ever",
"you are extremely disappointing",
"you are such a terrible example",
"you are always ruining the project",
"you are the worst helper here",
"you are extremely annoying to deal with",
"you are always embarrassing the class",
"you are the most useless person here",
"you are such a weak teammate",
"you are always ruining things for everyone",
"you are extremely irritating to watch",
"you are the worst in this team",
"you are always embarrassing the group",
"you are such a terrible participant",
"you are the worst teammate in this group",
"you are always making things worse for everyone",
"you are extremely useless to this team",
"you are the worst contributor to this project",
"you are always disappointing everyone here",
"you are such a terrible teammate in this group","you are stupid",
"you are an idiot",
"you are so dumb",
"nobody likes you",
"you are useless",
"you are the worst",
"you are a loser",
"you are pathetic",
"you are embarrassing",
"you are disgusting",
"you are worthless",
"you are annoying",
"you are a failure",
"you are ugly",
"you are trash",
"you are nothing",
"you are ridiculous",
"you are a joke",
"you are hopeless",
"you are terrible",
"you are a disaster",
"you are fake",
"you are bad at everything",
"you are a nobody",
"you are always wrong",
"you are irritating",
"you are weak",
"you are a waste",
"you are clueless",
"you are horrible",

"you are the dumbest person",
"you are extremely annoying",
"you are such a clown",
"you are always messing things up",
"you are useless at everything",
"you are not good at anything",
"you are a terrible person",
"you are such a disappointment",
"you are a waste of space",
"you are so embarrassing to watch",
"you are the worst friend",
"you are a terrible teammate",
"you are a complete mess",
"you are always embarrassing yourself",
"you are the worst player",
"you are a bad person",
"you are the worst human",
"you are such a problem",
"you are the worst in the group",
"you are a pathetic person",
"you are a terrible example",
"you are the worst teammate",
"you are always ruining things",
"you are a fake person",
"you are terrible at this",
"you are a walking joke",
"you are completely pathetic",
"you are such an embarrassment",
"you are not worth anything",
"you are the most useless person",

"everyone hates you",
"everyone laughs at you",
"nobody wants you here",
"no one cares about you",
"everyone thinks you are dumb",
"everyone knows you are useless",
"everyone avoids you",
"everyone thinks you are a joke",
"everyone is tired of you",
"everyone knows you are pathetic",
"everyone dislikes you",
"everyone thinks you are annoying",
"everyone ignores you",
"everyone knows you are weak",
"everyone thinks you are a failure",
"everyone laughs at your mistakes",
"everyone thinks you are embarrassing",
"everyone knows you are fake",
"everyone sees you as useless",
"everyone knows you are a loser",

"you are so slow",
"you are always failing",
"you are always messing up",
"you never do anything right",
"you ruin everything",
"you always embarrass the team",
"you are always the problem",
"you make everything worse",
"you always cause trouble",
"you always disappoint people",
"you ruin every project",
"you fail at everything",
"you mess up every time",
"you always bring the team down",
"you make everything difficult",
"you always act foolish",
"you always ruin the mood",
"you always make bad decisions",
"you never learn anything",
"you always behave stupidly",

"you are so cringe",
"you are so lame",
"you are completely useless",
"you are so annoying to everyone",
"you are such a bad player",
"you are such a bad teammate",
"you are extremely irritating",
"you are extremely annoying",
"you are extremely dumb",
"you are extremely embarrassing",
"you are extremely useless",
"you are extremely pathetic",
"you are extremely weak",
"you are extremely bad",
"you are extremely disappointing",
"you are extremely clueless",
"you are extremely irritating to watch",
"you are extremely embarrassing online",
"you are extremely annoying to deal with",
"you are extremely bad at this",

"stop talking you idiot",
"nobody wants to hear you",
"just leave already",
"go away nobody wants you here",
"you should stop trying",
"stop embarrassing yourself",
"you should quit",
"you should give up",
"you should stop playing",
"you should stop talking",
"you should stop posting",
"you should stop commenting",
"you should disappear",
"you should just stay quiet",
"you should learn something first",
"you should not even try",
"you should stop ruining things",
"you should stop acting stupid",
"you should stop being annoying",
"you should stop wasting time",

"your work is terrible",
"your work is useless",
"your ideas are stupid",
"your ideas are terrible",
"your ideas are worthless",
"your ideas are ridiculous",
"your performance is awful",
"your performance is embarrassing",
"your work is a joke",
"your work is pathetic",
"your work is embarrassing",
"your work is disappointing",
"your work is useless to everyone",
"your work ruins everything",
"your work is always bad",
"your work is extremely poor",
"your work is embarrassing to see",
"your work is horrible",
"your work is a disaster",
"your work is the worst",

"this is the dumbest thing ever",
"this is the worst thing I have seen",
"this is completely pathetic",
"this is extremely embarrassing",
"this is a terrible effort",
"this is absolutely useless",
"this is completely ridiculous",
"this is the worst performance",
"this is totally embarrassing",
"this is a complete failure",
"this is a huge disappointment",
"this is unbelievably bad",
"this is painfully embarrassing",
"this is extremely poor work",
"this is completely pointless",
"this is the worst attempt ever",
"this is extremely disappointing",
"this is such a bad job",
"this is a total mess",
"this is completely awful",

"you bring nothing to the team",
"you add no value here",
"you are always the weakest link",
"you make everything worse",
"you ruin every opportunity",
"you make the team look bad",
"you embarrass everyone around you",
"you drag everyone down",
"you slow everyone down",
"you make everything harder",
"you are the biggest problem here",
"you make the group worse",
"you ruin the whole project",
"you bring everyone down",
"you always fail the team",
"you are a liability",
"you are a burden",
"you cause more problems than help",
"you ruin every discussion",
"you waste everyone's time",

"you are a terrible competitor",
"you are a terrible partner",
"you are a terrible student",
"you are a terrible worker",
"you are a terrible leader",
"you are a terrible teammate",
"you are a terrible example",
"you are a terrible influence",
"you are a terrible performer",
"you are a terrible participant",
"you are a terrible helper",
"you are a terrible contributor",
"you are a terrible member",
"you are a terrible player",
"you are a terrible speaker",
"you are a terrible thinker",
"you are a terrible communicator",
"you are a terrible planner",
"you are a terrible organizer",
"you are a terrible problem solver",

"you will never succeed",
"you will never improve",
"you will never learn",
"you will never get better",
"you will never be good at this",
"you will never be smart",
"you will never be respected",
"you will never achieve anything",
"you will never be useful",
"you will never be capable",
"you will never be competent",
"you will never be successful",
"you will never be taken seriously",
"you will never be good enough",
"you will never be appreciated",
"you will never be valuable",
"you will never be impressive",
"you will never be respected here",
"you will never be accepted",
"you will never be recognized"]

    is_vulgar = prediction == 1 or any(word in comment for word in vulgar_words)

    user_data = conn.execute(
        "SELECT vulgar_count, blocked FROM users WHERE username=?",
        (user,)
    ).fetchone()

    vulgar_count = user_data["vulgar_count"]
    blocked = user_data["blocked"]

    if blocked == 1:
        conn.close()
        return render_template("blocked.html")

    conn.execute(
        "INSERT INTO comments (post_id, username, comment) VALUES (?,?,?)",
        (post_id, user, comment)
    )

    if is_vulgar:
        vulgar_count += 1
        conn.execute(
        "UPDATE users SET vulgar_count=? WHERE username=?",
        (vulgar_count, user)
    )

    # CREATE HASH
        hash_input = user + comment
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()

    # 🔥 ONLY STORE VULGAR COMMENTS IN BLOCKCHAIN
    try:
        print("🚨 Bullying detected → sending to blockchain")

        tx_hash = contract.functions.storeEvidence(
            user,
            comment,
            hash_value,
            user
        ).transact({
            "from": account
        })

        web3.eth.wait_for_transaction_receipt(tx_hash)

        print("✅ Stored in blockchain")

    except Exception as e:
        print("❌ Blockchain error:", e)    # CONTINUE NORMAL FLOW  ✅ OUTSIDE try/except
    if vulgar_count == 3:
        conn.commit()
        conn.close()
        return redirect('/warning')

    if vulgar_count > 3:
        conn.execute(
            "UPDATE users SET blocked=1 WHERE username=?",
            (user,)
        )

        conn.commit()
        conn.close()
        return render_template("blocked.html")

    conn.commit()
    conn.close()

    return redirect('/home')


# ---------------- RUN APP ----------------

if __name__ == "__main__":
    app.run(debug=True)