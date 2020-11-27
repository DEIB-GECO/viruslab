import os
from typing import Optional, List, Iterable
from os.path import sep, exists
from os import remove, makedirs
from time import time
import gzip
import shutil
from vcf_downloads.refseqs import VIRUS_TAXON_TO_REFSEQ

SNPEFF_DIR = f".{sep}tmp_snpeff{sep}"
TEMP_FILES_DIR = f".{sep}vcf_downloads{sep}temp{sep}"
if not os.path.exists(TEMP_FILES_DIR):
        os.makedirs(TEMP_FILES_DIR, exist_ok=True)
ANNOTATION_FILES_DIR = f".{sep}annotation_files{sep}"
VIRUS_TAXON_TO_SNPEFF_DB_NAME = {
    2010960: "bombali_ebolavirus",
    1335626: "mers",
    694009: "sars_cov_1",
    186541: "tai_forest_ebolavirus",
    565995: "bundibugyo_ebolavirus",
    186539: "reston_ebolavirus",
    186540: "sudan_ebolavirus",
    186538: "zaire_ebolavirus",
    11070: "dengue_virus_4",
    11069: "dengue_virus_3",
    11060: "dengue_virus_2",
    11053: "dengue_virus_1",
    2697049: "new_ncbi_sars_cov_2"
}
VIRUS_TAXON_TO_ANN_FILE_NAME = {
    2010960: "bombali_ebolavirus.tsv",
    1335626: "mers.tsv",
    694009: "new_sars_cov_1.tsv",
    186541: "tai_forest_ebolavirus.tsv",
    565995: "bundibugyo_ebolavirus.tsv",
    186539: "reston_ebolavirus.tsv",
    186540: "sudan_ebolavirus.tsv",
    186538: "zaire_ebolavirus.tsv",
    11070: "dengue_virus_4.tsv",
    11069: "dengue_virus_3.tsv",
    11060: "dengue_virus_2.tsv",
    11053: "dengue_virus_1.tsv",
    2697049: "new_ncbi_sars_cov_2.tsv"
}


def _read_chromosome_name(virus_taxon_id, include_version_number: bool) -> str:
    """
    :param virus_taxon_id:
    :param include_version_number: include/remove the version number in the chromosome name.
    :return: a string with the chromosome name
    """
    annotation_file_path = ANNOTATION_FILES_DIR + VIRUS_TAXON_TO_ANN_FILE_NAME[virus_taxon_id]
    with open(annotation_file_path, mode="r") as annotation_file:
        annotation_file.readline()  # skip first line in case it contains a header
        second_line = annotation_file.readline()
    separator_idx = second_line.index("\t")
    chromosome_full_name = second_line[:separator_idx]
    if not include_version_number:
        try:
            dot_idx = chromosome_full_name.index(".")
            chromosome_full_name = chromosome_full_name[:dot_idx]
        except ValueError:
            pass # chromosome name is without version number -> OK
    return chromosome_full_name


def _VCF_header(accession_ids: List[str], reference_sequence_accession_id: str) -> str:
    """
    Returns the first lines of a VCF file according to the given parameters.
    :param accession_ids: the list of ids that will appear in the VCF.
    :param reference_sequence_accession_id: the accession_id of the reference sequence associated to this virus. This is
    printed in the header lines.
    :return: A string representing the header of a VCF file.
    """
    lines = \
f"""##fileformat=VCFv4.2
##source=VirusLab-VCF-generator
##reference=https://www.ncbi.nlm.nih.gov/nuccore/{reference_sequence_accession_id}
##INFO=<ID=TYPE,Number=1,Type=String,Description="Type of variant:INS|DEL|SUB">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT"""
    for acc_id in accession_ids:
        lines += '\t' + acc_id
    return lines


