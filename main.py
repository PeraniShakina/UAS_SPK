from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api 
from models import MotorSport as motorsportModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session
from tabulate import tabulate

session = Session(engine)

app = Flask(__name__)
api = Api(app)        

class BaseMethod():

    def __init__(self):
        self.raw_weight = {'cc': 3, 'harga': 4, 'speed': 4, 'berat': 3, 'kapasitas_tangkibensin': 3}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(motorsportModel.id, motorsportModel.cc, motorsportModel.harga, motorsportModel.speed, motorsportModel.berat, motorsportModel.kapasitas_tangkibensin)
        result = session.execute(query).fetchall()
        print(result)
        return [{'id': MotorSport.id, 'cc': MotorSport.cc, 'harga': MotorSport.harga, 'speed': MotorSport.speed, 'berat': MotorSport.berat, 'kapasitas_tangkibensin': MotorSport.kapasitas_tangkibensin} for MotorSport in result]

    @property
    def normalized_data(self):
        cc_values = []
        harga_values = []
        speed_values = []
        berat_values = []
        kapasitas_tangkibensin_values = []

        for data in self.data:
            cc_values.append(data['cc'])
            harga_values.append(data['harga'])
            speed_values.append(data['speed'])
            berat_values.append(data['berat'])
            kapasitas_tangkibensin_values.append(data['kapasitas_tangkibensin'])

        return [
            {'id': data['id'],
             'cc': data['cc'] / max(cc_values),
             'harga': data['harga'] / max(harga_values),
             'speed': data['speed'] / max(speed_values),
             'berat': min(berat_values) / data['berat'] if data['berat'] != 0 else 0,
             'kapasitas_tangkibensin': data['kapasitas_tangkibensin'] / max(kapasitas_tangkibensin_values)
             }
            for data in self.data
        ]

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = [
            {
                'id': row['id'],
                'produk': row['cc'] ** self.raw_weight['cc'] *
                row['harga'] ** self.raw_weight['harga'] *
                row['speed'] ** self.raw_weight['speed'] *
                row['berat'] ** self.raw_weight['berat'] *
                row['kapasitas_tangkibensin'] ** self.raw_weight['kapasitas_tangkibensin']
            }
            for row in normalized_data
        ]
        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)
        sorted_data = [
            {
                'ID': product['id'],
                'score': round(product['produk'], 5)
            }
            for product in sorted_produk
        ]
        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return result, HTTPStatus.OK.value
    
    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'MotorSport': result}, HTTPStatus.OK.value
    

class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = [
            {
                'id':row['id'],
                'Score':round(row['cc'] * weight['harga'] +
                        row['harga'] * weight['harga'] +
                        row['speed'] * weight['speed'] +
                        row['berat'] * weight['berat'] +
                        row['kapasitas_tangkibensin'] * weight['kapasitas_tangkibensin'], 5)
            }
            for row in self.normalized_data
        ]
        sorted_result = sorted(result, key=lambda x: x['Score'], reverse=True)
        return sorted_result


    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return sorted(result, key=lambda x: x['Score'], reverse=True), HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'MotorSport': sorted(result, key=lambda x: x['Score'], reverse=True)}, HTTPStatus.OK.value



class MotorSport(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None
        
        if page > page_count or page < 1:
            abort(404, description=f'Halaman {page} tidak ditemukan.') 
        return {
            'page': page, 
            'page_size': page_size,
            'next': next_page, 
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = select(motorsportModel)
        data = [{'id': MotorSport.id, 'cc': MotorSport.cc, 'harga': MotorSport.harga, 'speed': MotorSport.speed, 'berat': MotorSport.berat, 'kapasitas_tangkibensin': MotorSport.kapasitas_tangkibensin} for MotorSport in session.scalars(query)]
        return self.get_paginated_result('motorsport/', data, request.args), HTTPStatus.OK.value


api.add_resource(MotorSport, '/motorsport')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)
