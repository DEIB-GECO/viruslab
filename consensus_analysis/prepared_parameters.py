from os.path import sep
parameters = {
    'dengue_virus_1': (f'.{sep}annotations{sep}dengue_virus_1.tsv', f'.{sep}annotations{sep}dengue_virus_1.tsv','NC_001477', 'dengue_virus_1'),
    'dengue_virus_2': (f'.{sep}annotations{sep}dengue_virus_2.tsv', f'.{sep}annotations{sep}dengue_virus_1.tsv','NC_001474', 'dengue_virus_2'),
    'dengue_virus_3': ('Dengue Virus 3', f'.{sep}annotations{sep}dengue_virus_3.tsv', f'.{sep}annotations{sep}dengue_virus_1.tsv', 'NC_001475', 'dengue_virus_3'),
    'dengue_virus_4': ('Dengue Virus 4', f'.{sep}annotations{sep}dengue_virus_4.tsv', f'.{sep}annotations{sep}dengue_virus_1.tsv','NC_002640', 'dengue_virus_4'),
    'mers': ('MERS-CoV', f'.{sep}annotations{sep}mers.tsv', f'.{sep}annotations{sep}dengue_virus_1.tsv','NC_019843', 'mers'),
    'betacoronavirus_england_1': ('Betacoronavirus England 1',f'.{sep}annotations{sep}dengue_virus_1.tsv', f'.{sep}annotations{sep}betacoronavirus_england_1.tsv', 'NC_038294', 'betacoronavirus_england_1'),
    'zaire_ebolavirus': (f'.{sep}annotations{sep}zaire_ebolavirus.tsv', f'.{sep}annotations{sep}dengue_virus_1.tsv','NC_002549', 'zaire_ebolavirus'),
    'sudan_ebolavirus': (f'.{sep}annotations{sep}sudan_ebolavirus.tsv',f'.{sep}annotations{sep}dengue_virus_1.tsv', 'NC_006432', 'sudan_ebolavirus'),
    'reston_ebolavirus': (f'.{sep}annotations{sep}reston_ebolavirus.tsv', f'.{sep}annotations{sep}dengue_virus_1.tsv','NC_004161', 'reston_ebolavirus'),
    'bundibugyo_ebolavirus': (f'.{sep}annotations{sep}bundibugyo_ebolavirus.tsv', f'.{sep}annotations{sep}dengue_virus_1.tsv','NC_014373', 'bundibugyo_ebolavirus'),
    'bombali_ebolavirus': (f'.{sep}annotations{sep}bombali_ebolavirus.tsv', f'.{sep}annotations{sep}dengue_virus_1.tsv','NC_039345', 'bombali_ebolavirus'),
    'tai_forest_ebolavirus': (f'.{sep}annotations{sep}tai_forest_ebolavirus.tsv',f'.{sep}annotations{sep}dengue_virus_1.tsv', 'NC_014372', 'tai_forest_ebolavirus'),
    'sars_cov_2': (f'.{sep}consensus_analysis{sep}annotations{sep}sars_cov_2.fa',
                   f'.{sep}annotation_files{sep}new_ncbi_sars_cov_2.tsv',
                   'NC_045512',
                   'new_ncbi_sars_cov_2',
                   f'blast_db{sep}new_ncbi_sars_cov_2.meta',
                   f'.{sep}annotation_files{sep}sars_cov_2_products.json'),
    'sars_cov_1': (f'.{sep}annotations{sep}sars_cov_1.tsv', f'.{sep}annotations{sep}dengue_virus_1.tsv','NC_004718', 'sars_cov_1')
}