Starting Python environment:
source .venv/bin/activate

Starting app:
python app.py
http://127.0.0.1:5000


Babel:
Sempre que adicionar novos textos no código:

pybabel extract -F babel.cfg -o messages.pot .
pybabel update -i messages.pot -d translations
pybabel compile -d translations


https://www.collinsdictionary.com/dictionary/english/have
https://www.collinsdictionary.com/dictionary/french-english/devoir
https://www.collinsdictionary.com/dictionary/portuguese-english/ter_1