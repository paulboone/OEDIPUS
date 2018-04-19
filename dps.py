#!/usr/bin/env python3

import click

from oedipus.oedipus import oedipus

@click.command()
@click.argument('config_path',type=click.Path())
def dps(config_path):
    """Start process to manage run.

    Args:
        run_id (str): identification string for run.

    Runs OEDIPUS-method in one process.

    """
    oedipus(config_path)

if __name__ == '__main__':
    dps()
