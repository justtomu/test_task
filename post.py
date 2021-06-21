import psycopg2
from psycopg2 import Error
from icecream import ic


class Postgres:
    def __init__(self):
        self.cursor = None
        self.con = None
        self.connect()

    def connect(self):
        try:
            self.con = psycopg2.connect(user='postgres',
                                        password='1234',
                                        host='127.0.0.1',
                                        port='5432',
                                        database='postgres')

            cursor = self.con.cursor()
            self.cursor = cursor

        except (Exception, Error) as e:
            raise Exception('Ошибка при подключении к базе данных PostgreSQL\n' + str(e))

        return {'success': True}

    def create_table(self, table, *params):
        try:
            command = f'CREATE TABLE IF NOT EXISTS {table}('
            for p in params:
                command += p + ', '
            command = command[:-2] + ');'
            self.cursor.execute(command)
            self.con.commit()
        except (Exception, Error) as e:
            raise Exception(f'Ошибка при создании таблицы {table}\n' + str(e))

        return {'success': True}

    def disconnect(self):
        try:
            self.cursor.close()
            self.con.close()
        except (Exception, Error) as e:
            raise Exception('Ошибка при отключении от бд\n' + str(e))

        return {'success': True}

    def insert(self, table: str, values):
        try:
            com = ''
            for i in values:
                com += '%s, '
            self.cursor.execute(f'INSERT INTO {table} VALUES ({com[:-2]})', values)
            self.con.commit()
        except (Exception, Error) as e:
            raise Exception('Ошибка при вставке\n' + str(e))

        return {'success': True}

    def update(self, table: str, com, values):
        try:
            command = f'UPDATE {table} SET {com}'
            # ic(command)
            self.cursor.execute(command, values)
            self.con.commit()
        except (Exception, Error) as e:
            raise Exception('Ошибка при обновлении\n' + str(e))

        return {'success': True}

    def delete_all(self, table):

        try:
            self.cursor.execute(f'delete from {table}')
            self.con.commit()
        except (Exception, Error) as e:
            raise Exception('Ошибка при удалении delete_all\n' + str(e))

        return {'success': True}

    def delete(self, table: str, com, values):
        try:
            command = f'delete from {table} where {com}'
            self.cursor.execute(command, values)
            self.con.commit()
        except (Exception, Error) as e:
            raise Exception('Ошибка при удалении\n' + str(e))

        return {'success': True}

    def show_table(self, table: str):
        try:
            self.cursor.execute(f'SELECT * FROM {table};')
            return {'data': self.cursor.fetchall()}
        except (Exception, Error) as e:
            raise Exception('Ошибка в методе show_table\n' + str(e))

    def select(self, table, fields, where=None, values=None, one=False):
        try:
            if where is None and values is None:
                com = f'select {fields} from {table}'
                self.cursor.execute(com)
            else:
                com = f'select {fields} from {table} where {where}'
                # ic(com)
                self.cursor.execute(com, values)
            ic(com)
            if one:
                return self.cursor.fetchone()
            else:
                return self.cursor.fetchall()
        except Exception as e:
            raise Exception('Ошибка в методе select\n' + str(e))

    def get_count(self, table):
        try:
            self.cursor.execute(f"select count (*) from {table};")
            return self.cursor.fetchone()
        except Exception as e:
            raise Exception('Ошибка в методе get_count\n' + str(e))
