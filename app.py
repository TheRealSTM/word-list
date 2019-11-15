from flask import Flask, flash, request, Response, render_template, redirect, url_for, jsonify
import requests
import itertools
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS, cross_origin
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField
from wtforms.fields.html5 import DecimalRangeField
import json

class WordForm(FlaskForm):
    avail_letters = StringField("Letters")
    avail_pattern = StringField("Pattern")
    select_word_len = BooleanField("Filter by Length")
    word_len = DecimalRangeField("Word Length", default=3)
    submit = SubmitField("Go")



csrf = CSRFProtect()
app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = "row the boats"
app.config["TESTING"] = True
csrf.init_app(app)


def generate_permutations(letters, l, word_set, good_words, filter_len):
    word_list = []
    if filter_len:
        for word_let in itertools.permutations(letters,l):
            search_word = "".join(word_let)
            word_list.append(search_word)
    else:
        for i in range(1, l + 1):
            for word_let in itertools.permutations(letters,i):
                search_word = "".join(word_let)
                word_list.append(search_word)


    app.logger.info("{}".format(word_list))
    for w in word_list:
        if w in good_words:
            word_set.add(w)

def get_good_words_by_size(sorted_good_words, word_len):
    res = set()
    for word in sorted_good_words:
        len_word = len(word)
        if len_word < word_len:
            continue
        elif len_word > word_len:
            break
        if len(word) == word_len:
            res.add(word)
    return res

def has_non_alpha(letters):
    return not all(let.isalpha() for let in letters)

def has_non_pattern(letters):
    return not all(let.isalpha() or let == '.' for let in letters)

def filter_by_pattern(pattern, word_set, sorted_good_words):
    len_pattern = len(pattern)
    for word in sorted_good_words:
        len_word= len(word)
        if len_word < len_pattern:
            continue
        elif len_word > len_pattern:
            break
        i = 0
        while i < len_pattern:
            if pattern[i] == '.' or pattern[i] == word[i]:
                i += 1
            else:
                break
        if i == len_pattern:
            word_set.add(word)


@app.route('/')
@app.route('/index')
def index():
    form = WordForm()
    return render_template("index.html", form=form, name="Sean Montague")


@app.route('/words', methods=['GET', 'POST'])
def list_words():
    word_set, good_words = set(), set()
    sorted_good_words = []
    form = WordForm()
    modal_word = dict()

    if form.validate_on_submit():
        letters = form.avail_letters.data
        pattern = form.avail_pattern.data
        if has_non_alpha(letters) or has_non_pattern(pattern):
            flash('letters must consist of alphabetical characters and patterns must consist of alphabetical characters or .')
            return render_template("index.html", form=form, name="Sean Montague")

        filter_by_len = bool(form.select_word_len.data)
        word_len = int(form.word_len.data)
    else:
        return render_template("index.html", form=form, name="Sean Montague")


    with open('sowpods.txt') as f:
        good_words = set(x.strip().lower() for x in f.readlines())
        sorted_good_words = sorted(list(good_words), key=lambda x: len(x))

    if letters and filter_by_len:
        generate_permutations(letters, word_len, word_set, good_words, filter_by_len)
        word_set = get_good_words_by_size(word_set, word_len)
    elif letters and not filter_by_len:
        generate_permutations(letters, len(letters), word_set, good_words, filter_by_len)
    elif pattern and filter_by_len:
        if len(pattern) != word_len:
            flash('if pattern and filter by length are both selected, they must be the same length!')
            return render_template("index.html", form=form, name="Sean Montague")
        filter_by_pattern(pattern, word_set, sorted_good_words)
    elif pattern and not filter_by_len:
        filter_by_pattern(pattern, word_set, sorted_good_words)
    elif filter_by_len:
        word_set = get_good_words_by_size(sorted_good_words, word_len)
    else:
        flash('Due to limitations in flash/heroku, results must have a filter applied!')
        return redirect(url_for('index', form=form, name="Sean Montague"))
    if modal_word:
        modal_word['def'] = get_definition(modal_word['word'])

    return render_template('wordlist.html', wordlist=sorted(word_set, key=lambda x:(len(x), x)),
        name="CS4131",
        modal_word=modal_word)


@app.route('/get_def/<word>', methods=['GET', 'POST'])
def get_definition(word):
    app.logger.info("Received request for {}".format(word))
    result = requests.get('https://www.dictionaryapi.com/api/v3/references/collegiate/json/' + \
        word + '?key=6283d672-c28a-4e42-af70-aefc42fe7fc6')
    word_dict = json.loads(result.text)
    if isinstance(word_dict[0], dict):
        defs = word_dict[0]["shortdef"]
    else:
        defs = ["definition was not found!"]
    message = {'defs':defs}
    return jsonify(message)
