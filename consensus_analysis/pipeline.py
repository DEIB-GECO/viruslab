from Bio import SeqIO
from Bio import Align
from io import StringIO
import sys
import numpy as np
import os
from .prepared_parameters import parameters
#from pipeline_nuc_variants__annotations__aa import \
#    parse_annotated_variants, \
#    filter_nuc_variants, \
#    call_annotation_variant, \
#    filter_ann_and_variants
#from data_sources.ncbi_any_virus.ncbi_importer import prepared_parameters
#import json


class InputException(Exception):
    def __init__(self, message):
        self.msg = message

def parse_inputs(input_fasta, input_metadata):
    fasta_sequences = SeqIO.parse(StringIO(input_fasta), 'fasta')
    sequences = {x.id: x.seq for x in fasta_sequences}

    metadata = {}
    meta_rows = input_metadata.strip().split("\n")

    header = meta_rows[0].strip().split(",")
    for line in meta_rows[1:]:
        s = line.strip().split(",")
        sid = s[0]
        seq_metadata = {a: v for a, v in list(zip(header, s))[1:]}
        metadata[sid] = seq_metadata

    if len(metadata.keys()) < len(sequences.keys()):
        raise InputException("Some sequences in the FASTA file do not have a corresponding entry in the metadata.")

    if len(metadata.keys()) > len(sequences.keys()):
        raise InputException("Some metadata rows in do not have a corresponding sequence in the FASTA.")

    return sequences, metadata

def pipeline(sequences, metadata, species = 'sars_cov_2'):
    ref_fasta_file_name,_,_,_ = parameters[species]

    #read reference FASTA of the species
    reference_sequence = SeqIO.parse(open(ref_fasta_file_name),
                                     'fasta').__next__().seq


