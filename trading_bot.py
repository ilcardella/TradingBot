#!/usr/bin/python3 -u

import os
from shutil import which
import subprocess
import signal
import argparse
import shutil
import json

# Define global variables
SCRIPT_DIR=os.path.dirname(os.path.realpath(__file__))
HOME_DIR=os.path.expanduser('~')
TRADINGBOT_DIR='{}/.TradingBot'.format(HOME_DIR)
LOG_DIR='{}/log'.format(TRADINGBOT_DIR)
DATA_DIR='{}/data'.format(TRADINGBOT_DIR)
CONFIG_DIR='{}/config'.format(TRADINGBOT_DIR)
INSTALL_DIR='/opt/TradingBot'

SCRIPT_FILE=os.path.realpath(__file__)
DOCKERFILE='{}/Dockerfile'.format(SCRIPT_DIR)
PID_FILE='{}/pid.txt'.format(LOG_DIR)
LOG_FILE='{}/log.txt'.format(LOG_DIR)
CONFIG_FILE='{}/config.json'.format(CONFIG_DIR)
TRADINGBOT_BIN='{}/trading_bot.py'.format(INSTALL_DIR)
PYTHON_BIN=which('python3')
MAIN_BIN='{}/src/TradingBot.py'.format(INSTALL_DIR)

DOCKER_IMAGE_NAME = 'trading_bot'
DOCKER_CONTAINER_NAME='dkr_trading_bot'

# Functions
def start(args_list=[]):
    print('Starting TradingBot...')
    _run_command('{} {} {}'.format(PYTHON_BIN, MAIN_BIN, " ".join(args_list)))

def start_detached():
    print('Starting TradingBot in detached mode...')
    command = 'nohup {} {}'.format(PYTHON_BIN, MAIN_BIN)
    process = subprocess.Popen(command.split(),
                stdout=open('/dev/null', 'w'),
                stderr=open(LOG_FILE, 'a'),
                preexec_fn=os.setpgrp)
    # Write process pid in PID_FILE
    with open(PID_FILE, 'w') as pid_file:
        pid_file.write(str(process.pid))
        pid_file.close()
    print('TradingBot started in detached mode')

def stop():
    print('Stopping TradingBot...')
    # Check if PIP_FILE exists
    if not os.path.exists(PID_FILE):
        print('pid file not found: {}'.format(PID_FILE))
        return
    # Kill process from pid
    with open(PID_FILE, 'r') as pid_file:
        pid = pid_file.readline()
        os.kill(int(pid), signal.SIGKILL)
        pid_file.close()
    # Delete PID_FILE
    os.remove(PID_FILE)

    # Delete LOG_FILE too if exists
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    print('TradingBot stopped')

def close_positions():
    print('Starting TradingBot to close open positions')
    # Start TradingBot passing -c argument
    start(['-c'])
    print('Completed')

def install_dependencies():
    print('Installing dependencies...')
    _run_command('apt-get update')
    _find_package('python3', 'python3')
    _find_package('python3-pip', 'pip3')
    _run_command('{} install pipenv'.format(which('pip3')))
    _run_command('pipenv install --dev')

def test():
    print('Starting TradingBot automatic test suite...')
    install_dependencies()
    _run_command('pytest')
    print('Testing documentation...')
    docs(True)

def start_docker():
    import docker
    print('Starting TradingBot in a Docker container...')
    client = docker.from_env()
    image = DOCKER_IMAGE_NAME
    try:
        client.images.get(DOCKER_IMAGE_NAME)
    except docker.errors.NotFound as err:
        print('Docker image {} not found!'.format(DOCKER_IMAGE_NAME))
        build_docker_image()
    command = TRADINGBOT_BIN
    volumes = {
        INSTALL_DIR: {'bind': INSTALL_DIR, 'mode': 'ro'},
        TRADINGBOT_DIR: {'bind': '/root/.TradingBot', 'mode': 'rw'}
    }
    container = client.containers.run(image, command, name=DOCKER_CONTAINER_NAME, detach=True, auto_remove=True, init=True, volumes=volumes)

def stop_docker():
    import docker
    print('Stopping TradingBot Docker container...')
    client = docker.from_env()
    try:
        container = client.containers.get(DOCKER_CONTAINER_NAME)
        container.kill()
    except docker.errors.NotFound as err:
        print('Docker container {} not found!'.format(DOCKER_CONTAINER_NAME))
    except docker.errors.APIError as err:
        print('Unable to kill {}: {}'.format(DOCKER_CONTAINER_NAME, err))

def test_docker():
    import docker
    print('Starting TradingBot automatic test suite in docker containers...')
    client = docker.from_env()
    images = ['python:3.4', 'python:3.5', 'python:3.6', 'python:3']
    for img in images:
        print('Testing TradingBot for {}'.format(img))
        volumes = {
            SCRIPT_DIR: {'bind': '/test', 'mode': 'ro'}
        }
        command = 'python -u trading_bot.py --test'
        container = client.containers.run(img, command, remove=True, auto_remove=True,
                                init=True, volumes=volumes, working_dir='/test',
                                #stdout=True, stderr=True, stream=True)
                                detach=True)
        for log in container.logs(stdout=True, stderr=True, stream=True):
            print('>>> {}'.format(log))
        print('Test with {} complete'.format(img))

