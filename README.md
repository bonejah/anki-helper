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
