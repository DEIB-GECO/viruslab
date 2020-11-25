from Bio import SeqIO
from Bio import Align
from io import StringIO
import sys
import numpy as np
import os
from .prepared_parameters import parameters
#from pipeline_nuc_variants__annotations__aa import \
#    filter_nuc_variants, \
#    call_annotation_variant, \
#from data_sources.ncbi_any_virus.ncbi_importer import prepared_parameters
#import json

def filter_nuc_variants(nuc_variants):
    """
    Transforms nucleotide variants of type DELs and SUBs longer than 1 in multiple variants of length 1
    """
    new_nuc_variants = []
    for n in nuc_variants:
        seq_original = n['sequence_original']
        seq_alternative = n['sequence_alternative']
        start_original = int(n['start_original'])
        start_alternative = int(n['start_alternative'])
        variant_length = int(n['variant_length'])
        variant_type = n['variant_type']
        impacts = n['annotations']
        if variant_type == 'DEL' and variant_length > 1:
            for i in range(variant_length):
                new_nuc_variants.append({
                    'sequence_original': seq_original[i],
                    'sequence_alternative': '-',
                    'start_original': start_original + i,
                    'start_alternative': start_alternative + i,
                    'variant_length': 1,
                    'variant_type': variant_type,
                    'annotations': impacts
                })
        elif (variant_type == 'SUB' and variant_length > 1) or seq_alternative.lower()=='n':
            for i in range(variant_length):
                if seq_alternative[i].lower()!= 'n':
                    new_nuc_variants.append({
                        'sequence_original': seq_original[i],
                        'sequence_alternative': seq_alternative[i],
                        'start_original': start_original + i,
                        'start_alternative': start_alternative + i,
                        'variant_length': 1,
                        'variant_type': variant_type,
                        'annotations': impacts
                })
        else:
            new_nuc_variants.append(n)
    return new_nuc_variants


def parse_annotated_variants(annotated_variants):
    result = []
    for variant in annotated_variants:
        try:
            _, start_original, _, _, _, _, others, snpeff_ann = variant.split("\t")
        except ValueError:
            continue

        annotations = []
        for ann in snpeff_ann.split(","):
            try:
                s = ann.split("|")
                annotations.append([s[1], s[2], s[3]])
            except:
                pass

        variant_type, start_alternative, variant_length, sequence_original, sequence_alternative = others.split(',')

        result.append({'sequence_original': sequence_original,
                       'sequence_alternative': sequence_alternative,
                       'start_original': start_original,
                       'start_alternative': start_alternative,
                       'variant_length': variant_length,
                       'variant_type': variant_type,
                       'annotations': annotations
                       })
    return result

class InputException(Exception):
    def __init__(self, message):
        self.msg = message

def add_variant_factory(chr_name):
    def add_variant(pos_ref, pos_seq, length, original, mutated, variant_type, reference, sequence):
        # return [sequence_id, pos_ref, pos_seq, length, original,  mutated, variant_type]
        if variant_type == "INS":
            return "\t".join(
                map(str, [chr_name,
                          max(1, pos_ref),
                          ".",
                          reference[max(1, pos_ref) - 1],
                          sequence[0:length + 1] if (pos_ref == 0) else sequence[pos_seq - 2:pos_seq - 1 + length],
                          ".",
                          ",".join(map(str, [variant_type, pos_seq, length, original, mutated]))]))
        elif variant_type == "DEL":
            return "\t".join(
                map(str, [chr_name,
                          pos_ref,
                          ".",
                          reference[0:length + 1] if (pos_seq == 0) else reference[pos_ref - 2:pos_ref - 1 + length],
                          sequence[max(1, pos_seq) - 1],
                          ".",
                          ",".join(map(str, [variant_type, pos_seq, length, original, mutated]))]))
        else:
            return "\t".join(
                map(str, [chr_name,
                          pos_ref,
                          ".",
                          original,
                          mutated,
                          ".",
                          ",".join(map(str, [variant_type, pos_seq, length, original, mutated]))]))

    return add_variant