def docs(dummy_build=False):
    print('Building documentation (dummy={})...'.format(dummy_build))
    builder = 'dummy' if dummy_build else 'html'
    _find_package('python3-sphinx', 'sphinx-build')
    _run_command('sphinx-build -nWT -b {} doc doc/_build/html'.format(builder))

def install():
    print('Installing TradingBot...')
    install_dependencies()
    # If installation dir exists, then clean everything
    if os.path.exists(INSTALL_DIR):
        shutil.rmtree(INSTALL_DIR)
    # Copy all sources
    shutil.copytree(os.path.join(SCRIPT_DIR, 'src'),
                    os.path.join(INSTALL_DIR, 'src'),
                    ignore=shutil.ignore_patterns('*.pc'))
    # Copy other files
    shutil.copy(SCRIPT_FILE, INSTALL_DIR)
    shutil.copy(DOCKERFILE, INSTALL_DIR)
    # Create TradingBot user folder
    os.makedirs(TRADINGBOT_DIR, exist_ok=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    # Backup existing configuration and copy new default configuration
    if os.path.exists(CONFIG_FILE):
        os.rename(CONFIG_FILE, os.path.join(CONFIG_DIR, 'config_autobackup.json'))
    shutil.copy(os.path.join(SCRIPT_DIR, 'config', 'config.json'), CONFIG_DIR)

    print('Installation complete')
    print('IMPORTANT: change ownership of the following folder: {}'.format(TRADINGBOT_DIR))
    print('Use the following command: sudo chown -R $USER: {}'.format(TRADINGBOT_DIR))

def build_docker_image():
    import docker
    print('Building TradingBot Docker image...')
    client = docker.from_env()
    args = {
        'BASELINE': 'python:3'
    }
    try:
        client.images.build(path=SCRIPT_DIR, buildargs=args, tag=DOCKER_IMAGE_NAME, nocache=True, rm=True)
    except docker.errors.BuildError as e:
        print("Something went wrong with image build!")
        for line in e.build_log:
            if 'stream' in line:
                print(line['stream'].strip())
        return
    print('Image built successfully')

###### Private functions

def _check_installed(required_installed=True):
    """
    Check if TradingBot has been installed and exit if not
    """
    is_installed = bool(SCRIPT_DIR == INSTALL_DIR)
    if not is_installed and required_installed:
        print('Please install TradingBot with: ./trading_bot.py -i')
        exit(1)
    elif is_installed and not required_installed:
        print('Command disabled from installation directory. Run it from workspace')
        exit(1)

def _check_root_user():
    """
    Check if the current user is root and exit if not
    """
    if not os.geteuid()==0:
        print('This script must be run as root!')
        exit(1)


def _find_package(package, binary):
    """
    Check if binary exists and if not it install the package with apt-get
    """
    bin_path = which(binary)
    if bin_path is None:
        print('{} not found. Installing {}'.format(binary, package))
        command = 'apt-get install -y {}'.format(package)
        _run_command(command)
    else:
        print('Found {}: {}'.format(binary, bin_path))
        _run_command('{} --version'.format(binary))

def _run_command(command, pipe_output=True):
    """
    Run a command as a subprocess. Return the Popen object
    """
    stdout = subprocess.PIPE if pipe_output else subprocess.DEVNULL
    process = subprocess.Popen(command.split(), stdout=stdout, universal_newlines=True)
    if pipe_output:
        for line in iter(process.stdout.readline, ''):
            print(">>> {}".format(line.rstrip()))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-d", "--detached",
                        help="Start TradingBot as a background process", action="store_true")
    group.add_argument("-s", "--stop",
                        help="Stop TradingBot background process", action="store_true")
    group.add_argument("-c", "--close-positions",
                        help="Start TradingBot to close all open positions", action="store_true")
    group.add_argument("-i", "--install",
                        help="Install TradingBot", action="store_true")
    group.add_argument("--test",
                        help="Start TradingBot automatic test suite", action="store_true")
    group.add_argument("--docs",
                        help="Build TradingBot html documentation", action="store_true")
    group.add_argument("--install-dep",
                        help="Install TradingBot dependencies", action="store_true")
    group.add_argument("--build-docker",
                        help="Build TradingBot Docker image", action="store_true")
    group.add_argument("--start-docker",
                        help="Start TradingBot in a detached docker container", action="store_true")
    group.add_argument("--test-docker",
                        help="Start TradingBot automatic test suite in docker containers", action="store_true")
    group.add_argument("--stop-docker",
                        help="Stop TradingBot docker container", action="store_true")
    args = parser.parse_args()

    if args.detached:
        _check_installed()
        start_detached()
    elif args.stop:
        _check_installed()
        stop()
    elif args.close_positions:
        _check_installed()
        close_positions()
    elif args.install:
        _check_installed(False)
        _check_root_user()
        install()
    elif args.test:
        _check_installed(False)
        test()
    elif args.docs:
        _check_installed(False)
        docs()
    elif args.install_dep:
        install_dependencies()
    elif args.build_docker:
        build_docker_image()
    elif args.start_docker:
        _check_installed()
        start_docker()
    elif args.test_docker:
        _check_installed(False)
        test_docker()
    elif args.stop_docker:
        _check_installed()
        stop_docker()
    else:
        _check_installed()
        start()
