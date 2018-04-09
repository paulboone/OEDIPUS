import os

import yaml
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Boolean, PrimaryKeyConstraint

from oedipus import config
from oedipus.db import Base, session

class MutationStrength(Base):
    """Declarative class mapping to table of mutation_strengths for each bin.
    
    Attributes:
        run_id (str): identification string for run.
        generation (int): iteration in overall bin-mutate-simulate routine.
        alpha_bin (int):
        beta_bin (int):
    """
    __tablename__ = 'mutation_strengths'
    # COLUMN                                                 UNITS
    run_id = Column(String(50))                            # dimm.
    generation = Column(Integer)                           # generation
    alpha_bin = Column(Integer)
    beta_bin = Column(Integer)
    strength = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint('run_id', 'generation', 'alpha_bin', 'beta_bin'),
    )

    def __init__(self, run_id=None, generation=None, alpha_bin=None,
                 beta_bin=None, strength=None):
        self.run_id = run_id
        self.generation = generation
        self.alpha_bin = alpha_bin
        self.beta_bin = beta_bin
        self.strength = strength

    @classmethod
    def get_prior(cls, run_id, generation, alpha_bin, beta_bin):
        """
        Looks for the most recent mutation_strength row. If a row doesn't exist
        for this bin, the default value is used from the configuration file.

        Args:
            cls (classmethod): here MutationStrength.__init__ .
            run_id (str): identification string for run.

        Returns:
            ms (float): either the mutation strength specified in the mutation
                stength datatable, or the default mutation strength if there is
                no row in the datatable corresponding to the bin.

        """

        ms = session.query(MutationStrength) \
                .filter(
                    MutationStrength.run_id == run_id,
                    MutationStrength.alpha_bin == alpha_bin,
                    MutationStrength.beta_bin == beta_bin,
                    MutationStrength.generation <= generation) \
                .order_by(MutationStrength.generation.desc()) \
                .first()

        if ms:
            return ms
        else:
            return MutationStrength(run_id, generation, alpha_bin, beta_bin, config['initial_mutation_strength'])
