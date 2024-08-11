from flask import jsonify, request

from . import app, db
from .error_handlers import InvalidAPIUsage
from .models import Opinion
from .views import random_opinion


@app.route('/api/opinions/<int:id>/', methods=['GET'])
def get_opinion(id):
    opinion = Opinion.query.get(id)
    if opinion is None:
        raise InvalidAPIUsage('Мнение с указанным id не найдено', 404)
    return jsonify({'opinion': opinion.to_dict()}), 200


@app.route('/api/opinions/<int:id>/', methods=['PATCH'])
def update_opinion(id):
    data = request.get_json()
    if (
        'text' in data and
        Opinion.query.filter_by(text=data['text']).first() is not None
    ):
        raise InvalidAPIUsage('Такое мнение уже есть в базе данных')
    # Если метод get_or_404 не найдёт указанный ID,
    # то он выбросит исключение 404:
    opinion = Opinion.query.get(id)
    if opinion is None:
        raise InvalidAPIUsage('Мнение с указанным id не найдено', 404)
    opinion.title = data.get('title', opinion.title)
    opinion.text = data.get('text', opinion.text)
    opinion.source = data.get('source', opinion.source)
    opinion.added_by = data.get('added_by', opinion.added_by)
    # Все изменения нужно сохранить в базе данных.
    # Объект opinion добавлять в сессию не нужно.
    # Этот объект получен из БД методом get_or_404() и уже хранится в сессии.
    db.session.commit()
    # При изменении объекта вернём сам объект и код 200:
    return jsonify({'opinion': opinion.to_dict()}), 201


@app.route('/api/opinions/<int:id>/', methods=['DELETE'])
def delete_opinion(id):
    opinion = Opinion.query.get(id)
    if opinion is None:
        raise InvalidAPIUsage('Мнение с указанным id не найдено', 404)
    db.session.delete(opinion)
    db.session.commit()
    # При удалении принято возвращать только код ответа 204:
    return '', 204


@app.route('/api/opinions/', methods=['GET'])
def get_opinions():
    opinions = Opinion.query.all()
    opinions_list = [opinion.to_dict() for opinion in opinions]
    return jsonify({'opinions': opinions_list}), 200


@app.route('/api/opinions/', methods=['POST'])
def add_opinion():
    # Получение данных из запроса в виде словаря:
    data = request.get_json(silent=True)
    # Если нужных ключей нет в словаре...
    if data is None or 'title' not in data or 'text' not in data:
        # Выбрасываем собственное исключение.
        # Второй параметр (статус-код) в этом обработчике можно не передавать:
        # нужно вернуть код 400, а он и так возвращается по умолчанию.
        raise InvalidAPIUsage('В запросе отсутствуют обязательные поля')
    # Если в базе данных уже есть объект
    # с таким же значением поля text...
    if Opinion.query.filter_by(text=data['text']).first() is not None:
        # Выбрасываем собственное исключение.
        raise InvalidAPIUsage('Такое мнение уже есть в базе данных')
    # Создание нового пустого экземпляра модели:
    opinion = Opinion()
    # Наполнение экземпляра данными из запроса:
    opinion.from_dict(data)
    # Добавление новой записи в сессию:
    db.session.add(opinion)
    # Сохранение изменений:
    db.session.commit()
    return jsonify({'opinion': opinion.to_dict()}), 201


@app.route('/api/get-random-opinion/', methods=['GET'])
def get_random_opinion():
    opinion = random_opinion()
    if opinion is not None:
        return jsonify({'opinion': opinion.to_dict()}), 200
    raise InvalidAPIUsage('В базе данных нет мнений', 404)