def call_nucleotide_variants(sequence_id, reference, sequence, ref_aligned, seq_aligned, ref_positions, seq_positions,
                             chr_name, snpeff_database_name):

    add_variant = add_variant_factory(chr_name)
    variants = []
    ins_open = False
    ins_len = 0
    ins_pos = None
    ins_pos_seq = None
    ins_seq = ""
    for i in range(len(ref_aligned)):
        if ref_aligned[i] == '-':
            if not ins_open:
                ins_pos_seq = seq_positions[i]
            ins_open = True
            ins_len += 1
            ins_pos = ref_positions[i]
            ins_seq += seq_aligned[i]
        else:
            if ins_open:
                v = add_variant(ins_pos, ins_pos_seq, ins_len, "-" * ins_len, ins_seq, "INS", reference,
                                sequence)
                variants.append(v)

                ins_open = False
                ins_len = 0
                ins_pos = None
                ins_pos_seq = None
                ins_seq = ""
    if ins_open:
        v = add_variant(ins_pos, ins_pos_seq, ins_len, "-" * ins_len, ins_seq, "INS", reference, sequence)
        variants.append(v)

    del_open = False
    del_len = 0
    del_pos = None
    del_pos_seq = None
    del_seq = ""
    for i in range(len(ref_aligned)):
        if seq_aligned[i] == '-':
            if not del_open:
                del_pos = ref_positions[i]
            del_pos_seq = seq_positions[i]
            del_open = True
            del_len += 1
            del_seq += ref_aligned[i]
        else:
            if del_open:
                if del_pos != 1:
                    v = add_variant(del_pos, del_pos_seq, del_len, del_seq, "-" * del_len, "DEL", reference,
                                    sequence)
                    variants.append(v)

                del_open = False
                del_len = 0
                del_pos = None
                del_pos_seq = None
                del_seq = ""

    mut_open = False
    mut_len = 0
    mut_pos = None
    mut_pos_seq = None
    mut_seq_original = ""
    mut_seq_mutated = ""
    for i in range(len(ref_aligned)):
        if ref_aligned[i] != '-' and seq_aligned[i] != '-' and ref_aligned[i] != seq_aligned[i]:
            if not mut_open:
                mut_pos = ref_positions[i]
                mut_pos_seq = seq_positions[i]
            mut_open = True
            mut_len += 1
            mut_seq_original += ref_aligned[i]
            mut_seq_mutated += seq_aligned[i]
        else:
            if mut_open:
                v = add_variant(mut_pos, mut_pos_seq, mut_len, mut_seq_original, mut_seq_mutated, "SUB", reference, sequence)
                variants.append(v)

                mut_open = False
                mut_len = 0
                mut_pos = None
                mut_pos_seq = None
                mut_seq_original = ""
                mut_seq_mutated = ""


    if mut_open:
        v = add_variant(mut_pos, mut_pos_seq, mut_len, mut_seq_original, mut_seq_mutated, "SUB", reference, sequence)
        variants.append(v)

    variant_file = "./tmp_snpeff/{}.vcf".format(sequence_id)
    with open(variant_file, "w") as f:
        for m in variants:
            f.write(m + '\n')

    if variants:
        os.system("java -jar ./tmp_snpeff/snpEff/snpEff.jar  {}  {} > ./tmp_snpeff/output_{}.vcf".format(snpeff_database_name,
                                                                                                         variant_file,
                                                                                                         sequence_id))

        try:
            with open("./tmp_snpeff/output_{}.vcf".format(sequence_id)) as f:
                annotated_variants = [line for line in f if not line.startswith("#")]
            os.remove("./tmp_snpeff/output_{}.vcf".format(sequence_id))
        except FileNotFoundError:
            annotated_variants = list()
            pass
    else:
        annotated_variants = list()

    try:
        os.remove("./tmp_snpeff/{}.vcf".format(sequence_id))
    except:
       pass

    return filter_nuc_variants(parse_annotated_variants(annotated_variants))

def sequence_aligner(sequence_id, reference, sequence, chr_name, snpeff_database_name, annotation_file):
    aligner = Align.PairwiseAligner()
    aligner.match_score = 3.0  # the documentation states we can pass the scores in the constructor of PairwiseAligner but it doesn't work
    aligner.mismatch_score = -2.0
    aligner.open_gap_score = -2.5
    aligner.extend_gap_score = -1

    alignments = sorted(list(aligner.align(reference, sequence)),
                        key = lambda x: len(str(x).strip().split('\n')[2].strip("-")))
    alignment = str(alignments[0]).strip().split('\n')
    ref_aligned = alignment[0]
    seq_aligned = alignment[2]

    ref_positions = np.zeros(len(seq_aligned), dtype=int)

    pos = 0
    for i in range(len(ref_aligned)):
        if ref_aligned[i] != '-':
            pos += 1
        ref_positions[i] = pos

    seq_positions = np.zeros(len(seq_aligned), dtype=int)

    pos = 0
    for i in range(len(seq_aligned)):
        if seq_aligned[i] != '-':
            pos += 1
        seq_positions[i] = pos

    annotated_variants = call_nucleotide_variants(sequence_id,
                                                  reference,
                                                  sequence,
                                                  ref_aligned,
                                                  seq_aligned,
                                                  ref_positions,
                                                  seq_positions,
                                                  chr_name,
                                                  snpeff_database_name
                                                  )

    # annotations = filter_ann_and_variants(
    #     call_annotation_variant(annotation_file,
    #                             ref_aligned,
    #                             seq_aligned,
    #                             ref_positions,
    #                             seq_positions
    #                             )
    # )

    # return annotated_variants, annotations

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

    if len(set(metadata.keys()).union(set(sequences.keys()))) > len(set(metadata.keys())):
        raise InputException("Some sequences in the FASTA file do not have a corresponding entry in the metadata.")

    if len(set(metadata.keys()).union(set(sequences.keys()))) > len(set(sequences.keys())):
        raise InputException("Some metadata rows in do not have a corresponding sequence in the FASTA.")

    return sequences, metadata

def pipeline(sequences, metadata, species = 'sars_cov_2'):
    ref_fasta_file_name,annotation_file_name,chr_name,snpeff_db_name = parameters[species]

    #read reference FASTA of the species
    reference_sequence = SeqIO.parse(open(ref_fasta_file_name),
                                     'fasta').__next__().seq

    for sid, sequence in sequences.items():

        sequence_aligner(sid,
                         reference_sequence,
                         sequence,
                         chr_name,
                         snpeff_db_name,
                         annotation_file_name)


