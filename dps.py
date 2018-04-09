#!/usr/bin/env python3
from datetime import datetime
import os

import click
import yaml

import oedipus
from oedipus.files import load_config_file
from oedipus.oedipus import worker_run_loop, calc_bin

@click.group()
def dps():
    pass

@dps.command()
@click.argument('config_path',type=click.Path())
def start(config_path):
    """Create a new run.
    
    Args:
        config_path (str): path to config-file (ex: settings/oedipus.sample.yaml)

    Prints run_id, creates run-folder with config-file.

    """
    config = load_config_file(config_path)
    oedipus_dir = os.path.dirname(os.path.dirname(oedipus.__file__))
    run_id = datetime.now().isoformat()
    config['run_id'] = run_id
    config['oedipus_dir'] = oedipus_dir
    
    run_dir = os.path.join(oedipus_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)
    file_name = os.path.join(run_dir, 'config.yaml')
    with open(file_name, 'w') as config_file:
        yaml.dump(config, config_file, default_flow_style=False)
    print('Run created with id: %s' % run_id)

@dps.command()
@click.argument('run_id')
def launch_worker(run_id):
    """Start process to manage run.

    Args:
        run_id (str): identification string for run.

    Runs OEDIPUS-method in one process.

    """
    oedipus._init(run_id)
    worker_run_loop(run_id)

if __name__ == '__main__':
    dps()
