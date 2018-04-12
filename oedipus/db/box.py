import sys
import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.sql import text

#from htsohm import config
from oedipus.db import Base, session, engine

class Box(Base):
    """Declarative class mapping to table storing material/simulation data.

    Attributes:
        id (int): database table primary_key.
        run_id (str): identification string for run.
        uuid (str): unique identification string for material.
        parent_id (int): uuid of parent mutated to create material.
        generation (int): iteration in overall bin-mutate-simulate routine.
        generation_index (int): order material was created in generation (used
            to determine when all materials appear in database for a particular
            generation).
        
        x (float):
        y (float):
        z (float):

        alpha (float):
        beta (float):

        alpha_bin (int):
        beta_bin (int):
    """
    __tablename__ = 'boxes'
    # COLUMN                                                 UNITS
    id = Column(Integer, primary_key=True)                 # dimm.
    run_id = Column(String(50))                            # dimm.
    uuid = Column(String(40))
    parent_id = Column(Integer)                            # dimm.
    generation = Column(Integer)                           # generation#

    # structural data
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)

    # calculated properties
    alpha = Column(Float)
    beta = Column(Float)

    # bins
    alpha_bin = Column(Integer)
    beta_bin = Column(Integer)

    def __init__(self, run_id=None, ):
        """Init material-row.

        Args:
            self (class): row in material table.
            run_id : identification string for run (default = None).

        Initializes row in materials datatable.

        """
        self.uuid = str(uuid.uuid4())
        self.run_id = run_id

    @property
    def bin(self):
        """Determine material's structure-property bin.

        Args:
            self (class): row in material table.

        Returns:
            The bin corresponding to a material's gas loading, void
            fraction, and surface area data and their postion in this three-
            dimension parameter-space.

        """
        return [self.alpha_bin, self.beta_bin]

    def calculate_generation_index(self):
        """Determine material's generation-index.

        Args:
            self (class): row in material table.

        Returns:
            The generation-index is used to count the number of materials
            present in the database (that is to have all definition-files in
            the RASPA library and simulation data in the materials datatable).
            This attribute is used to determine when to stop adding new
            materials to one generation and start another.

        """
        return session.query(Box).filter(
                Box.run_id==self.run_id,
                Box.generation==self.generation,
                Box.id < self.id,
            ).count()

    def calculate_percent_children_in_bin(self):
        """Determine number of children in the same bin as their parent.

        Args:
            self (class): row in material table.

        Returns:
            Fraction of children in the same bin as parent (self).
        """
        sql = text("""
            select
                m.alpha_bin,
                m.beta_bin,
                (
                    m.alpha_bin = p.alpha_bin and
                    m.beta_bin = p.beta_bin
                ) as in_bin
            from boxes m
            join boxes p on (m.parent_id = p.id)
            where m.generation = :gen
                and m.run_id = :run_id
                and p.alpha_bin = :a_bin
                and p.beta_bin = :b_bin
        """)

        rows = engine.connect().execute(
                sql,
                gen=self.generation,
                run_id=self.run_id,
                a_bin=self.alpha_bin,
                b_bin=self.beta_bin
        ).fetchall()

        return len([ r for r in rows if r.in_bin ]) / len(rows)
