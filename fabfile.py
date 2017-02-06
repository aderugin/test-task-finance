# -*- coding: utf-8 -*-
from datetime import datetime
import os

from fabric.api import task, run, local, env, cd, get, prefix
from fabric.contrib.files import append


BACKUPS_ROOT = 'backups/'

MARKUP_DIRECTORY = ''

LOCAL_SSH_KEY = None

with open(os.path.expanduser('~/.ssh/id_rsa.pub'), 'r') as f:
    LOCAL_SSH_KEY = f.read()

ENVIRONMENT = {
    'staging': '',
    'production': {
        # Пользователь на сервере
        'user': 'user',
        # Хосты на которых расположен проект.
        'host': ['127.0.0.1'],  # django@127.0.0.1
        # Ветка
        'branch': 'master',
        # Путь до папки с media
        'media_root': '',
        # Папка с проектом на сервере
        'root_dir': '',
        # Команда активации окружения
        'venv': 'source <path>/bin/activate',
        # Пользователь базы данных
        'db_user': 'root',
        # Пароль базы данных
        'db_password': '',
        # Имя базы данных
        'db_name': '',
        # Название процесс supervisor
        'supervisor': None,
        # Файл с зависимостями
        'requirements': 'requirements/production.txt'
    },
}


def active_env(name):
    """
    Подготовка окружения
    """
    local_env = ENVIRONMENT.get(name, None)
    if not local_env:
        raise RuntimeError("Не найдено окружение")

    env.user = local_env['user']
    env.hosts = local_env['host']
    env.root = local_env['root_dir']
    env.media_root = local_env['media_root']
    env.branch = local_env['branch']
    env.activate = local_env['venv']
    env.db_user = local_env['db_user']
    env.db_password = local_env['db_password']
    env.db_name = local_env['db_name']
    env.supervisor = local_env['supervisor']
    env.requirements = local_env['requirements']


@task
def staging():
    """
    Подготовка окружения тестового сервера
    """
    active_env('staging')


@task
def production():
    """
    Подготовка окружения рабочего сервера
    """
    active_env('production')


@task
def deploy(branch=None):
    branch = branch or env.branch

    # Пушим все локальные изменения
    local('git push origin %s' % branch)

    # Заливаем изменения на сервер
    with cd(env.root):
        if branch != env.branch:
            run('git fetch origin %s' % branch)
        run('git pull origin %s' % branch)

    # Дамп базы данных перед миграциями
    backup_database()

    # Выполняем команды django
    with cd(env.root):
        with prefix(env.activate):
            run('python manage.py collectstatic --noinput')
            run('python manage.py migrate')

    # Перезагружаем процессы
    run('supervisorctl restart ' + env.supervisor)


@task
def install():
    """
    Установка зависимостей
        Ставит завизимости соответсвующи окружению
    """
    with cd(env.root):
        with prefix(env.activate):
            run('pip install -r %s' % env.requirements)


def backup_database():
    """
    Бэкап базы данных
        return: путь до сделанного бэкапа
    """
    path = '~/%s/db' % BACKUPS_ROOT
    name = '{0}_{1}.sql'.format(env.db_name, datetime.strftime(datetime.now(), '%d.%m.%y_%M:%S'))
    run('mkdir -p %s' % path)
    run('mysqldump -u %s -p%s %s > ~/%s%s' % (env.db_user, env.db_password, env.db_name, path, name))
    return '%s/%s' (path, name)


@task
def push_ssh_key():
    """
    Загрузка ssh ключа
    """
    with cd('~/.ssh/'):
        append('authorized_keys', LOCAL_SSH_KEY)


@task
def dump_database():
    """
    Создание дампа базы данных и его загрузка
    """
    get(backup_database(), 'db/')


@task
def dump_media():
    """
    Создание дампа media и его загрузка
    """
    pass


# ==============================================================================
# Docker
# ==============================================================================

@task
def build():
    local('docker-compose build')


@task
def start(port='8000'):
    with prefix('export APP_PORT=%s' % port):
        local('docker-compose up -d')


@task
def stop():
    local('docker-compose down')


@task
def status():
    local('docker-compose ps')


@task
def migrate(app='', fake=False):
    local('docker-compose exec webapp python manage.py migrate %s %s' % (
        app, '--fake-initial' if fake else ''
    ))


@task
def makemigrations(app=''):
    local('docker-compose exec webapp python manage.py makemigrations %s' % app)


@task
def runserver():
    local('docker-compose exec webapp python manage.py runserver 0.0.0.0:8000')


@task
def shell():
    local('docker-compose exec webapp python manage.py shell')


@task
def manage(command):
    local('docker-compose exec webapp python manage.py %s' % command)


@task
def sqlshell():
    local('docker-compose exec webapp python manage.py shell_plus --print-sql')


@task
def run_tests(app=''):
    local('docker-compose exec webapp python manage.py test %s --keepdb' % app)
