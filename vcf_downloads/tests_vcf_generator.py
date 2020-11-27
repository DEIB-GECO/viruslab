from vcf_downloads.vcf_generator import *
import json

# # JSON -> VCF STRING
# json_path = f'.{sep}/example_min_4_snpeff.json'
# with open(json_path, mode='r') as json_fp:
#     json_file = json.load(json_fp)
# vcf_as_string = NUC_vcf(json_file)
#
#
# # WRITE VCF STRING TO FILE
# # get a unique filename   (use str(datetime.now().strftime("%Y-%M-%d--%H-%M-%S-%f")) for a readable timestamp instead)
# timestamp = str(time()) # seconds (+ possibly fraction of seconds since epoch)
# temp_file_path = f".{sep}example_min_4_snpeff.vcf"
# with open(file=temp_file_path, mode="w") as temp_file:
#     temp_file.write(vcf_as_string)
#
#
# print("USING HARDCODED VCF FILE PATH")
# input_file_path = "example_min_4_snpeff.vcf"
# output_temp_file_path = "output_"+input_file_path
# virus_taxon_id = json_file["result"]["taxon_id"]
# add_aa_variants(input_file_path, output_temp_file_path, virus_taxon_id)
#
#
# compress(output_temp_file_path, output_temp_file_path+".gz")


# some test files here http://genomic.elet.polimi.it/ftp/virusviz/


# json_path = f'.{sep}vcf_downloads{sep}3_australians.json'
json_path = f'.{sep}example-for-vcf-download.json'
output_path = f"{TEMP_FILES_DIR}{time()}.vcf.gz"
with open(json_path, mode='r') as json_fp:
    json_file = json.load(json_fp)
start = time()
print(save_compressed_vcf_from_json(json_file, output_path))
print(f"elapsed time (s) {time() - start}")