def _simple_VCF(json_file: dict, subset_of_ids: Optional[List[str]] = None) -> str:
    """
    Creates a long string describing nucleotide variants in VCF format. To complete the VCF generation,
    just write this string into a file with extension ".vcf".
    :param json_file: the source JSON
    :param subset_of_ids: An optional list of ids. If this argument is missing or it is an empty list,
    all the variants of the original JSON file will be included. Otherwise, only the variants of the ids
    included in this array will be part of the VCF.
    :return: A string representing the content of a VCF file.
    """
    virus_taxon_id = json_file["data"]["taxon_id"]
    refseq = VIRUS_TAXON_TO_REFSEQ[virus_taxon_id]
    chromosome_wo_version = _read_chromosome_name(virus_taxon_id, False)
    isolates: dict = json_file["data"]["sequences"]
    consider_subset_of_ids = subset_of_ids is not None and len(subset_of_ids) > 0
    # prepare variants-to-ids data structure

    variants_to_ids = dict()
    for isolate in isolates.values():
        _id = isolate["id"]
        if consider_subset_of_ids and _id not in subset_of_ids:
            continue
        N_variants_super_group: dict = isolate["variants"]["N"]
        N_variants_subgroup: list = N_variants_super_group["variants"]
        schema: list = N_variants_super_group["schema"]

        pos_idx = schema.index("position")
        ref_idx = schema.index("from")
        alt_idx = schema.index("to")
        type_idx = schema.index("type")
        effects_idx = schema.index(["effect", "putative_impact", "gene"])

        for variant in N_variants_subgroup:
            pos = variant[pos_idx]
            ref = variant[ref_idx]
            alt = variant[alt_idx]
            _type = variant[type_idx]
            # effects in json is an array of arrays. Transform each child array into a string
            # effects_as_str = map(lambda triplet: ",".join(triplet), variant[effects_idx])

            variant_key = (pos, ref, alt, _type)
            try:
                variant_attributes: dict = variants_to_ids[variant_key]
                # add this id and effects
                variant_attributes["id"].append(_id)
                # variant_attributes["effects"].update(effects_as_str)
            except KeyError:
                # create key-value
                variants_to_ids[variant_key] = {
                    "id": [_id]
                    # ,
                    # "effects": set(effects_as_str)
                }

    # prepare body of VCF
    body_strings = list()

    all_ids = subset_of_ids if subset_of_ids else [isolate["id"] for isolate in isolates.values()]
    all_ids.sort()
    all_ids_length = len(all_ids)

    # sort variants by POS
    sorted_variant_keys = sorted(variants_to_ids.keys(), key=lambda variant_tuple: variant_tuple[0])

    for key in sorted_variant_keys:
        variant_attributes = variants_to_ids[key]
        # prepare variant description. Describing columns are:  chrom pos id ref alt qual filter info format
        pos, ref, alt, _type = key

        # prepare info
        info = f"TYPE={_type}"
        # format effects as "(modifier,gene,bla),(modifier,gene, bla),..."
        # effect_values: Iterable = map(lambda triplet: f"({triplet})", variant_attributes["effects"])
        # effect_values: str = ",".join(effect_values)
        # if effect_values:
        #     info += f";EFFECTS={effect_values}"

        # convert pos, ref, alt to VCF notation
        ref = ref.replace("-", "")
        alt = alt.replace("-", "")
        # add prefix residue and adapt coordinates
        if _type != 'SUB':
            if pos != 1:
                pos -= 1
                try:
                    prefix_residue = refseq[pos - 1]
                except IndexError as e:
                    print(f"ref len {len(refseq)} - pos {pos}")
                    raise e
                ref = prefix_residue + ref
                alt = prefix_residue + alt
            else:   # handle special case of indel at position 1
                trailing_residue = refseq[len(ref)]
                ref += trailing_residue
                alt += trailing_residue
                # position must not change value

        variant_str = f"{chromosome_wo_version}\t{pos}\t.\t{ref}\t{alt}\t.\t.\t{info}\tGT"

        # prepare genotypes
        this_variant_ids = sorted(variants_to_ids[key]["id"])
        genotype_str = ""
        genotype_idx = 0
        for _id in this_variant_ids:
            id_idx = all_ids.index(_id) # i.e. find the position where to write "1"
            how_many_blanks = id_idx - genotype_idx
            genotype_str += "\t0"*how_many_blanks + "\t1"
            genotype_idx = id_idx + 1 # advance current index to next empty position
        genotype_str += "\t0"*(all_ids_length - genotype_idx)

        body_strings.append(variant_str + genotype_str)

    # concat header and body
    content = _VCF_header(all_ids, _read_chromosome_name(virus_taxon_id, True))
    content += "\n"
    content += "\n".join(body_strings)
    return content


def _add_aa_variants(input_vcf_path, output_vcf_path, virus_taxon_id) -> None:
    """
    Annotates the VCF file given in input with effects and associated amino acid variants
    :param input_vcf_path: path of the input vcf file
    :param output_vcf_path: path of the annotated vcf to be created
    :param virus_taxon_id:
    :return: None
    """
    snpeff_db_name = VIRUS_TAXON_TO_SNPEFF_DB_NAME[virus_taxon_id]
    os.system(f"java -jar {SNPEFF_DIR}snpEff{sep}snpEff.jar {snpeff_db_name} {input_vcf_path} > .{sep}{output_vcf_path}")


def _compress(input_file_path: str, output_file_path: str) -> None:
    with open(input_file_path, mode="rb") as input_file:
        with gzip.open(output_file_path, mode="wb") as output_file:
            shutil.copyfileobj(input_file, output_file)


def save_compressed_vcf_from_json(json_file: dict, output_file_path:str, subset_of_ids: Optional[List[str]] = None) -> str:
    """
    Builds a GZ compressed VCF file representing the nucleotide variants in the given json file.
    Variants are annotated with SnpEff.
    :param json_file: a dictionary representing the json file in python
    :param output_file_path: the path of the .vcf.gz file to create
    :param subset_of_ids: an optional list of ids of the sequences. If not null or empty, the VCF file will
    contain only the variants associated to the specified sequence ids.
    :return: the path (relative to the project root directory) of the GZ compressed VCF file.
    """
    vcf_as_string = _simple_VCF(json_file, subset_of_ids)
    # WRITE VCF STRING TO FILE
    # get a unique filename   (use str(datetime.now().strftime("%Y-%M-%d--%H-%M-%S-%f")) for a readable timestamp instead)
    timestamp = str(time())  # seconds (+ possibly fraction of seconds since epoch)
    vcf_file_path = f"{TEMP_FILES_DIR}{timestamp}.vcf"
    with open(file=vcf_file_path, mode="w") as temp_file:
        temp_file.write(vcf_as_string)
    # ANNOTATE WITH SNPEFF
    annotated_vcf_file_path = f"{TEMP_FILES_DIR}{timestamp}_ann.vcf"
    virus_taxon_id = json_file["data"]["taxon_id"]
    _add_aa_variants(vcf_file_path, annotated_vcf_file_path, virus_taxon_id)
    # COMPRESS
    _compress(annotated_vcf_file_path, output_file_path)
    # CLEANUP
    remove(vcf_file_path)
    remove(annotated_vcf_file_path)
    return output_file_path


# taxon id 2697049#