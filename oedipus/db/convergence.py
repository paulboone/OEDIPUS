import sys
import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.sql import text

#from htsohm import config
from oedipus.db import Base, session, engine

class Convergence(Base):
    __tablename__ = 'convergence_scores'
    # COLUMN                                                 UNITS
    id = Column(Integer, primary_key=True)                 # dimm.
    run_id = Column(String(50), index=True)                # dimm.
    generation = Column(Integer, index=True)               # generation#

    # structural data
    score = Column(Float)

    def __init__(self, run_id, generation, score):
        """Init material-row.

        Args:

        Initializes row in materials datatable.

        """
        self.run_id = run_id
        self.generation = generation
        self.score = score
